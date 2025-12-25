import streamlit as st
from groq import Groq
import json, os, base64, io
from PIL import Image

# --- 1. UI SETUP ---
st.set_page_config(page_title="GOBIDAS BETA", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0A0A0A; color: white; }
    [data-testid="stSidebar"] { background: #111 !important; border-right: 2px solid #FF6D00; width: 300px !important; }
    .main-title { font-weight: 900; background: linear-gradient(90deg, #FF6D00, #FFAB40); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; font-size: 3rem; }
    .stButton>button { background: linear-gradient(90deg, #FF6D00, #FFAB40) !important; color: white !important; border-radius: 8px; border: none; width: 100%; font-weight: bold; }
    .stChatMessage { background-color: #161616 !important; border-radius: 12px !important; border: 1px solid #222 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE SYSTEM ---
DB_FILE = "gobidas_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                if "users" in data and "history" in data:
                    return data
        except:
            pass
    return {"users": {}, "history": {}}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# Initialize database in session
if "db" not in st.session_state:
    st.session_state.db = load_db()

# --- 3. LOGIN / JOIN ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>GOBIDAS BETA</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Login", "Join"])
    
    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("LOG IN"):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                st.session_state.user = u
                st.rerun()
            else: st.error("Invalid Login")
            
    with tab2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("SIGN UP"):
            if nu and np:
                st.session_state.db["users"][nu] = np
                st.session_state.db["history"][nu] = []
                save_db(st.session_state.db)
                st.success("Account Created! Use Login tab.")
    st
