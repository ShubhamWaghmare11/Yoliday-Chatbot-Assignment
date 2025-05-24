"""
Streamlit Frontend for Yoliday LLP Chatbot Assignment

Features:
- Takes User ID and Groq API Key as input
- Sends user queries to FastAPI backend (/generate)
- Displays AI-generated casual and formal responses
- Shows chat history from Supabase via /history endpoint
- Supports reloading past conversations
- Provides logout functionality
"""


# Importing libraries
import streamlit as st
import requests
from datetime import datetime
import time



# Page setup
st.set_page_config(initial_sidebar_state="collapsed")

# Authentication Form (if session not set)
if "user_id" not in st.session_state:
    st.markdown("### Enter your User ID and GROQ API Key to continue")

    with st.form("user_credentials_form", clear_on_submit=True):
        user_id_input = st.text_input("User ID")
        groq_api_key_input = st.text_input("GROQ API Key", type="password")

        # Add clickable link below the input box
        st.markdown(
            "Don't have a GROQ API Key? "
            "[Click here to get one](https://console.groq.com/keys) 🔑",
            unsafe_allow_html=True
        )

        submitted = st.form_submit_button("Submit")

        if submitted:
            if not user_id_input.strip():
                st.warning("User ID cannot be empty.")
            elif not groq_api_key_input.strip():
                st.warning("GROQ API Key cannot be empty.")
            else:
                st.session_state.user_id = user_id_input.strip()
                st.session_state.groq_api_key = groq_api_key_input.strip()
                st.rerun()

    st.stop()


#Main Chat UI
st.title("Yoliday LLP Assignment")

