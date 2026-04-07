## 시스템 아키텍처 설명

<p align="center">
  <img src="https://github.com/user-attachments/assets/747be191-f4ad-4b2c-a94b-58232ff093ba" width="800"/>
</p>

## External Services

| Service | 용도 |
|---------|------|
| OpenAI API | LLM 답변 생성 |
| ChromaDB | 논문 벡터 검색 (papers.jsonl / aux_docs.jsonl) |
| Tavily | 신조어 해석 · 웹 검색 fallback |


## API Endpoints

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/api/ask` | 질문 응답 |
| `POST` | `/api/ask/stream` | 스트리밍 응답 |
| `GET` | `/api/health` | 서버 상태 확인 |

## api 명세서
<img width="2290" height="264" alt="Image" src="https://github.com/user-attachments/assets/7f4385b6-9095-4b55-86ae-605664e69ac9" />


## Data Flow

1. 사용자 질문 입력 (Streamlit)
2. FastAPI → LangGraph 파이프라인 실행
3. `analyze_query` 에서 신조어 감지 및 쿼리 확장
4. `route` 에서 카테고리 분류 후 ChromaDB MMR 검색
5. 신조어/결과 부족 시 Tavily로 보완 검색
6. LLM 품질 평가 후 필요 시 웹 검색 추가
7. 컨텍스트 조립 → OpenAI 답변 생성 → 한국어 후처리
8. 최종 응답 반환
