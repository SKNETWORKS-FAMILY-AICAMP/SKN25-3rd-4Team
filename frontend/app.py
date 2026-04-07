from __future__ import annotations

import os
import re

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="BioRAG", page_icon="🧬", layout="wide")

# ── CSS: borderless, surface-based, minimal ──

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif&display=swap');

* { font-family: 'Noto Sans KR', sans-serif; box-sizing: border-box; }

/* 전체 배경 — 따뜻한 오프화이트 */
.main, .stApp { background-color: #FAF9F6 !important; }
header[data-testid="stHeader"] { background: transparent !important; }

/* 사이드바 — 부드러운 면 */
[data-testid="stSidebar"] {
    background: #F3F1EC !important;
    border-right: none !important;
}
[data-testid="stSidebar"] > div { padding-top: 0 !important; }

/* 채팅 입력 — 보더 없는 면 */
.stChatInput textarea {
    border-radius: 16px !important;
    border: none !important;
    background: #F0EDE6 !important;
    font-size: 14px !important;
    padding: 14px 20px !important;
    color: #2C2C2A !important;
}
.stChatInput textarea::placeholder { color: #9C9A92 !important; }
.stChatInput textarea:focus { box-shadow: none !important; }

/* 유저 메시지 버블 */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) [data-testid="stMarkdownContainer"] {
    background: #ECEAE3;
    border-radius: 20px 20px 4px 20px;
    padding: 12px 18px;
    color: #2C2C2A;
}

/* 답변 카드 — 보더 없음, 면으로 구분 */
.res-card {
    background: #FFFFFF;
    border: none;
    border-radius: 20px;
    padding: 28px 28px 24px;
    margin: 4px 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    font-size: 14px;
    line-height: 1.8;
    color: #2C2C2A;
}
.res-card h3 {
    font-family: 'Instrument Serif', serif;
    color: #2C2C2A;
    font-size: 20px;
    font-weight: 400;
    margin: 0 0 16px;
    padding: 0;
    border: none;
    letter-spacing: -0.3px;
}

/* 뱃지 — 보더 없음, 면으로 */
.badge-ok {
    display: inline-flex; align-items: center; gap: 5px;
    background: #E8F5E9; color: #2E7D32;
    font-size: 12px; font-weight: 600;
    padding: 5px 14px; border-radius: 20px; margin: 0 0 14px 0;
}
.badge-weak {
    display: inline-flex; align-items: center; gap: 5px;
    background: #FFF8E1; color: #F57F17;
    font-size: 12px; font-weight: 600;
    padding: 5px 14px; border-radius: 20px; margin: 0 0 14px 0;
}
.badge-none {
    display: inline-flex; align-items: center; gap: 5px;
    background: #FCEAEA; color: #C62828;
    font-size: 12px; font-weight: 600;
    padding: 5px 14px; border-radius: 20px; margin: 0 0 14px 0;
}

/* 출처 pills — 보더 없음, 면으로 */
.pill-wrap { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 16px; }
.pill-src {
    background: #F3F1EC; color: #5F5E5A;
    border: none;
    font-size: 11px; font-weight: 500;
    padding: 5px 12px; border-radius: 20px;
    text-decoration: none;
    transition: background 0.15s;
}
.pill-src:hover { background: #E8E5DD; color: #2C2C2A; }

/* 점수 바 — 얇고 미니멀 */
.score-bar-wrap {
    display: flex; align-items: center; gap: 10px; margin: 12px 0 16px;
}
.score-bar-bg {
    flex: 1; height: 4px; background: #ECEAE3;
    border-radius: 2px; overflow: hidden;
}
.score-bar-fill { height: 100%; border-radius: 2px; }

/* 경고 — 부드러운 면 */
.combo-warning {
    background: #FFF8E1;
    border: none;
    border-radius: 12px; padding: 12px 16px;
    font-size: 13px; color: #8D6E00; margin: 12px 0;
    line-height: 1.6;
}

/* 버튼 — 보더 없음 */
.stButton > button {
    border-radius: 12px !important;
    border: none !important;
    font-weight: 500 !important;
    background: #ECEAE3 !important;
    color: #2C2C2A !important;
    transition: background 0.15s !important;
    padding: 8px 16px !important;
}
.stButton > button:hover {
    background: #E0DDD4 !important;
}

/* Streamlit 기본 요소 숨기기 */
#MainMenu, footer, header { display: none !important; }
div[data-testid="stDecoration"] { display: none !important; }

/* 타이틀 영역 */
.bio-hero {
    text-align: center;
    padding: 48px 0 20px;
}
.bio-hero-title {
    font-family: 'Instrument Serif', serif;
    font-size: 42px;
    font-weight: 400;
    color: #2C2C2A;
    letter-spacing: -1px;
    margin: 0;
}
.bio-hero-sub {
    font-size: 14px;
    color: #9C9A92;
    font-weight: 300;
    margin-top: 6px;
    letter-spacing: 0.5px;
}

/* 사이드바 브랜드 */
.sidebar-brand {
    text-align: center;
    padding: 32px 20px 24px;
}
.sidebar-brand-name {
    font-family: 'Instrument Serif', serif;
    font-size: 22px;
    color: #2C2C2A;
    letter-spacing: -0.5px;
}
.sidebar-brand-sub {
    font-size: 11px;
    color: #9C9A92;
    font-weight: 300;
    margin-top: 2px;
    letter-spacing: 0.3px;
}

/* 서버 상태 커스텀 */
.server-status {
    background: #E8F5E9;
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 12px;
    color: #2E7D32;
    margin: 0 16px 12px;
    text-align: center;
}
.server-status-warn {
    background: #FFF8E1;
    border-radius: 10px;
    padding: 8px 14px;
    font-size: 12px;
    color: #F57F17;
    margin: 0 16px 12px;
    text-align: center;
}

/* 예시 질문 라벨 */
.example-label {
    font-size: 11px;
    color: #9C9A92;
    font-weight: 500;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 0 16px;
    margin: 16px 0 8px;
}
</style>
""", unsafe_allow_html=True)


# ── Backend 호출 ──

def call_backend(question: str) -> dict | None:
    try:
        resp = requests.post(
            f"{BACKEND_URL}/api/ask",
            json={"question": question},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("백엔드 서버에 연결할 수 없습니다.")
        return None
    except Exception as e:
        st.error(f"요청 실패: {e}")
        return None


def check_backend_health() -> dict | None:
    try:
        return requests.get(f"{BACKEND_URL}/api/health", timeout=5).json()
    except Exception:
        return None


# ── 렌더링 헬퍼 ──

def render_score_bar(score: float) -> str:
    pct = int(score * 100)
    if score >= 0.75:
        color = "#4CAF50"
    elif score >= 0.5:
        color = "#FFB300"
    else:
        color = "#EF5350"
    return (
        '<div class="score-bar-wrap">'
        f'<span style="font-size:11px;color:#9C9A92;font-weight:500;min-width:56px">관련도</span>'
        f'<div class="score-bar-bg"><div class="score-bar-fill" style="width:{pct}%;background:{color}"></div></div>'
        f'<span style="font-size:11px;color:#9C9A92;font-weight:500;min-width:32px;text-align:right">{pct}%</span>'
        '</div>'
    )


def render_source_pills(sources: list[dict]) -> str:
    if not sources:
        return ""
    pills = []
    for s in sources[:5]:
        label = (s.get("journal") or s.get("source_type", "출처")).strip()
        year = s.get("year", "").strip()
        display = f"{label} {year}".strip()
        url = s.get("url", "")
        pmid = s.get("pmid", "")
        if url:
            pills.append(f'<a class="pill-src" href="{url}" target="_blank">{display}</a>')
        elif pmid:
            pills.append(
                f'<a class="pill-src" href="https://pubmed.ncbi.nlm.nih.gov/{pmid}/"'
                f' target="_blank">{display}</a>'
            )
        else:
            pills.append(f'<span class="pill-src">{display}</span>')
    return f'<div class="pill-wrap">{"".join(pills)}</div>'


def render_answer_card(result: dict) -> str:
    answer = result.get("answer", "")
    paper_sources = result.get("paper_sources", [])
    has_evidence = result.get("has_paper_evidence", False)
    weak = result.get("weak_evidence", False)
    paper_score = result.get("paper_score", 0.0)

    # 답변 본문
    clean = re.sub(r"<[^>]+>", "", answer)
    clean = re.sub(r'(?<!\n)(※)', r'\n\n\1', clean)
    body_parts = []
    for line in clean.split("\n"):
        s = line.strip()
        if not s:
            continue
        if "⚠️" in s or "의사 또는 약사와 상담" in s:
            body_parts.append(f'<div class="combo-warning">{s}</div>')
        elif "※ 검색된 논문의 관련도가 낮아" in s:
            continue
        else:
            body_parts.append(f"<p style='margin:6px 0'>{s}</p>")
    body_html = "\n".join(body_parts)

    # 뱃지
    if has_evidence and not weak:
        badge = '<div class="badge-ok">논문 근거 확인됨</div>'
    elif has_evidence and weak:
        badge = '<div class="badge-weak">간접 근거</div>'
    else:
        badge = '<div class="badge-none">직접 근거 없음</div>'

    # 점수 바
    score_html = render_score_bar(paper_score) if has_evidence and paper_score > 0 else ""

    # 출처
    source_html = render_source_pills(paper_sources)

    inner = "".join(filter(None, [badge, score_html, body_html, source_html]))
    return f'<div class="res-card"><h3>분석 리포트</h3>{inner}</div>'


# ── Session ──

if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None
if "pending_input" not in st.session_state:
    st.session_state.pending_input = None


# ── Sidebar ──

with st.sidebar:
    st.markdown(
        '<div class="sidebar-brand">'
        '<div class="sidebar-brand-name">BioRAG</div>'
        '<div class="sidebar-brand-sub">논문 기반 건강 팩트체커</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    health = check_backend_health()
    if health and health.get("status") == "ok":
        c = health.get("collections", {})
        st.markdown(
            f'<div class="server-status">연결됨 · 논문 {c.get("papers",0)} · 보조 {c.get("aux",0)}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="server-status-warn">서버 연결 대기 중</div>',
            unsafe_allow_html=True,
        )

    if st.button("새 채팅", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()

    st.markdown('<div class="example-label">예시 질문</div>', unsafe_allow_html=True)
    for ex in [
        "마운자로의 효과와 부작용",
        "콜라겐이 피부에 도움이 돼?",
        "간헐적 단식의 대사 효과",
        "올레샷 효과 있어?",
        "오메가3와 심혈관 건강",
    ]:
        if st.button(ex, key=f"ex_{ex}", use_container_width=True):
            st.session_state.pending_input = ex
            st.session_state.current_chat_id = ex[:15]
            st.rerun()

    if st.session_state.chat_history:
        st.markdown('<div class="example-label">이전 대화</div>', unsafe_allow_html=True)
        for chat_id in list(st.session_state.chat_history.keys()):
            c1, c2 = st.columns([0.85, 0.15])
            if c1.button(chat_id, key=f"load_{chat_id}", use_container_width=True):
                st.session_state.messages = st.session_state.chat_history[chat_id]
                st.session_state.current_chat_id = chat_id
                st.rerun()
            if c2.button("✕", key=f"del_{chat_id}"):
                del st.session_state.chat_history[chat_id]
                if st.session_state.current_chat_id == chat_id:
                    st.session_state.messages = []
                    st.session_state.current_chat_id = None
                st.rerun()


# ── Main ──

if not st.session_state.messages:
    st.markdown(
        '<div class="bio-hero">'
        '<div class="bio-hero-title">BioRAG</div>'
        '<div class="bio-hero-sub">논문 기반 건강 팩트체커</div>'
        '</div>',
        unsafe_allow_html=True,
    )
else:
    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="🧬" if m["role"] == "assistant" else None):
            if m["role"] == "assistant" and m.get("result"):
                st.markdown(render_answer_card(m["result"]), unsafe_allow_html=True)
            else:
                st.markdown(m["content"])

# 예시 버튼 or 직접 입력
pending = st.session_state.pop("pending_input", None)
user_input = st.chat_input("무엇이든 물어보세요") or pending

if user_input:
    if st.session_state.current_chat_id is None:
        st.session_state.current_chat_id = user_input[:15]

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="🧬"):
        with st.spinner("분석 중..."):
            result = call_backend(user_input)

        if result:
            clean_text = re.sub(r"<[^>]+>", "", result.get("answer", ""))
            result["answer"] = clean_text
            st.markdown(render_answer_card(result), unsafe_allow_html=True)
            st.session_state.messages.append({
                "role": "assistant",
                "content": clean_text,
                "result": result,
            })
        else:
            st.warning("서버 연결에 실패했습니다.")
            st.session_state.messages.append({"role": "assistant", "content": "서버 연결 실패"})

        st.session_state.chat_history[st.session_state.current_chat_id] = (
            st.session_state.messages.copy()
        )