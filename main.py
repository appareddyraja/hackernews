import streamlit as st
import requests
from datetime import datetime
import concurrent.futures

# Hacker News API Endpoints
HACKERNEWS_TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HACKERNEWS_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"
HACKERNEWS_USER_URL = "https://hacker-news.firebaseio.com/v0/user/{}.json"

# Function to fetch single story
def fetch_story(story_id):
    try:
        response = requests.get(HACKERNEWS_ITEM_URL.format(story_id), timeout=5)
        story = response.json()
        return story if story.get('type') == 'story' else None
    except Exception:
        return None

# Function to fetch top stories with concurrent requests
def fetch_top_stories(limit=30):
    try:
        # Fetch top story IDs
        response = requests.get(HACKERNEWS_TOP_STORIES_URL, timeout=10)
        response.raise_for_status()
        story_ids = response.json()[:limit]
        
        # Use concurrent requests to speed up fetching
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            stories = list(filter(None, executor.map(fetch_story, story_ids)))
        
        return stories
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching stories: {e}")
        return []

# Calculate story age
def calculate_story_age(timestamp):
    try:
        story_time = datetime.fromtimestamp(timestamp)
        now = datetime.now()
        diff = now - story_time
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds // 3600 > 0:
            return f"{diff.seconds // 3600} hours ago"
        else:
            return f"{diff.seconds // 60} minutes ago"
    except Exception:
        return "Unknown time"

# Fetch user profile link
def get_user_profile_link(username):
    return f"https://news.ycombinator.com/user?id={username}"

# Streamlit UI Configuration
st.set_page_config(page_title="Hacker News Clone", layout="wide")

# Custom CSS
st.markdown("""
    <style>
        .header { 
            background-color: #ff6600; 
            padding: 10px; 
            font-size: 24px; 
            color: white; 
            font-weight: bold;
        }
        .news-item { 
            font-size: 16px; 
            margin-bottom: 10px;
        }
        .news-meta { 
            font-size: 12px; 
            color: gray;
        }
        a { 
            text-decoration: none; 
            color: black; 
            transition: color 0.3s ease;
        }
        a:hover { 
            color: #ff6600;
        }
        .stButton>button {
            background-color: #ff6600;
            color: white;
            width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state for stories and displayed count
if 'stories' not in st.session_state:
    with st.spinner('Fetching top stories...'):
        st.session_state.stories = fetch_top_stories(50)

if 'displayed_count' not in st.session_state:
    st.session_state.displayed_count = 10

# Header
st.markdown('<div class="header">📰 Hacker News</div>', unsafe_allow_html=True)

# Display stories
for i, story in enumerate(st.session_state.stories[:st.session_state.displayed_count], 1):
    # Story URL handling
    story_url = story.get("url", f"https://news.ycombinator.com/item?id={story.get('id', '')}")
    story_title = story.get("title", "No Title")
    story_score = story.get("score", 0)
    story_comments = story.get("descendants", 0)
    story_by = story.get("by", "Unknown")
    story_time = calculate_story_age(story.get('time', 0))
    
    # Story title with link
    st.markdown(f'<div class="news-item">{i}. <a href="{story_url}" target="_blank">{story_title}</a></div>', unsafe_allow_html=True)
    
    # Metadata with clickable links
    metadata_html = f'''
    <div class="news-meta">
        {story_score} points by 
        <a href="{get_user_profile_link(story_by)}" target="_blank">{story_by}</a> | 
        <a href="https://news.ycombinator.com/item?id={story.get('id', '')}" target="_blank">{story_comments} comments</a> | 
        {story_time}
    </div>
    '''
    st.markdown(metadata_html, unsafe_allow_html=True)
    
    st.write("---")

# Load More button
if st.session_state.displayed_count < len(st.session_state.stories):
    if st.button('Load More Stories'):
        st.session_state.displayed_count += 10

# Show how many stories are left
remaining_stories = len(st.session_state.stories) - st.session_state.displayed_count
st.markdown(f"**{max(0, remaining_stories)} stories remaining**")
