import streamlit as st
from groq import Groq
from datetime import datetime

# --- 1. PAGE CONFIG & DARK PRO UI ---
st.set_page_config(page_title="Gobidas Beta", layout="wide", page_icon="🟠")

st.markdown("""
    <style>
    .stApp { background-color: #0A0A0A; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #111111 !important; border-right: 1px solid #222222; }
    .stSidebar .stButton>button {
        background-color: transparent !important; color: #888 !important;
        border: 1px solid #222 !important; border-radius: 12px !important;
        text-align: left !important; width: 100%; transition: 0.3s;
    }
    .stSidebar .stButton>button:hover { color: #FF6D00 !important; border-color: #FF6D00 !important; }
    .main-title { font-size: 2.5rem; font-weight: 900; background: linear-gradient(90deg, #FF6D00, #FFAB40);
                  -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SESSION INITIALIZATION ---
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "chat_history" not in st.session_state: st.session_state.chat_history = {} # Stories all chats
if "current_chat_id" not in st.session_state: st.session_state.current_chat_id = "Default Chat"

# --- 3. LOGIN SYSTEM (Lazy Method) ---
if not st.session_state.logged_in:
    _, center, _ = st.columns([1, 1, 1])
    with center:
        st.markdown("<h1 style='text-align: center; color: #FF6D00;'>Gobidas Access</h1>", unsafe_allow_html=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Initialize System"):
            # Checks your Streamlit Secrets for the password list
            if u in st.secrets["passwords"] and p == st.secrets["passwords"][u]:
                st.session_state.logged_in = True
                st.session_state.user = u
                st.rerun()
            else:
                st.error("Access Denied.")
    st.stop()

# --- 4. SIDEBAR (History & Controls) ---
with st.sidebar:
    st.markdown(f"<h2 style='color:#FF6D00;'>👤 {st.session_state.user.upper()}</h2>", unsafe_allow_html=True)
    
    if st.button("➕ START NEW CHAT"):
        new_id = f"Chat {datetime.now().strftime('%H:%M:%S')}"
        st.session_state.current_chat_id = new_id
        st.rerun()

    st.markdown("### COLLECTIONS")
    for chat_id in st.session_state.chat_history.keys():
        if st.button(f"● {chat_id}"):
            st.session_state.current_chat_id = chat_id
            st.rerun()

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# --- 5. MAIN CHAT LOGIC ---
st.markdown("<h1 class='main-title'>Gobidas Beta</h1>", unsafe_allow_html=True)

# Ensure current chat exists in history
if st.session_state.current_chat_id not in st.session_state.chat_history:
    st.session_state.chat_history[st.session_state.current_chat_id] = []

messages = st.session_state.chat_history[st.session_state.current_chat_id]

# Display history
for msg in messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
if prompt := st.chat_input("Ask Gobidas..."):
    messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages
        )
        ans = res.choices[0].message.content
        st.markdown(ans)
        messages.append({"role": "assistant", "content": ans})
        