st.markdown("""
    <style>
    /* Button style */
    div.stButton > button {
        background-color: transparent;
        color: white;
        border: none;
        box-shadow: none;
        padding: 10px;
        margin-left: 5px;
        font-size: 16px;
        text-decoration: none;  /* remove underline */
        justify-content:left;
        width: 100%;
        cursor: pointer;
        transition: background-color 0.2s ease;
        border-radius: 6px;
    }
    div.stButton > button:hover {
        background-color: #333333;  /* dark gray hover */
    }

    /* Header style like ChatGPT section titles */
    h3 {
        color: #aaa !important;
        font-weight: 900 !important;
        font-size: 14px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 12px 0 4px 0 !important;
        padding-bottom: 10px;
        border-bottom: 1px solid #444;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "awaiting_response" not in st.session_state:
    st.session_state.awaiting_response = False

if 'history_loaded' not in st.session_state:
    st.session_state.history_loaded = False

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []


if "selected_history" in st.session_state:
    print("here")
    if st.button("🔙 Back to chat"):
        del st.session_state.selected_history
        st.rerun()

    selected = st.session_state.selected_history
    with st.chat_message('user'):
        st.markdown(f"**Query:** {selected['query']}")
    
    with st.chat_message('ai'):
        cols = st.columns(2)
        with cols[0]:
            st.markdown("### 🎓 Formal Response")
            st.markdown(selected['formal_response'])

        with cols[1]:
            st.markdown("### 😄 Casual Response")
            st.markdown(selected['casual_response'])

    st.markdown("---")

    st.stop()


# Load and display history logic
def load_history():
    try:
        print(f"https://yoliday-chatbot-assignment.onrender.com/history?user_id={st.session_state.user_id}")
        response = requests.get(f"https://yoliday-chatbot-assignment.onrender.com/history?user_id={st.session_state.user_id}")
        print(response)
        print("RESPONSE: ",response.json())
        data = response.json()
        st.session_state.chat_history = data["output"]
        st.session_state.history_loaded = True
    except Exception as e:
            print(f"ERROR: {e}")
            st.error(f"Request failed: {e}")
            # Don't append error response to chat
            st.session_state.awaiting_response = False
            st.rerun()



# Display message history

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg['role'] == 'ai':
            cols = st.columns(2)
            with cols[1]:
                st.markdown("### 😄 Casual Response")
                st.markdown(msg['text'][0])

            with cols[0]:
                st.markdown("### 🎓 Formal Response")
                st.markdown(msg['text'][1])


        else:
            st.markdown(msg["text"])


# Only show input if bot is not responding
if not st.session_state.awaiting_response:
    if prompt := st.chat_input("Say something"):
        # Add user message
        st.session_state.awaiting_response = True
        st.session_state.messages.append({"role": "user", "text": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Set flag so input box is hidden until response comes

        # Trigger rerun to move into response processing block
        st.rerun()


# If awaiting_response is True, process the response
elif st.session_state.awaiting_response:
    prompt = st.session_state.messages[-1]["text"]  # last user input
    print("PROMPT: ",prompt)
    with st.spinner("Thinking..."):
        payload = {
            "user_id": st.session_state.user_id,
            "query": prompt,
            "groq_api_key": st.session_state.groq_api_key
        }
        print(payload)

        try:
            response = requests.post("https://yoliday-chatbot-assignment.onrender.com/generate", json=payload)
            response.raise_for_status()
            data = response.json()
            print("DATA: ",data)
            ai_response = (
                data.get("output")
            )
            # final_response = f"""Casual Response: {ai_response['casual_response']}\n\nFormal Response: {ai_response['formal_response']}"""
            print(ai_response)
            st.session_state.messages.append({"role": "ai", "text": [ai_response['casual_response'],ai_response['formal_response']]})
            
            #Reset flag to re enable output
            st.session_state.awaiting_response = False
            st.session_state.history_loaded = False

            # Trigger rerun to show input again
            st.rerun()
        
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 401:
                st.error("Authentication failed: Invalid Groq API Key. Redirecting...")
                time.sleep(2)
                st.session_state.pop("user_id", None)
                st.rerun()
            else:
                st.error(f"HTTP error occurred: {http_err}")
        except Exception as e:
            st.error(f"Something went wrong: {e}")




# Preprocessing the tiemstamp info for sorting
def parse_date_isoformat(date_str):
    if '.' in date_str:
        date_part, micro_part = date_str.split('.')
        # micro_part may end with 'Z' or timezone info - handle only microseconds here
        microseconds = micro_part[:6].ljust(6, '0')  # pad to 6 digits
        rest = micro_part[6:]  # possible timezone info
        fixed_date_str = f"{date_part}.{microseconds}{rest}"
    else:
        fixed_date_str = date_str
    return datetime.fromisoformat(fixed_date_str)

# Retrieving previous chats of user
def set_selected_history(index):
    try:
        response = requests.get(f"https://yoliday-chatbot-assignment.onrender.com/history?user_id={st.session_state.user_id}")
        response.raise_for_status()
        all_chats = response.json()
        selected=all_chats['output'][index]
        if 'created_at' in selected:
            selected['created_at'] = parse_date_isoformat(selected['created_at'])

        # print(all_chats)
        st.session_state.selected_history = selected
        print(selected)

    except requests.exceptions.RequestException as req_err:
        st.error(f"Network error: {req_err}")
    except Exception as e:
        st.error(f"Failed to load chat: {e}")



#Populating sidebar with historical chats
with st.sidebar:
    if st.button("Logout"):
        # Clear user session state
        for key in ["user_id", "groq_api_key", "messages", "awaiting_response", "history_loaded", "chat_history", "selected_history"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    st.markdown("---")  # separator line
    st.text("All history")
    if not st.session_state.history_loaded:
        load_history()

    

    st.markdown('<h3>Today</h3>', unsafe_allow_html=True)
    for i, chat in enumerate(st.session_state.chat_history):
        try:
            if parse_date_isoformat(chat['created_at']).date() == datetime.today().date():
                st.button(
                    chat["query"],
                    key=f"history_{i}",
                    on_click=set_selected_history,
                    args=(i,)
                )
        except Exception as e:
            st.error(f"Invalid date format: {e}")

    st.markdown('<h3>Older Chats</h3>', unsafe_allow_html=True)
    for i, chat in enumerate(st.session_state.chat_history):
        try:
            if parse_date_isoformat(chat['created_at']).date() != datetime.today().date():
                st.button(
                    chat["query"],
                    key=f"history_{i}_old",
                    on_click=set_selected_history,
                    args=(i,)
                )
        except Exception as e:
            st.error(f"Invalid date format: {e}")

