import streamlit as st
from groq import Groq
import requests as r
import os
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# --- 1. Page Configuration ---
st.set_page_config(page_title="KP Personal Assistant", page_icon="🤖")

# --- 2. State & Data Initialization ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "context" not in st.session_state:
    st.session_state.context = ""

# Prioritize Streamlit Secrets for deployment, fallback to environment variables for local testing
try:
    user_api_key = st.secrets["API_KEY"]
except KeyError:
    st.error("Missing API_KEY in Streamlit Secrets. Please add it to your dashboard or .streamlit/secrets.toml.")
    st.stop()


# --- 3. Helper Functions ---

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception)
)
def safe_groq_call(chat_client, model, chat_messages):
    """Executes a Groq call with automatic retry logic."""
    return chat_client.chat.completions.create(
        model=model,
        messages=chat_messages,
        max_tokens=1024,
        temperature=0.1,
    )

def summarize_text(client, text, target_words=250):
    """Summarizes raw content to stay within token limits."""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant", # Using a faster model for background tasks
            messages=[
                {"role": "system", "content": f"Summarize the following technical content in approximately {target_words} words. Focus on core features and tech stack."},
                {"role": "user", "content": text[:12000]} # Truncate input to avoid errors
            ]
        )
        return response.choices[0].message.content
    except:
        return text[:1000] # Fallback to truncated text if summarization fails

def get_github_readme(repo_url):
    """Fetches raw README content from GitHub."""
    path = repo_url.replace("https://github.com/", "").strip("/")
    for branch in ["main", "master"]:
        raw_url = f"https://raw.githubusercontent.com/{path}/{branch}/README.md"
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            res = r.get(raw_url, headers=headers, timeout=5)
            if res.status_code == 200:
                return res.text
        except r.RequestException:
            continue

    return "README not found."

@st.cache_data
def load_all_context(api_key):
    """Loads and summarizes README files to optimize the knowledge base."""
    combined_context = ""
    dir_path = os.path.dirname(os.path.realpath(__file__))
    client = Groq(api_key=api_key)
    
    # Process local data.md
    data_path = os.path.join(dir_path, "data.md")
    if os.path.exists(data_path):
        with open(data_path, "r", encoding="utf-8") as f:
            combined_context += f"## KP CORE DATA\n{f.read()}\n\n"

    # Process GitHub READMEs with summarization
    github_path = os.path.join(dir_path, "github_repo_links.txt")
    if os.path.exists(github_path):
        with open(github_path, "r", encoding="utf-8") as f:
            for line in f:
                if "," in line:
                    name, url = line.strip().split(",", 1)
                    raw_content = get_github_readme(url.strip())
                    if raw_content != "README not found.":
                        with st.spinner(f"Summarizing {name}..."):
                            summary = summarize_text(client, raw_content)
                            combined_context += f"\n[SOURCE: {name}]\n{summary}\n---\n"
    return combined_context

# --- 4. Main UI Logic ---

st.title("🤖 KP Personal Assistant")

if not st.session_state.context:
    if not user_api_key:
        st.error("Please provide an API_KEY in your .env file.")
        st.stop()
    with st.spinner("Preparing summarized knowledge base..."):
        st.session_state.context = load_all_context(user_api_key)
    st.toast("Context Loaded Successfully!", icon="✅")

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Character Counter Logic
# We use st.empty() to create a persistent spot for the counter
counter_placeholder = st.empty()

if prompt := st.chat_input("Ask a question about KP's data...", max_chars=200):

    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        with st.spinner("Thinking..."):
            client = Groq(api_key=user_api_key)
            recent_history = st.session_state.messages[-5:]

            SYSTEM_INSTRUCTION = (
                "You are a helpful KP Personal assistant. Use the provided context to answer. "
                "If the answer is not in the context, say: 'I can only answer questions based on KP's data.' "
                "Do not use outside knowledge. Never fabricate information. "
                "Only mention the source repository for github projects when answering. No speculation."
            )

            messages = [
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "system", "content": f"CONTEXT:\n{st.session_state.context[:10000]}"}
            ]
            messages.extend(recent_history)

            time.sleep(1) # Buffer for RPM limits
            response = safe_groq_call(client, "llama-3.3-70b-versatile", messages)
            answer = response.choices[0].message.content

            with st.chat_message("assistant"):
                st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

    except Exception as e:
        if "RateLimitError" in str(e):
            st.error("Groq Rate Limit reached. Please wait a few minutes.")
        else:
            st.error(f"Error: {e}")
