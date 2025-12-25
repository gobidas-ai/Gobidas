import streamlit as st
from groq import Groq
import json, os

# --- 1. SIMPLE UI ---
st.set_page_config(page_title="GOBIDAS TEXT", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0A0A0A; color: white; }
    [data-testid="stSidebar"] { background: #111 !important; border-right: 2px solid #FF6D00; }
    .main-title { font-weight: 900; color: #FF6D00; text-align: center; font-size: 3rem; }
    .stButton>button { background: #FF6D00 !important; color: white !important; font-weight: bold; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE BULLETPROOF DATABASE ---
DB_FILE = "gobidas_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                # Force the correct structure if it's broken
                if not isinstance(data, dict) or "users" not in data:
                    return {"users": {}, "history": {}}
                if "history" not in data:
                    data["history"] = {}
                return data
        except:
            return {"users": {}, "history": {}}
    return {"users": {}, "history": {}}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

if "db" not in st.session_state:
    st.session_state.db = load_db()

# --- 3. LOGIN SYSTEM ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>GOBIDAS LOGIN</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["Login", "Join"])
    
    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("LOG IN"):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                st.session_state.user = u
                st.session_state.messages = []
                st.rerun()
            else:
                st.error("Invalid Username or Password")
    
    with t2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("CREATE ACCOUNT"):
            if nu and np:
                st.session_state.db["users"][nu] = np
                st.session_state.db["history"][nu] = []
                save_db(st.session_state.db)
                st.success("Success! Please log in.")
    st.stop()

# --- 4. SIDEBAR ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.title(f"🟠 {st.session_state.user}")
    if st.button("➕ NEW CHAT"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    # This button wipes the local data if things get buggy
    if st.button("⚠️ CLEAR MY HISTORY"):
        st.session_state.db["history"][st.session_state.user] = []
        save_db(st.session_state.db)
        st.session_state.messages = []
        st.rerun()

# --- 5. CHAT ENGINE ---
st.markdown("<h1 class='main-title'>GOBIDAS BETA</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Show the messages
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# User input
if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Using the most stable text model available
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.messages
            )
            ans = response.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            # Save to history safely
            if st.session_state.user not in st.session_state.db["history"]:
                st.session_state.db["history"][st.session_state.user] = []
            
            # Just keep the last chat active for simplicity
            st.session_state.db["history"][st.session_state.user] = st.session_state.messages
            save_db(st.session_state.db)
            
        except Exception as e:
            st.error(f"AI Error: {str(e)}")
