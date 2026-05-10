# KP Resume Assistant

A Streamlit-based chat assistant for exploring KP-related content from local data and GitHub README files.

Live app: https://kp-personal-assistant.streamlit.app/

The app loads `data.md`, fetches repository README content from `github_readme.txt`, summarizes it, and answers user questions using Groq models.

## Features

- Summarizes local `data.md` content and GitHub README content.
- Loads GitHub repository URLs from `github_readme.txt`.
- Uses Groq LLM models for summarization and chat responses.
- Caches loaded context to improve performance and reliability.
- Applies retry logic on Groq API calls to reduce failures.

## Prerequisites

- Python 3.11+ (recommended)
- A valid Groq API key

## Dependencies

All required Python packages are listed in `requirements.txt`.

Key packages include:

- `streamlit`
- `groq`
- `requests`
- `python-dotenv`
- `tenacity`
- `markdown`
- `faiss-cpu`
- `sentence-transformers`
- `torch`
- `torchvision`
- `langchain-text-splitters`

## Setup

1. Create and activate a virtual environment.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies.

```powershell
pip install -r requirements.txt
```

3. Create a `.env` file in the project root and add your Groq API key.

```text
API_KEY=your_groq_api_key_here
```

4. Populate `github_readme.txt` with repositories to summarize.

Example format:

```text
Project Name,https://github.com/owner/repo
```

## Run the app

```powershell
streamlit run app.py
```

Open the URL shown in the terminal to use the app.

Hosted version: https://kp-personal-assistant.streamlit.app/

## Usage

- Ask questions through the chat input.
- The assistant responds based on loaded KP data and summarized GitHub README content.
- It intentionally avoids speculation and only answers from the provided context.

## File Overview

- `app.py` — main Streamlit application.
- `data.md` — local project data used as part of the knowledge base.
- `github_readme.txt` — list of GitHub repositories to summarize.
- `requirements.txt` — Python dependencies.
- `.env` — environment variables, including `API_KEY`.

## Notes

- If `API_KEY` is missing, the app shows an error and stops.
- Local and GitHub content is summarized before chat interactions begin.
- The app uses a faster summarization model and a larger conversational model for responses.
