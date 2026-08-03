from __future__ import annotations

from pathlib import Path

import streamlit as st

from studybot.answering import Assistant

APP_TITLE = "StudyBot"
APP_SUBTITLE = "A dark-themed AI assistant for notes, coding, weather, definitions, and live factual lookups."
DEFAULT_KNOWLEDGE_ROOT = Path("assets") / "knowledge"


st.set_page_config(page_title=APP_TITLE, page_icon="🧠", layout="wide")

st.markdown(
    """
    <style>
        :root {
            --bg: #0b0f16;
            --panel: #111827;
            --panel-alt: #161c28;
            --border: rgba(148, 163, 184, 0.18);
            --text: #e5e7eb;
            --muted: #9ca3af;
            --accent: #7c3aed;
            --accent-2: #22c55e;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(124, 58, 237, 0.18), transparent 32%),
                radial-gradient(circle at top right, rgba(34, 197, 94, 0.10), transparent 26%),
                linear-gradient(180deg, #0b0f16 0%, #0f1219 100%);
            color: var(--text);
        }

        .hero {
            padding: 1.4rem 1.5rem;
            border: 1px solid var(--border);
            border-radius: 1.2rem;
            background: linear-gradient(180deg, rgba(17, 24, 39, 0.92), rgba(17, 24, 39, 0.78));
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.24);
            margin-bottom: 1rem;
        }

        .hero h1 {
            margin: 0;
            font-size: 2rem;
            line-height: 1.1;
            color: #f8fafc;
        }

        .hero p {
            margin: 0.6rem 0 0;
            color: var(--muted);
            font-size: 1rem;
        }

        .metric-card {
            border: 1px solid var(--border);
            background: rgba(17, 24, 39, 0.88);
            border-radius: 1rem;
            padding: 0.85rem 1rem;
        }

        .message {
            padding: 0.9rem 1rem;
            border-radius: 1rem;
            border: 1px solid var(--border);
            margin-bottom: 0.6rem;
            background: rgba(17, 24, 39, 0.7);
        }

        .assistant-message {
            background: linear-gradient(180deg, rgba(22, 28, 40, 0.95), rgba(17, 24, 39, 0.82));
        }

        .user-message {
            background: rgba(30, 41, 59, 0.82);
        }

        .small-label {
            color: var(--muted);
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.35rem;
        }

        .source-pill {
            display: inline-block;
            margin: 0.15rem 0.35rem 0.15rem 0;
            padding: 0.18rem 0.55rem;
            border-radius: 999px;
            background: rgba(124, 58, 237, 0.18);
            border: 1px solid rgba(124, 58, 237, 0.38);
            color: #ddd6fe;
            font-size: 0.78rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_assistant() -> Assistant:
    return Assistant(DEFAULT_KNOWLEDGE_ROOT)


def ensure_session_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "assistant" not in st.session_state:
        st.session_state.assistant = get_assistant()


def render_header() -> None:
    st.markdown(
        f"""
        <div class="hero">
            <h1>{APP_TITLE}</h1>
            <p>{APP_SUBTITLE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar() -> dict[str, object]:
    with st.sidebar:
        st.markdown("### Controls")
        knowledge_root = st.text_input("Knowledge folder", value=str(DEFAULT_KNOWLEDGE_ROOT))
        top_k = st.slider("Retrieved passages", min_value=1, max_value=5, value=3)
        st.caption("The assistant uses local notes first, then routes to live APIs when the topic fits.")

        st.markdown("### Suggested prompts")
        prompts = [
            "How does StudyBot answer questions?",
            "How is the weather in Brooklyn today?",
            "What does TypeError mean in Python?",
            "What is polymorphism?",
        ]
        chosen_prompt = None
        for prompt in prompts:
            if st.button(prompt, use_container_width=True):
                chosen_prompt = prompt

        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        return {"knowledge_root": knowledge_root, "top_k": top_k, "prompt": chosen_prompt}


def render_chat_history() -> None:
    for message in st.session_state.messages:
        role = message["role"]
        with st.chat_message(role):
            if role == "assistant":
                st.markdown(f"<div class='message assistant-message'>{message['content']}</div>", unsafe_allow_html=True)
                if message.get("sources"):
                    st.markdown(
                        "".join(f"<span class='source-pill'>{source}</span>" for source in message["sources"]),
                        unsafe_allow_html=True,
                    )
                    st.caption(f"Confidence: {message.get('confidence', 0.0):.2f}")
            else:
                st.markdown(f"<div class='message user-message'>{message['content']}</div>", unsafe_allow_html=True)


def add_message(role: str, content: str, sources: list[str] | None = None, confidence: float | None = None) -> None:
    entry = {"role": role, "content": content}
    if sources is not None:
        entry["sources"] = sources
    if confidence is not None:
        entry["confidence"] = confidence
    st.session_state.messages.append(entry)


def main() -> None:
    ensure_session_state()
    controls = render_sidebar()

    if controls["prompt"]:
        st.session_state.pending_prompt = controls["prompt"]

    render_header()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div class='metric-card'><div class='small-label'>Mode</div><strong>Multi-topic assistant</strong></div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='metric-card'><div class='small-label'>Memory</div><strong>Session follow-up context</strong></div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='metric-card'><div class='small-label'>Theme</div><strong>Dark</strong></div>", unsafe_allow_html=True)

    render_chat_history()

    prompt = st.chat_input("Ask about notes, coding, weather, definitions, or news...")
    if "pending_prompt" in st.session_state:
        prompt = st.session_state.pop("pending_prompt")

    if prompt:
        add_message("user", prompt)
        assistant = st.session_state.assistant
        answer = assistant.answer(prompt, top_k=int(controls["top_k"]))
        add_message("assistant", answer.response, sources=answer.sources, confidence=answer.confidence)
        st.rerun()


if __name__ == "__main__":
    main()
