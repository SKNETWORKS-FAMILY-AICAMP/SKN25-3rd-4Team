# BioRAG

</br>

## 1. 팀 소개

| 이름 | 담당 업무 |
|---|---|
| 김주희 | 시스템 아키텍처 설계 · LangGraph 파이프라인 설계 · PubMed/보조 문서 크롤링 · 코드 구조 리팩토링 |
| 김찬영 | Hybrid RAG 구현 · Streamlit UI 개발 · 전처리 설계서 작성 · LangChain 파이프라인 구현 · PPT 제작 및 발표 |
| 조민서 | LLM 기반 RAG 파이프라인 설계 · 테스트 케이스 설계 · LangChain 파이프라인 구현 · 문서 작성(README) |
| 최현우 | 크롤링 · MMR Retriever 구현 · Hybrid RAG 구현 · LangChain 파이프라인 구현 · PPT 제작 및 발표 |


</br>
</br>

## 2. 프로젝트 개요 

### BioRAG
> 건강 트렌드 질의응답 챗봇 (LLM 연동 내외부 문서 기반 질의응답 챗봇)

</br>

### 프로젝트 배경 및 목적 
SNS와 커뮤니티에 넘쳐나는 건강 정보는 출처가 불명확하고 과장·왜곡된 경우가 많다. </br>
특히 GLP-1 주사, 영양제, 공복 루틴 등 건강 트렌드 관련 질문에 대해 신뢰할 수 있는 정보를 얻기 어렵다. </br>
</br>
본 프로젝트는 세계 최대 의학 논문 데이터베이스인 **PubMed**를 기반으로,
환각(Hallucination) 방지를 위한 질의응답 RAG 챗봇을 구축하는 것을 목적으로 한다.

</br>

### 주요 기능
- **논문 근거 기반 답변** </br>
   PubMed 343개 논문 초록을 벡터 검색해 출처(논문 제목·연도) 자동 표기. 컨텍스트에 없는 내용은 생성하지 않는 환각 방지 구조 적용
  
- **신조어·슬랭 자동 해석** </br>
  "위고비", "올레샷", "애사비" 등 커뮤니티 용어를 Tavily 실시간 조회로 성분명·학술 키워드로 변환 후 논문 재검색 (Paper-First 원칙)
- **3단계 근거 판정** </br>
   LLM이 논문 내용과 유사도 점수를 함께 평가해 직접 근거 / 간접 근거 / 근거 없음 3단계로 판정, 뱃지로 시각화
- **웹 검색 보완** </br>
   논문 유사도 낮거나 신조어 미등록 용어일 경우 Tavily 웹검색으로 자동 보완. MedlinePlus·Glossary 보조 문서도 병렬 검색
- **실시간 스트리밍** </br>
   SSE 기반 스트리밍으로 답변이 타이핑되듯 실시간 출력. 분석 완료 후 논문 관련도 점수바·출처 pills 표시


</br>

### 기대 효과
- 사용자가 건강 정보의 신뢰도를 논문 출처와 함께 직접 확인 가능
- 신조어·유행어 기반 질문도 학술 근거로 연결
- 환각 방지 구조로 잘못된 의료 정보 전달 최소화

</br>
</br>

## 3. 프로젝트 구조 
```
biorag-health-chatbot/
├── .env                          # 환경변수 설정
├── .env.sample                   # 환경변수 예시
│
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI 앱 진입점 (API 라우터)
│   │   ├── schemas.py            # 요청/응답 Pydantic 스키마
│   │   └── settings.py           # 앱 설정
│   │
│   ├── configs/
│   │   ├── domain_scope.json     # 도메인 범위 설정
│   │   ├── glossary.json         # 의학 용어 사전
│   │   ├── pubmed_topics.json    # PubMed 수집 토픽 목록
│   │   └── trusted_domains.json  # 신뢰 도메인 목록
│   │
│   ├── data/
│   │   ├── chroma/               # ChromaDB 벡터스토어 (자동 생성)
│   │   └── raw/
│   │       ├── papers.jsonl      # 수집된 PubMed 논문 데이터
│   │       └── aux_docs.jsonl    # 수집된 보조 문서 데이터
│   │
│   ├── ingestion/
│   │   ├── crawl_pubmed.py       # PubMed 논문 크롤러
│   │   ├── crawl_aux_docs.py     # 보조 문서 크롤러
│   │   └── build_vectorstores.py # 벡터스토어 빌드 (임베딩 → ChromaDB 저장)
│   │
│   ├── pipeline/
│   │   ├── state.py              # LangGraph 상태 정의
│   │   ├── graph.py              # RAG 파이프라인 그래프 구성
│   │   ├── nodes.py              # 그래프 노드 함수들
│   │   ├── rag_service.py        # RAG 서비스 
│   │   ├── retriever.py          # 벡터스토어 검색기
│   │   ├── category_router.py    # 질문 카테고리 분류 라우터
│   │   ├── korean_rewriter.py    # 한국어 질문 재작성기
│   │   ├── glossary_matcher.py   # 용어 사전 매처
│   │   ├── external_search.py    # 외부 검색 (웹/PubMed API)
│   │   └── draw_graph.py         # 파이프라인 그래프 시각화
│   │
│   └── requirements.txt
│
├── docs/                         # 산출물
│   ├── architecture.md           # 시스템 아키텍처
│   ├── data_preprocessing.md     # 데이터 전처리 문서
│   └── test_report.md            # 테스트 케이스 및 결과 보고서
│
├── frontend/
│   ├── app.py                    # Streamlit 프론트엔드
│   └── requirements.txt
│
└── scripts/
    └── ingest.sh                 # 데이터 수집 및 벡터스토어 빌드 스크립트
```

