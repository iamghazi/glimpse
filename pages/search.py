"""
Search Page
Semantic search across video library
"""
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Search - Video Library",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Search Video Library")

# Search Input
st.markdown("## Search")

with st.form("search_form"):
    query = st.text_input(
        "Enter your search query",
        placeholder="e.g., 'people cooking in a kitchen' or 'sunset over mountains'",
        help="Use natural language to describe what you're looking for"
    )

    col1, col2 = st.columns([3, 1])

    with col1:
        top_k = st.slider(
            "Number of results",
            min_value=1,
            max_value=20,
            value=5,
            help="How many results to return"
        )

    with col2:
        st.markdown("")  # Spacer
        st.markdown("")  # Spacer
        search_button = st.form_submit_button("Search", type="primary", use_container_width=True)

if search_button:
    if not query:
        st.error("Please enter a search query")
    else:
        st.divider()

        # Placeholder for search results
        st.markdown("## Results")

        with st.spinner("Searching..."):
            st.warning("⚠️ Backend not connected yet")
            st.info(f"**Query:** {query}")
            st.info(f"**Top-K:** {top_k}")

        st.markdown("### 📋 What will happen here:")
        st.markdown("""
        **Phase 3.8+**: Search backend will:
        1. Generate embedding for your query using `multimodal-embedding-001`
        2. Search Qdrant vector database for similar chunks
        3. Display results with:
           - Video title and chunk timestamp
           - Similarity score
           - Visual description and audio transcript
           - Representative frame thumbnail
           - Checkbox to select for chat
        """)

        # Mock result display
        st.markdown("---")
        st.markdown("**Example Result Format:**")

        with st.container():
            col1, col2 = st.columns([1, 3])

            with col1:
                st.image("https://via.placeholder.com/300x200?text=Thumbnail", caption="Representative Frame")

            with col2:
                st.markdown("**Video Title** - Chunk [00:30 - 01:30]")
                st.markdown("**Similarity Score:** 0.89")
                st.markdown("**Visual:** A person cooking pasta in a modern kitchen with stainless steel appliances")
                st.markdown("**Audio:** 'First, we add the pasta to the boiling water...'")

                col_a, col_b = st.columns([1, 3])
                with col_a:
                    st.checkbox("Select for chat", key="example_checkbox")
                with col_b:
                    st.button("View Clip", key="example_view")

st.divider()

# Selected Clips for Chat
st.markdown("## Selected Clips for Chat")

if "selected_clips" not in st.session_state:
    st.session_state.selected_clips = []

if not st.session_state.selected_clips:
    st.info("No clips selected. Search for videos and select clips to chat with them.")
else:
    st.markdown(f"**{len(st.session_state.selected_clips)} clip(s) selected**")

    for clip_id in st.session_state.selected_clips:
        st.markdown(f"- {clip_id}")

    if st.button("Go to Chat →", type="primary"):
        st.switch_page("pages/chat.py")

st.divider()

st.markdown("### 💡 Tips")
st.markdown("""
- Use descriptive natural language queries
- Search works across both visual descriptions and audio transcripts
- You can search for objects, actions, locations, or spoken words
- Select multiple clips from different videos to compare and analyze
""")
