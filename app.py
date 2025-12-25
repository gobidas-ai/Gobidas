import streamlit as st
import ollama
import sqlite3
import hashlib
import os
from datetime import datetime

# --- 1. PAGE CONFIG & DARK PRO UI ---
st.set_page_config(page_title="Gobidas Beta", layout="wide", page_icon="🟠")

st.markdown("""
    <style>
    /* Main Dark Canvas */
    .stApp {
        background-color: #0A0A0A;
        color: #E0E0E0;
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar: Sleek Charcoal with Glass Effect */
    [data-testid="stSidebar"] {
        background-color: #111111 !important;
        border-right: 1px solid #222222;
    }

    /* Premium Logo Container */
    .logo-container {
        text-align: center;
        padding: 20px;
        background: linear-gradient(180deg, #1A1A1A 0%, #111111 100%);
        border-radius: 20px;
        margin-bottom: 25px;
        border: 1px solid #333;
    }

    /* History Buttons: Cyber Orange Style */
    .stSidebar .stButton>button {
        background-color: transparent !important;
        color: #888 !important;
        border: 1px solid #222 !important;
        border-radius: 12px !important;
        text-align: left !important;
        padding: 10px 15px !important;
        transition: 0.3s all;
        font-size: 0.9rem;
        width: 100%;
    }
    
    .stSidebar .stButton>button:hover {
        color: #FF6D00 !important;
        border-color: #FF6D00 !important;
        background-color: rgba(255, 109, 0, 0.05) !important;
        box-shadow: 0 0 15px rgba(255, 109, 0, 0.1);
    }

    /* Chat Bubbles: Modern Minimalist */
    .stChatMessage {
        background-color: #161616 !important;
        border: 1px solid #222 !important;
        border-radius: 20px !important;
        padding: 20px !important;
        margin-bottom: 15px !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }

    /* User Message: Electric Orange Accent */
    div[data-testimonial="user"] {
        border-right: 4px solid #FF6D00 !important;
    }

    /* Modern Floating Input Bar */
    .stChatInputContainer {
        background-color: #1A1A1A !important;
        border-radius: 15px !important;
        border: 1px solid #333 !important;
        padding: 5px !important;
    }

    /* Custom Title Gradient */
    .main-title {
        font-size: 2.5rem;
        font-weight: 900;
        background: linear-gradient(90deg, #FF6D00, #FFAB40);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ARCHITECTURE ---
def init_db():
    conn = sqlite3.connect('gobidas_vault.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS chat_sessions (id INTEGER PRIMARY KEY, username TEXT, title TEXT, timestamp TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS messages (session_id INTEGER, role TEXT, content TEXT)')
    conn.commit()
    return conn

conn = init_db()

# --- 3. SESSION LOGIC ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "current_session_id" not in st.session_state: st.session_state.current_session_id = None

# --- 4. AUTHENTICATION (Modern Minimalist) ---
if not st.session_state.logged_in:
    _, center, _ = st.columns([1, 1, 1])
    with center:
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; color: #FF6D00;'>Gobidas Beta</h1>", unsafe_allow_html=True)
        with st.container():
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            col1, col2 = st.columns(2)
            if col1.button("Login"):
                hp = hashlib.sha256(p.encode()).hexdigest()
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, hp))
                if c.fetchone():
                    st.session_state.logged_in = True
                    st.session_state.user = u
                    st.rerun()
            if col2.button("Join"):
                hp = hashlib.sha256(p.encode()).hexdigest()
                try:
                    conn.cursor().execute("INSERT INTO users VALUES (?,?)", (u, hp))
                    conn.commit()
                    st.success("Welcome aboard!")
                except: st.error("User exists.")

# --- 5. MAIN APPLICATION ---
else:
    with st.sidebar:
        # LOGO AREA
        st.markdown("<div class='logo-container'>", unsafe_allow_html=True)
        if os.path.exists("logo_cube.jpg"):
            st.image("logo_cube.jpg", width=120)
        st.markdown(f"<p style='margin-top:10px; opacity:0.6;'>{st.session_state.user.upper()}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        if st.button("➕ START NEW CHAT"):
            st.session_state.current_session_id = None
            st.rerun()
        
        st.markdown("<br><p style='font-size:0.7rem; color:#555;'>COLLECTIONS</p>", unsafe_allow_html=True)
        c = conn.cursor()
        c.execute("SELECT id, title FROM chat_sessions WHERE username=? ORDER BY id DESC", (st.session_state.user,))
        for s_id, title in c.fetchall():
            if st.button(f"● {title}", key=f"sess_{s_id}"):
                st.session_state.current_session_id = s_id
                st.rerun()
        
        st.markdown("---")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # CHAT AREA
    st.markdown("<h1 class='main-title'>Gobidas Beta</h1>", unsafe_allow_html=True)

    messages_to_show = []
    if st.session_state.current_session_id:
        c.execute("SELECT role, content FROM messages WHERE session_id=?", (st.session_state.current_session_id,))
        messages_to_show = [{"role": r, "content": c} for r, c in c.fetchall()]

    for msg in messages_to_show:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Vision Logic
    uploaded_file = st.sidebar.file_uploader("📎 Upload Image for Vision Mode", type=['png', 'jpg', 'jpeg'])

    if prompt := st.chat_input("Ask anything..."):
        if not st.session_state.current_session_id:
            title = (prompt[:25] + '...') if len(prompt) > 25 else prompt
            c.execute("INSERT INTO chat_sessions (username, title, timestamp) VALUES (?,?,?)", 
                      (st.session_state.user, title, datetime.now().isoformat()))
            st.session_state.current_session_id = c.lastrowid
            conn.commit()

        c.execute("INSERT INTO messages VALUES (?,?,?)", (st.session_state.current_session_id, "user", prompt))
        conn.commit()

        with st.chat_message("user"):
            st.markdown(prompt)
            if uploaded_file: st.image(uploaded_file, width=300)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                try:
                    if uploaded_file:
                        # Use Moondream for RTX 2050 stability
                        res = ollama.chat(model='moondream', messages=[{'role': 'user', 'content': prompt, 'images': [uploaded_file.getvalue()]}])
                    else:
                        res = ollama.chat(model='llama3.2', messages=messages_to_show + [{"role": "user", "content": prompt}])
                    
                    ans = res['message']['content']
                    st.markdown(ans)
                    c.execute("INSERT INTO messages VALUES (?,?,?)", (st.session_state.current_session_id, "assistant", ans))
                    conn.commit()
                    st.rerun()
                except Exception as e:
                    st.error(f"Hardware error: {e}")
