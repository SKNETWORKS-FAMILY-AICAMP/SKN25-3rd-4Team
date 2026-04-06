"""
Hybrid RAG service — 모든 파이프라인 컴포넌트를 조합하는 메인 서비스.

전체 흐름:
1. glossary 매칭 → 쿼리 확장
2. 카테고리 라우팅
3. 한글 → 영어 번역
4. 논문/aux 병렬 검색 (MMR) + similarity score 계산
5. score < threshold → weak_evidence 플래그 + Tavily fallback
6. 논문 없으면 → 신조어 판별 → glossary → Tavily
7. LLM 답변 생성
8. 한국어 재작성 + 안전 문구 적용
"""
from __future__ import annotations

import logging
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.schemas import (
    AskResponse,
    MatchedTermInfo,
    SourceInfo,
)
from app.settings import get_settings
from pipeline.category_router import needs_web_fallback, route_category
from pipeline.external_search import tavily_resolve_neologism, tavily_search_context
from pipeline.glossary_matcher import (
    detect_query_type,
    expand_query,
    get_components,
    is_combo_query,
    is_neologism,
    is_supplement_query,
    match_terms,
)
from pipeline.korean_rewriter import apply_safety_notes, rewrite_answer
from pipeline.retriever import (
    VectorStoreManager,
    docs_to_source_info,
    format_docs,
)

logger = logging.getLogger(__name__)

# score threshold — 이 값 이하면 "논문 직접근거 약함" 판정
PAPER_SCORE_THRESHOLD = 0.75

SYSTEM_PROMPT = """당신은 논문 기반 건강 정보 어시스턴트입니다. 아래 규칙을 반드시 따르세요.

[논문이 있는 경우 — paper_context에 내용이 있을 때]
- "현재 보유한 논문 데이터에서 직접적인 근거를 찾지 못했습니다" 같은 문구를 절대 쓰지 마세요.
- 핵심 내용을 짧고 명확하게 씁니다. 수치가 있으면 반드시 포함하세요.
- 한 주제/성분당 한 문단으로 묶고, 출처는 같은 줄 끝에 붙입니다.
- 출처 형식: (출처: 저널명, 연도, PMID: 번호)
- 문단과 문단 사이는 반드시 빈 줄(

)로 구분합니다.
- 마지막 줄: "자세한 내용은 아래 논문을 확인하세요."

예시:
티르제파타이드는 비만 환자에서 72주 동안 평균 15~21% 체중 감소 효과를 보였습니다. (출처: NEJM, 2022, PMID: 35658024)

당뇨병 예방 측면에서도 3년간 투여 시 제2형 당뇨 진행 위험을 크게 줄였습니다. (출처: NEJM, 2025, PMID: 39536238)

자세한 내용은 아래 논문을 확인하세요.

[논문이 없는 경우 — paper_context가 "관련 논문 없음"일 때]
반드시 아래 형식을 정확히 따르세요. 절대로 한 문단에 몰아쓰지 마세요.
각 성분 설명은 반드시 별도 문단으로 나누고, 문단 사이에 반드시 빈 줄을 넣으세요.

예시 (올레샷):
올레샷에 대한 직접적인 논문 근거는 없습니다.
올레샷은 올리브오일과 레몬즙을 공복에 마시는 건강법입니다.

올리브오일: 폴리페놀 성분이 항산화·항염 효과를 가지며, 심혈관 질환과 당뇨 위험을 낮춥니다. (출처: Int J Mol Sci, 2018, PMID: 29495598)

레몬즙: 헤스페리딘 등 플라보노이드가 항산화·항균 효과를 가집니다. (출처: Nutrients, 2022, PMID: 35745117)

각 성분의 효과는 입증되어 있으나 조합 자체를 검증한 연구는 없습니다.
자세한 내용은 아래 논문을 확인하세요.

[웹검색 결과를 사용한 경우]
- 웹검색 내용을 인용할 때는 문장 끝에 [웹 검색] 표시를 붙이세요.
- 웹검색 결과는 논문 근거와 명확히 구분해서 쓰세요.

[공통 규칙]
- 마크다운 헤더(###, **) 사용 금지
- 개인 진단·처방·복용량 결정 금지
- 한국어로 답변
- SUPPLEMENT_MODE가 ON이면 먹는 영양제/섭취 성분만 다루고, 주사·시술은 "영양제로는 비권장"으로 분리 표기
- COMBO_MODE가 ON이면 조합 효과를 단정하지 말고 성분별로 나눠 각각의 근거만 제시

[모드]
- SUPPLEMENT_MODE: {supplement_mode}
- COMBO_MODE: {combo_mode}
- QUERY_TYPE: {query_type}
- WEAK_EVIDENCE: {weak_evidence_mode}

[용어 정보]
{term_descriptions}

[논문 컨텍스트]
{paper_context}

[보조 문서 컨텍스트]
{aux_context}

[웹검색 보조 컨텍스트]
{web_context}
"""


