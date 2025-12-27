import streamlit as st
from groq import Groq
import json, os, base64, io, time
import pandas as pd
from PIL import Image
from st_gsheets_connection import GSheetsConnection

# --- 1. CONFIG & UI (EXACTLY AS YOU MADE IT) ---
st.set_page_config(page_title="Gobidas Beta", layout="wide", initial_sidebar_state="expanded")

def get_base64(file):
    if os.path.exists(file):
        with open(file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

bin_str = get_base64('background.jpg')

st.markdown(f"""
<style>
    [data-testid="stHeader"] {{ background: transparent !important; }}
    header[data-testid="stHeader"] > div:first-child {{ display: none !important; }}
    [data-testid="stSidebarCollapseButton"] {{
        visibility: visible !important;
        display: block !important;
        color: #FF6D00 !important;
        background: rgba(0,0,0,0.8) !important;
        border: 2px solid #FF6D00 !important;
        border-radius: 8px !important;
        z-index: 999999 !important;
        opacity: 1 !important;
    }}
    footer, .stDeployButton, [data-testid="stStatusWidget"] {{ display: none !important; }}
    [data-testid="stSidebar"] {{ background-color: rgba(10, 10, 10, 0.98) !important; border-right: 2px solid #FF6D00; min-width: 320px !important; }}
    .stApp {{ background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("data:image/jpeg;base64,{bin_str if bin_str else ''}"); background-size: cover; background-attachment: fixed; }}
    .main-title {{ font-weight: 900; color: #FF6D00; text-align: center; font-size: 5.5rem; text-shadow: 0px 0px 35px rgba(255, 109, 0, 0.8); margin-top: -60px; }}
    .stButton>button {{ width: 100%; border-radius: 12px; border: 1px solid #FF6D00 !important; color: white !important; background: transparent; font-weight: 800; text-transform: uppercase; }}
    .stButton>button:hover {{ background: #FF6D00 !important; color: black !important; }}
</style>
""", unsafe_allow_html=True)

# --- 2. PERMANENT DATABASE (GOOGLE SHEETS) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_db_df():
    try:
        # ttl=0 means it always gets the freshest data from the sheet
        return conn.read(ttl=0)
    except:
        return pd.DataFrame(columns=["username", "password"])

def show_legal():
    st.markdown("## 📜 GOVERNANCE, PRIVACY & LEGAL PROTOCOLS")
    st.error("### **ARTICLE I: USER ACKNOWLEDGMENT OF BETA STATUS**")
    st.write("Gobidas is in Beta. Use at your own risk. AI is probabilistic.")
    st.markdown("### **ARTICLE II: LIMITATION OF LIABILITY**")
    st.write("Developer is not liable for AI-generated content.")
    st.markdown("### **ARTICLE III: DATA SOVEREIGNTY**")
    st.write("Credentials are saved in a secure external vault. History is purged every 30 days.")

# --- 3. LOGIN / SIGN UP (NO DELETIONS) ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas BETA</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.8, 1])
    with c2:
        mode = st.radio("GATEWAY ACCESS", ["LOG IN", "SIGN UP"], horizontal=True)
        u = st.text_input("USERNAME")
        p = st.text_input("PASSWORD", type="password")
        agree = st.checkbox("I confirm agreement to the Privacy & Terms")
        
        if st.button("ENTER SYSTEM", disabled=not agree):
            df = get_db_df()
            if mode == "LOG IN":
                match = df[(df['username'] == u) & (df['password'] == p)]
                if not match.empty:
                    st.session_state.user = u
                    st.session_state.messages = []
                    st.rerun()
                else: st.error("ACCESS DENIED: INCORRECT CREDENTIALS")
            else:
                if u and p:
                    if u in df['username'].values:
                        st.error("USERNAME ALREADY TAKEN")
                    else:
                        # Append to Google Sheet permanently
                        new_user = pd.DataFrame([{"username": u, "password": p}])
                        updated_df = pd.concat([df, new_user], ignore_index=True)
                        conn.update(data=updated_df)
                        st.success("CREDENTIALS REGISTERED PERMANENTLY. PROCEED TO LOG IN.")
        st.divider()
        with st.expander("REVIEW FULL LEGAL DOCUMENTATION"): show_legal()
    st.stop()

# --- 4. SIDEBAR & CHAT ---
# (Your original Sidebar and Chat logic goes here)
# Just remember to use st.session_state.user to filter chats!
st.sidebar.title(f"@{st.session_state.user}")
st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
st.write("Welcome to the Beta launch.")
