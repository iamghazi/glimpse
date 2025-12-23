"""
Search Page
Semantic search across video library
"""
import streamlit as st
from pathlib import Path
import requests
from PIL import Image

st.set_page_config(
    page_title="Search - Video Library",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Search Video Library")

# Initialize session state
if "selected_clips" not in st.session_state:
    st.session_state.selected_clips = []
if "search_results" not in st.session_state:
    st.session_state.search_results = None
if "last_query" not in st.session_state:
    st.session_state.last_query = ""

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
        search_button = st.form_submit_button("Search", type="primary", width="stretch")

if search_button:
    if not query:
        st.error("Please enter a search query")
    else:
        with st.spinner("Searching..."):
            try:
                # Call backend search API
                response = requests.post(
                    "http://localhost:8000/search",
                    json={"query": query, "top_k": top_k},
                    timeout=30
                )
                response.raise_for_status()
                search_data = response.json()

                # Store results in session state
                st.session_state.search_results = search_data.get("results", [])
                st.session_state.last_query = query

            except requests.exceptions.RequestException as e:
                st.error(f"Failed to connect to backend: {e}")
                st.warning("Please ensure the backend server is running at http://localhost:8000")
                st.session_state.search_results = None

# Display results (if any)
if st.session_state.search_results is not None:
    st.divider()
    st.markdown("## Results")

    results = st.session_state.search_results

    if not results:
        st.warning("No results found. Try a different query or upload more videos.")
    else:
        st.success(f"Found {len(results)} result(s) for: **{st.session_state.last_query}**")

        # Display results
        for i, result in enumerate(results):
            # Data is at top level, not in payload
            chunk_id = result.get("chunk_id", "")
            video_id = result.get("video_id", "")
            start_time = result.get("start_time", 0.0)
            end_time = result.get("end_time", 0.0)
            visual_desc = result.get("visual_description", "No visual description")
            audio_transcript = result.get("audio_transcript", "No transcript")
            representative_frame = result.get("representative_frame", "")
            score = result.get("score", 0.0)

            # Get video title from result or backend
            video_title = result.get("title", "")
            if not video_title or video_title.startswith("Video vid_"):
                try:
                    video_response = requests.get(f"http://localhost:8000/videos/{video_id}", timeout=2)
                    video_response.raise_for_status()
                    video_data = video_response.json()
                    video_title = video_data.get("title", "Untitled")
                except:
                    video_title = "Untitled"

            # Format timestamps
            start_min = int(start_time // 60)
            start_sec = int(start_time % 60)
            end_min = int(end_time // 60)
            end_sec = int(end_time % 60)
            time_range = f"{start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}"

            # Display result
            st.markdown("---")
            with st.container():
                col1, col2 = st.columns([1, 3])

                with col1:
                    # Show representative frame
                    if representative_frame and Path(representative_frame).exists():
                        try:
                            image = Image.open(representative_frame)
                            st.image(image, caption="Representative Frame", width="stretch")
                        except:
                            st.info("Frame not available")
                    else:
                        st.info("No preview available")

                with col2:
                    st.markdown(f"### {video_title}")
                    st.markdown(f"**Chunk:** [{time_range}] • **Similarity:** {score:.3f}")

                    with st.expander("📝 Details", expanded=False):
                        st.markdown(f"**Visual Description:**")
                        st.write(visual_desc)

                        st.markdown(f"**Audio Transcript:**")
                        st.write(audio_transcript if audio_transcript else "_No speech detected_")

                    # Selection controls
                    col_a, col_b = st.columns([2, 3])
                    with col_a:
                        # Check if already selected
                        is_selected = chunk_id in st.session_state.selected_clips

                        if st.button(
                            "✓ Selected" if is_selected else "Select for Chat",
                            key=f"select_{chunk_id}",
                            type="secondary" if is_selected else "primary",
                            width="stretch"
                        ):
                            if is_selected:
                                st.session_state.selected_clips.remove(chunk_id)
                            else:
                                st.session_state.selected_clips.append(chunk_id)
                            st.rerun()

st.divider()

# Selected Clips for Chat
st.markdown("## Selected Clips for Chat")

if not st.session_state.selected_clips:
    st.info("No clips selected. Search for videos and select clips to chat with them.")
else:
    st.success(f"**{len(st.session_state.selected_clips)} clip(s) selected**")

    for clip_id in st.session_state.selected_clips:
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"- `{clip_id}`")
        with col2:
            if st.button("Remove", key=f"remove_{clip_id}"):
                st.session_state.selected_clips.remove(clip_id)
                st.rerun()

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
