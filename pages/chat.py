"""
Chat with Clips Page
Ask questions about selected video clips with context caching
"""
import streamlit as st
import requests

st.set_page_config(
    page_title="Chat - Video Library",
    page_icon="💬",
    layout="wide"
)

st.title("💬 Chat with Video Clips")

# Initialize session state
if "selected_clips" not in st.session_state:
    st.session_state.selected_clips = []
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# Sidebar: Selected clips
with st.sidebar:
    st.markdown("## Selected Clips")

    if not st.session_state.selected_clips:
        st.info("No clips selected. Go to Search page to select clips.")

        if st.button("Go to Search →"):
            st.switch_page("pages/search.py")
    else:
        st.success(f"**{len(st.session_state.selected_clips)} clip(s)**")

        for i, clip_id in enumerate(st.session_state.selected_clips):
            with st.expander(f"Clip {i+1}", expanded=False):
                st.code(clip_id, language=None)

                if st.button("Remove", key=f"remove_{clip_id}"):
                    st.session_state.selected_clips.remove(clip_id)
                    st.rerun()

        if st.button("Clear All", type="secondary"):
            st.session_state.selected_clips = []
            st.rerun()

    st.divider()

    st.markdown("## 💡 About Context Caching")
    st.markdown("""
    **Benefits:**
    - First question creates cache
    - Follow-up questions reuse cache
    - ~90% cost reduction
    - 1-hour cache TTL

    **How it works:**
    - Frames + transcripts cached
    - Multiple clips supported
    - Gemini analyzes content
    - Answers with timestamps
    """)

# Main Chat Interface
if not st.session_state.selected_clips:
    st.warning("⚠️ No clips selected. Please go to the Search page and select some clips first.")
    st.markdown("### How it works:")
    st.markdown("""
    1. **Search** for videos using natural language queries
    2. **Select** relevant clips from search results
    3. **Chat** with the selected clips here
    4. **Ask questions** about the content in those clips
    5. **Get answers** with timestamp references
    """)
else:
    # Display chat history
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if message["role"] == "assistant" and "sources" in message:
                with st.expander("📎 Sources"):
                    for source in message["sources"]:
                        st.markdown(f"- `{source}`")

                if "cache_info" in message:
                    with st.expander("⚡ Cache Info"):
                        cache_info = message["cache_info"]
                        if cache_info.get("cache_hit"):
                            st.success("✅ Cache hit - reused previous context")
                        elif cache_info.get("cache_used") is False:
                            st.info(f"ℹ️ {cache_info.get('reason', 'No caching')}")
                        else:
                            st.info("📝 Cache created for future questions")

                        st.json(cache_info)

    # Chat input
    if prompt := st.chat_input("Ask a question about the selected clips..."):
        # Add user message
        st.session_state.chat_messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Call backend chat API
                    response = requests.post(
                        "http://localhost:8000/chat",
                        json={
                            "chunk_ids": st.session_state.selected_clips,
                            "question": prompt
                        },
                        timeout=60
                    )
                    response.raise_for_status()
                    chat_data = response.json()

                    answer = chat_data.get("answer", "No response")
                    sources = chat_data.get("sources", [])
                    cache_info = chat_data.get("cache_info", {})

                    st.markdown(answer)

                    # Store assistant message
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "cache_info": cache_info
                    })

                    st.rerun()

                except requests.exceptions.RequestException as e:
                    error_msg = f"Failed to connect to backend: {e}"
                    st.error(error_msg)
                    st.warning("Please ensure the backend server is running at http://localhost:8000")

st.divider()

# Chat Controls
col1, col2 = st.columns(2)

with col1:
    if st.button("Clear Chat History", type="secondary"):
        st.session_state.chat_messages = []
        st.rerun()

with col2:
    if st.button("Back to Search", type="secondary"):
        st.switch_page("pages/search.py")

st.divider()

st.markdown("### 💡 Example Questions")
st.markdown("""
Try asking questions like:
- "What is happening in these clips?"
- "Summarize the main points discussed"
- "What objects or people are visible?"
- "What is being said in the audio?"
- "Compare the content across the clips"
- "At what timestamp does X happen?"
""")
