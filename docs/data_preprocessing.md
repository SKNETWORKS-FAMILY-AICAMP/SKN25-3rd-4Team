# 데이터 전처리 문서

## BioRAG 전처리 파이프라인 정리

---

## Backend — LangGraph 9단계

```
질문 입력
  ↓
1. analyze_query
   - glossary 매칭 (브랜드명/신조어 → 성분명)
   - 쿼리 타입 분류 (general / supplement / combo 등)
   - 확장 키워드 생성

  ↓
2. route
   - 질문 카테고리 분류 (다이어트, 피부, 영양제 등)

  ↓
3. retrieve
   - 한글 질문 → 영어 번역 (LLM)
   - ChromaDB MMR 검색 (paper + aux 병렬)
   - similarity score = 평균 × 1.7, 최대 1.0

  ↓ [신조어이거나 검색 결과 없으면]
4. resolve_neologism → Tavily 웹 조회 → 성분명 추출
5. re_retrieve → 추출된 키워드로 재검색 + 기존 결과 합산

  ↓
6. assess_retrieval (LLM 구조화 출력)
   - needs_web: 논문 부족 or 유사도 < 0.5 or 신조어
   - weak_evidence: 간접 근거만 있을 때

  ↓ [needs_web=True면]
7. web_search → Tavily 웹 검색 (trend / official 모드)

  ↓
8. build_context
   - 논문 문서 → LLM 컨텍스트 문자열로 포맷
   - valid_pmids 수집 (환각 방지)

  ↓
9. generate_answer
   - SYSTEM_PROMPT: 서론/본론/결론 형식 강제
   - 논문 없으면 "근거 없음" 메시지

  ↓
10. postprocess
    - 서론/본론/결론 문단 구조화
    - 안전 문구 (⚠️ 콤보/간접 경고) 삽입
    - "근거 없음" 신호어 감지 → paper_docs/score 초기화
```

---

## Frontend — `app.py` 처리 흐름

```
1. 입력 수신
   - st.chat_input 또는 예시 버튼 (pending_input 경유)

2. is_health_related() 검사
   - 건강·의학 무관하면 st.toast 경고 → 채팅 기록 저장 안 함

3. SSE 스트리밍 (/api/ask/stream)
   - status 이벤트 → 로딩 카드 텍스트 업데이트
   - chunk 이벤트 → streaming_text에 조용히 누적
   - done 이벤트 → result 저장

4. 타이핑 애니메이션
   - 3글자씩 출력, 0.01초 딜레이
   - 완료 후 출처 pills 표시

5. render_answer_card
   - badge: 논문 근거 있음 / 간접 근거 / 직접 근거 없음
   - score bar: has_evidence=True일 때만
   - source pills: has_evidence=True일 때만
   - HTML 연결: "".join(filter(None, [...]))
     → CommonMark 빈 줄 버그 방지
```