class HybridRAGService:
    """Hybrid RAG 서비스. 앱 시작 시 한 번 생성하여 재사용한다."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._vs = VectorStoreManager(self._settings)
        self._llm = ChatOpenAI(
            model=self._settings.llm_model,
            temperature=0,
            openai_api_key=self._settings.openai_api_key,
        )
        self._prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", "질문: {question}"),
        ])
        self._parser = StrOutputParser()

    def get_collection_counts(self) -> dict[str, int]:
        return self._vs.get_collection_counts()

    def _translate_to_english(self, text: str) -> str:
        """한글 질문을 PubMed 검색용 영어로 번역한다."""
        try:
            result = self._llm.invoke(
                "Translate the following Korean health question into English "
                "for searching PubMed academic papers. "
                "Return only the translated text, no explanation.\n\n"
                f"Korean: {text}"
            )
            translated = result.content.strip()
            logger.info("번역 완료 | KO: %s → EN: %s", text[:30], translated[:60])
            return translated
        except Exception as e:
            logger.warning("번역 실패, 원문 사용: %s", e)
            return text

    def ask(self, question: str) -> AskResponse:
        """전체 RAG 파이프라인을 실행하고 AskResponse를 반환한다."""

        # 1. glossary 매칭 — 쿼리 확장
        matched = match_terms(question)
        query_type = detect_query_type(matched)
        expanded = expand_query(question, matched)
        components = get_components(matched)
        is_combo = is_combo_query(question, matched)
        is_supplement = is_supplement_query(question)

        # 2. 카테고리 라우팅
        category = route_category(question, matched)

        # 3. 한글 → 영어 번역
        translated_query = self._translate_to_english(expanded)

        # 4. 논문 + 보조문서 벡터 검색 + score 반환
        try:
            retrieved = self._vs.retrieve(
                query=translated_query,
                category=category,
                is_supplement=is_supplement,
            )
        except Exception as e:
            logger.error("Retrieval failed: %s", e)
            retrieved = {"paper_docs": [], "aux_docs": [], "paper_score": 0.0}

        paper_docs = retrieved["paper_docs"]
        aux_docs = retrieved["aux_docs"]
        paper_score = retrieved.get("paper_score", 0.0)

        paper_context = format_docs(paper_docs)
        aux_context = format_docs(aux_docs)
        has_paper_evidence = bool(paper_docs)

        # 5. score 기반 weak_evidence 판정
        weak_evidence = has_paper_evidence and paper_score < PAPER_SCORE_THRESHOLD
        if weak_evidence:
            logger.info("논문 근거 약함 (score=%.4f < %.2f) → Tavily 보완", paper_score, PAPER_SCORE_THRESHOLD)

        # 6. 논문 없을 때 → 신조어 판별 → glossary → Tavily
        neo_context = ""
        needs_web = needs_web_fallback(question, matched)
        is_neo = False

        if not has_paper_evidence:
            is_neo = is_neologism(question, matched)
            if is_neo:
                if not matched:
                    logger.info("논문 없음 + 신조어 + glossary 미매칭 → Tavily: %s", question)
                    neo_context = tavily_resolve_neologism(question)
                else:
                    logger.info("논문 없음 + 신조어 + glossary 매칭 → Tavily 생략")
            else:
                logger.info("논문 없음 + 일반 질문 → needs_web 플래그로만 처리")

        # 7. 웹검색 fallback
        web_context = ""
        if needs_web:
            web_context = tavily_search_context(question, mode="trend")
        if weak_evidence and not web_context:
            web_context = tavily_search_context(question, mode="official")
        if neo_context:
            web_context = (web_context + "\n\n" + neo_context).strip()

        # 8. 용어 설명 텍스트 생성
        term_descriptions = ""
        if matched:
            lines = [f"- {alias}: {info.get('description', '')}" for alias, info in matched.items()]
            term_descriptions = "\n".join(lines)

        # 9. LLM 답변 생성
        if not has_paper_evidence and not web_context:
            answer = (
                "현재 보유한 논문 데이터에서 관련 근거를 찾지 못했습니다. "
                "데이터를 업데이트하거나 전문의와 상담하세요."
            )
        else:
            chain = self._prompt | self._llm | self._parser
            answer = chain.invoke({
                "question": question,
                "paper_context": paper_context or "관련 논문 없음",
                "aux_context": aux_context or "보조 문서 없음",
                "web_context": web_context or "웹 검색 결과 없음",
                "supplement_mode": "ON" if is_supplement else "OFF",
                "combo_mode": "ON" if is_combo else "OFF",
                "query_type": query_type,
                "weak_evidence_mode": "ON" if weak_evidence else "OFF",
                "term_descriptions": term_descriptions or "없음",
            })

        # 10. 한국어 재작성
        answer = rewrite_answer(
            question,
            answer,
            use_llm_rewrite=is_neo,
        )

                # 10.5 답변 후처리 — 서론/본론/결론 문단 구조화
        import re as _re

        # (출처: ...) 뒤에 바로 다음 문장이 붙어오면 줄바꿈 삽입
        answer = _re.sub(r'(\(출처:[^)]+\))\s+(?=[가-힣A-Za-z(])', r'\1\n', answer)

        # 본론 앞 — 서론과 본론 사이 빈 줄 (첫 번째 출처 앞)
        answer = _re.sub(r'(\.)\s+(\S[^\n]+(\(출처:))', r'.\n\n\2', answer, count=1)

        # 결론 앞 — 마지막 출처 이후 내용 앞에 빈 줄
        answer = _re.sub(r'(\(출처:[^)]+\))\n((?!.*\(출처:)[\s\S]+?)$',
                         lambda m: m.group(1) + '\n\n' + m.group(2).lstrip(),
                         answer, flags=_re.MULTILINE)

        # 3개 이상 연속 줄바꿈은 2개로 정리
        answer = _re.sub(r'\n{3,}', '\n\n', answer)

        # 11. 안전 문구 적용
        is_indirect = is_neo and not matched
        answer = apply_safety_notes(
            answer,
            question,
            is_combo=is_combo,
            is_indirect=is_indirect,
        )

        # 12. 응답 조립
        matched_term_infos = [
            MatchedTermInfo(
                alias=alias,
                description=info.get("description", ""),
                expansions=info.get("expansions", []),
                query_type=info.get("query_type", "general"),
            )
            for alias, info in matched.items()
        ]

        return AskResponse(
            answer=answer,
            category=category,
            query_type=query_type,
            matched_terms=matched_term_infos,
            paper_sources=[SourceInfo(**s) for s in docs_to_source_info(paper_docs)],
            aux_sources=[SourceInfo(**s) for s in docs_to_source_info(aux_docs)],
            has_paper_evidence=has_paper_evidence,
            weak_evidence=weak_evidence,
            paper_score=paper_score,
            needs_web=needs_web,
            expanded_query=translated_query,
        )