</br>
</br>

## 4. 시스템 아키텍처
### RAG 파이프라인

<img width="761" height="925" alt="Image" src="https://github.com/user-attachments/assets/8d672bfa-dbc5-4c06-88e0-9781da8f6400" />

</br>
</br>

### 유사도 3단계 
`assess_retrieval` 노드에서 LLM이 논문 내용과 유사도 점수를 함께 평가해 3단계로 판정합니다.

| 단계 | 조건 | 뱃지 |
|---|---|---|
| 직접 근거 | `has_paper_evidence=True`, `weak_evidence=False` | 초록 `✓ 논문 근거 있음` |
| 간접 근거 | `has_paper_evidence=True`, `weak_evidence=True`, `paper_score ≥ 0.25` | 노랑 `△ 간접 근거` |
| 근거 없음 | `has_paper_evidence=False` 또는 `weak_evidence=True`, `paper_score < 0.25` | 빨강 `✗ 직접 근거 없음` |

```
질문 입력
    │
    ▼
has_paper_evidence?
    ├── True ──▶ weak_evidence?
    │               ├── False ──────────────────▶ 초록: "✓ 논문 근거 있음"
    │               └── True ──▶ paper_score?
    │                               ├── ≥ 0.25 ──▶ 노랑: "△ 간접 근거"
    │                               └── < 0.25 ──▶ 빨강: "✗ 직접 근거 없음"
    └── False ──────────────────────────────────▶ 빨강: "✗ 직접 근거 없음"
```

</br>
</br>

## 5. 데이터 수집 및 전처리
### 수집 파이프라인
```
[PubMed Entrez API]          [신뢰 도메인 크롤링]
  카테고리별 토픽 검색           MedlinePlus · Glossary
        │                              │
        ▼                              ▼
  papers.jsonl                   aux_docs.jsonl
  (논문 제목·초록·PMID·연도)      (보조 의학 문서)
        │                              │
        └──────────────┬───────────────┘
                       ▼
             OpenAI Embeddings
             (텍스트 → 벡터 변환)
                       │
                       ▼
                  ChromaDB
             (papers / aux 컬렉션)
```

</br>

### 수집 데이터

| 구분 | 출처 | 건수 | 저장 형식 |
|---|---|---|---|
| 메인 데이터 | PubMed Entrez API | 343개 논문 초록 | `papers.jsonl` |
| 보조 데이터 | MedlinePlus · Glossary | 391개 | `aux_docs.jsonl` |

</br>

### 전처리 과정

- **JSONL 정형화** — 논문 제목·초록·PMID·연도·카테고리를 구조화해 저장
- **카테고리 태깅** — `configs/pubmed_topics.json` 기반으로 수집 시 카테고리 자동 분류
- **MMR 검색 적용** — 검색 시 중복 정보 배제, 다양성 확보
- **supplement 필터** — 영양제 질문 시 주사·시술 관련 문서 자동 제외
  
</br>
</br>

## 6. 빠른 시작

**환경 설정**
```bash
cp .env.example .env
# .env 파일에 OPENAI_API_KEY, NCBI_EMAIL 입력
```


