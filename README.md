# Yoliday LLP - Chat Assistant

A simple chat app that takes your questions and gives you two answers — one casual and one formal. It uses a Groq-powered language model behind the scenes and saves your chat history so you can come back to it later.

---

## Live Demo

🔗  https://yoliday-chatbot-assignment.streamlit.app/

Upon launching, the app will prompt you to enter a user_id and GROQ API KEY. You can enter any value for user_id to sign up.
To get your GROQ API KEY, visit: https://console.groq.com/keys

---
## 📁 Folder Structure

```bash
.
├── .env                # Environment variables (local only, not committed)
├── backend.py         # FastAPI app
├── app.py              # Streamlit frontend
├── db/
│   └── database.py     #Setting up database
│   └── crud.py         # Supabase operations
├── utils/
│   └── prompts.py     # Prompt builders
├── tests/
│   └── alltests.py    # All unit/integration tests
├── schemas.py         # Pydantic model for request validation
├── requirements.txt
└── README.md
```
---

## What’s Used

| Part         | Tech                 |
|--------------|----------------------|
| Frontend     | Streamlit            |
| Backend      | FastAPI              |
| Database     | Supabase PostgreSQL  |
| AI Model     | Groq API (Gemma2-9b-It) |
| Database     | Supabase             |
| Testing      | Pytest               |

---

## Project Overview

This project was developed as a coding assignment given during the internship application process at Yoliday LLP. 

This project is a backend-powered chat assistant that responds to your query with dual-style explanations (casual and formal) generated via the Groq AI model. User queries are received through the API and processed using prompt building functions to ensure clear and consistent output by gemma model in JSON format.

User queries and AI-generated responses are stored in a Supabase PostgreSQL database, allowing users to retrieve their conversation history anytime. The historical chats appear in the sidebar of UI.

The backend is built with FastAPI, offering endpoints to generate responses and fetch chat history. The database layer is abstracted with CRUD operations, which interact with Supabase through its Python client.

Various tests using pytest verify prompt building, API endpoint correctness, and database interaction (using mocks), ensuring reliability and maintainability.



## Setup Instructions

1. **Clone the repository**: 
```bash
    git clone <repository-url>
    cd <repository-folder>

```

2. **Install dependencies**: 
```bash
    pip install -r requirements.txt
```

3. **Set Supabase environment variables:**: 
```bash
    export SUPABASE_URL="your_supabase_url_here"
    export SUPABASE_KEY="your_supabase_key_here"
```

4. **Run the backend server:**: 
```bash
    uvicorn backend:app --reload
```

5. **Run the frontend:**: 
```bash
    streamlit run frontend.py
```

4. **Run tests:**: 
```bash
    pytest .\tests\alltests.py -v
```

## Supabase Database Setup

Create the following table in your Supabase PostgreSQL database:

### Table: `prompts`

| Column          | Type                  | Description                                   |
|-----------------|-----------------------|-----------------------------------------------|
| `id`            | `serial` (Primary Key) | Unique identifier for each record             |
| `user_id`       | `text`                | ID of the user who made the query             |
| `query`         | `text`                | The user’s query                              |
| `casual_response`| `text`                | Casual style AI response                       |
| `formal_response`| `text`                | Formal style AI response                       |
| `created_at`    | `timestamp`           | Timestamp when the entry was created (default to now()) |


### SQL to Create Table

```sql
CREATE TABLE prompts (
    id SERIAL PRIMARY KEY,
    user_id TEXT,
    query TEXT NOT NULL,
    casual_response TEXT NOT NULL,
    formal_response TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```


## Prompt Strategy
This project uses two prompt templates to guide the AI in generating consistent and structured responses:

### 1. Initial Prompt
This prompt takes a user's query and instructs the AI to return a structured JSON output with both casual and formal explanations.

```text
    Given the topic: "{query}", respond with:
    1. A casual summary (as if explaining to a friend).
    2. A formal academic explanation (like a scholarly article).

    Respond exactly as a JSON dictionary:
    {"casual_response": "...", "formal_response": "..."}
```

### 2. refinement Prompt
Once the initial response is received, it's refined for clarity and tone using a second prompt:
```text
    You will receive a JSON dictionary with two fields.
    Refine and polish the texts for clarity and style, then return ONLY the refined JSON dictionary with the same keys.
```


## Testing
The project includes tests for:

* Prompt formatting (build_prompt, build_refine_prompt)

* API endpoint validation (/generate, /history)

* Supabase CRUD logic (add_entry, get_history)

* End-to-end flow using mocked Groq responses and database logic


### Run tests using:
```bash
    pytest tests/alltests.py
```
