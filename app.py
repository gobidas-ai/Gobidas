import streamlit as st
from groq import Groq

# --- 1. PREMIUM PRO UI (The "Cyber Orange" Look) ---
st.set_page_config(page_title="Gobidas Pro", layout="wide", page_icon="🟠")

st.markdown("""
    <style>
    .stApp { background-color: #0A0A0A; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #111 !important; border-right: 1px solid #222; }
    
    /* Title Gradient */
    .main-title {
        font-size: 3rem; font-weight: 900;
        background: linear-gradient(90deg, #FF6D00, #FFAB40);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 30px;
    }

    /* Modern Chat Bubbles */
    .stChatMessage {
        background-color: #161616 !important;
        border: 1px solid #222 !important;
        border-radius: 20px !important;
    }

    /* Floating Input Bar */
    .stChatInputContainer {
        background-color: #1A1A1A !important;
        border: 1px solid #FF6D00 !important;
        border-radius: 15px !important;
    }
    
    /* Pro Buttons */
    .stButton>button {
        background: linear-gradient(90deg, #FF6D00, #FFAB40) !important;
        color: white !important; font-weight: bold !important;
        border-radius: 12px !important; border: none !important;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE BRAIN ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("Go to Settings > Secrets and add: GROQ_API_KEY = 'your_key'")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. THE INTERFACE ---
with st.sidebar:
    st.markdown("<h2 style='color: #FF6D00;'>GOBIDAS PRO</h2>", unsafe_allow_html=True)
    if st.button("➕ NEW SESSION"):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.info("System: Online")

st.markdown("<h1 class='main-title'>Gobidas Pro</h1>", unsafe_allow_html=True)

# Display Chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Chat Input
if prompt := st.chat_input("Command Gobidas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.messages
        )
        ans = res.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