| 변수명 | 필수 | 설명 |
|---|---|---|
| `OPENAI_API_KEY` | ✓ | OpenAI API 키 |
| `NCBI_EMAIL` | ✓ | PubMed Entrez 사용 이메일 |
| `NCBI_API_KEY` | - | NCBI API 키 (선택, 요청 속도 향상) |
| `TAVILY_API_KEY` | - | Tavily 웹검색 키 (없으면 웹 검색 비활성) |

</br>

**의존성 설치**
```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# frontend (별도 터미널)
cd frontend
pip install -r requirements.txt
```

</br>

**데이터 수집 + 벡터스토어 빌드**
```bash
cd backend
bash ../scripts/ingest.sh --reset
```

</br>

**서버 실행**
```bash
# 터미널 1: Backend
cd backend
uvicorn app.main:app --reload

# 터미널 2: Frontend
cd frontend
streamlit run app.py
```

</br>

## 카테고리 
질문이 입력되면 category_router가 자동으로 카테고리를 분류해 해당 논문 컬렉션에서 검색합니다.
| 카테고리 | 예시 질문 |
|----------|-----------|
| diet_glp1 | 마운자로 부작용, 간헐적 단식 효과 |
| skin_beauty_regeneration | 콜라겐 보충제, 레티놀 효과 |
| supplement_trends | 오메가3, 비타민D, 유산균 |
| morning_fasted_routines | 올레샷, 애사비, 방탄커피 |


</br>
</br>

## 7. 기술 스택

| 분류 | 기술 |
|---|---|
| **Backend** | ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white) ![Uvicorn](https://img.shields.io/badge/Uvicorn-499848?style=flat&logo=gunicorn&logoColor=white) |
| **AI / LLM** | ![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat&logo=langchain&logoColor=white) ![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?style=flat&logo=langchain&logoColor=white) ![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white) |
| **Vector DB** | ![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6F00?style=flat&logoColor=white) |
| **Data** | ![PubMed](https://img.shields.io/badge/PubMed-326599?style=flat&logoColor=white) ![Tavily](https://img.shields.io/badge/Tavily-000000?style=flat&logoColor=white) |
| **Frontend** | ![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit&logoColor=white) |
| **Collaboration** | ![Git](https://img.shields.io/badge/Git-F05032?style=flat&logo=git&logoColor=white) ![GitHub](https://img.shields.io/badge/GitHub-181717?style=flat&logo=github&logoColor=white) ![Notion](https://img.shields.io/badge/Notion-000000?style=flat&logo=notion&logoColor=white) |


</br>
</br>

## 8. 향후 개선 과제

- **사용자 친화적 UI/UX 고도화** </br>
  대화형 인터페이스 시각화 기능 개선 및 Redis로 이전 대화 내용 기록 저장

- **Docker 기반 서비스 배포 및 환경 재현** </br>
  로컬 환경에 종속된 현재 시스템을 컨테이너화하여, 어떤 서버에서든 실행·배포 가능한 독립적 인프라 구축

- **Airflow 기반 데이터 수집 자동화 및 확장** </br>
  수동 데이터 스크래핑을 파이프라인으로 완전 자동화하여 카테고리 확장 및 벡터 DB 최신 상태 유지

</br>
</br>

## 9. 회고 

> 김주희 </br>

시스템 아키텍처와 LangGraph 파이프라인을 설계하고, PubMed 및 보조 문서 크롤링부터 코드 구조 리팩토링까지 전 과정을 직접 수행하며 모듈 간 의존성과 유지보수 구조의 중요성을 체감했고, 이를 통해 RAG 시스템 전체 흐름에 대한 이해를 크게 높일 수 있었습니다.

> 김찬영 </br>

백엔드와 프론트엔드 전체 구조를 파악하며 아키텍처 설계와 Git 협업의 중요성을 이 전 프로젝트보다 더 크게 다가왔던 프로젝트였습니다. 특히 오류 수정 과정에서 유지보수의 어려움을 체감하며 초기 코드 설계의 신중함을 배웠습니다. 열정적인 팀원들과 함께해서 좋은 결과물을 만들 수 있었습니다

> 조민서 </br>

이론으로만 접했던 RAG 시스템을 직접 구현하고 검증하는 경험을 할 수 있었습니다. 다양한 질문 유형에 대해 예상과 다른 결과가 나올 때마다 파이프라인 구조를 다시 들여다보며 디버깅하는 과정이 쉽지 않았지만, 팀원들과 함께 문제를 좁혀나가며 시스템 전체 흐름을 깊이 이해하게 된 계기가 되었습니다.

> 최현우 </br>

좋은팀원들과 재밋는 주제로 어떤 기능들을 넣을까 이야기하며 즐겁게 했습니다~^^
