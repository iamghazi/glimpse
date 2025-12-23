"""
Chat with Clips Page
Ask questions about selected video clips with context caching
"""
import streamlit as st

st.set_page_config(
    page_title="Chat - Video Library",
    page_icon="💬",
    layout="wide"
)

st.title("💬 Chat with Video Clips")

# Sidebar: Selected clips
with st.sidebar:
    st.markdown("## Selected Clips")

    if "selected_clips" not in st.session_state:
        st.session_state.selected_clips = []

    if not st.session_state.selected_clips:
        st.info("No clips selected. Go to Search page to select clips.")

        if st.button("Go to Search →"):
            st.switch_page("pages/search.py")
    else:
        st.markdown(f"**{len(st.session_state.selected_clips)} clip(s)**")

        for i, clip_id in enumerate(st.session_state.selected_clips):
            with st.expander(f"Clip {i+1}"):
                st.markdown(f"**ID:** `{clip_id}`")
                st.markdown("**Video:** Example Video")
                st.markdown("**Time:** 00:30 - 01:30")

                if st.button("Remove", key=f"remove_{clip_id}"):
                    st.session_state.selected_clips.remove(clip_id)
                    st.rerun()

        if st.button("Clear All", type="secondary"):
            st.session_state.selected_clips = []
            st.rerun()

    st.divider()

    st.markdown("## Cache Status")
    st.info("Backend not connected")

    st.markdown("""
    **Phase 3.9+**: Context caching will:
    - Cache video frames and transcripts
    - Reuse cache for multiple questions
    - Show cache hit/miss statistics
    - Reduce costs by ~90%
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
    # Chat Messages
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Display chat history
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

            if "sources" in message:
                with st.expander("📎 Sources"):
                    for source in message["sources"]:
                        st.markdown(f"- {source}")

    # Chat input
    if prompt := st.chat_input("Ask a question about the selected clips..."):
        # Add user message
        st.session_state.chat_messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate response (placeholder)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                st.warning("⚠️ Backend not connected yet")

                response = f"""
                **Phase 3.9+**: Chat backend will:
                1. Load frames and transcripts for selected clips
                2. Create context cache with Gemini 2.0 Flash
                3. Send your question: "{prompt}"
                4. Generate answer with timestamp references
                5. Return sources with clickable timestamps

                **Example Response:**
                "In the first clip at [00:45], the chef demonstrates the sautéing technique by heating olive oil in a pan. Later at [01:15], they add garlic and onions. This is a classic French cooking method mentioned in the audio transcript."

                **Cache Benefits:**
                - First question: ~$0.10 (caching input)
                - Follow-up questions: ~$0.01 (cache hit)
                - 90% cost reduction for multi-turn conversations
                """

                st.markdown(response)

                st.session_state.chat_messages.append({
                    "role": "assistant",
                    "content": response,
                    "sources": [
                        "Example Clip 1 [00:45]",
                        "Example Clip 1 [01:15]"
                    ]
                })

st.divider()

# Chat Controls
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Clear Chat History"):
        st.session_state.chat_messages = []
        st.rerun()

with col2:
    if st.button("Clear Cache (Backend)"):
        st.info("Cache clearing will be implemented in Phase 3.9+")

with col3:
    if st.button("Export Chat"):
        st.info("Chat export will be implemented in Phase 3.10")

st.divider()

st.markdown("### 💡 Example Questions")
st.markdown("""
Once backend is connected, you can ask questions like:
- "What cooking techniques are shown in these clips?"
- "Summarize the main points discussed"
- "At what timestamp does the chef add the ingredients?"
- "Compare the approaches shown in clip 1 vs clip 2"
- "What tools or equipment are visible in the scenes?"
""")
