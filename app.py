import streamlit as st
import os
import json
import base64
from groq import Groq

# --- 1. CONFIG ---
st.set_page_config(page_title="Gobidas AI", layout="wide")

# Ensure you have your new key in Secrets!
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 2. THEME & BACKGROUND ---
def get_base64(file):
    try:
        if os.path.exists(file):
            with open(file, 'rb') as f: return base64.b64encode(f.read()).decode()
    except: return ""
    return ""

bin_str = get_base64('background.jpg')
st.markdown(f"""
<style>
    [data-testid="stHeader"] {{ background: transparent !important; }}
    .stApp {{ 
        background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("data:image/jpeg;base64,{bin_str}"); 
        background-size: cover; 
    }}
    .main-title {{ font-weight: 900; color: #FF6D00; text-align: center; font-size: 5rem; text-shadow: 0px 0px 25px #FF6D00; margin-bottom: 20px; }}
    .stButton>button {{ width: 100%; border: 2px solid #FF6D00 !important; color: white !important; background: rgba(0,0,0,0.3) !important; font-weight: bold; border-radius: 8px; height: 3em; }}
    .stButton>button:hover {{ background: #FF6D00 !important; color: black !important; }}
    [data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 1px solid #FF6D00; }}
</style>
""", unsafe_allow_html=True)

# --- 3. LOGIN GATEWAY ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.write("### BETA ACCESS")
        u_in = st.text_input("USERNAME").strip()
        p_in = st.text_input("PASSWORD", type="password")
        
        # --- THE ROBOT SECURITY CHECK ---
        st.divider()
        is_human = st.checkbox("I am not a robot")
        
        if st.button("ENTER SYSTEM"):
            if not is_human:
                st.warning("Please verify you are not a robot.")
            elif u_in in st.secrets["users"] and st.secrets["users"][u_in] == p_in:
                st.session_state.user = u_in
                st.session_state.messages = [{"role": "system", "content": "You are Gobidas AI, a helpful assistant."}]
                st.success(f"Welcome back, {u_in}!")
                st.rerun()
            else:
                st.error("Access Denied: Invalid Username or Password.")
        
        st.caption("Don't have an account? Contact the administrator for access.")
    st.stop()

# --- 4. CHAT INTERFACE ---
with st.sidebar:
    st.title(f"@{st.session_state.user}")
    st.divider()
    st.subheader("Settings")
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = [{"role": "system", "content": "You are Gobidas AI."}]
        st.rerun()
    
    st.file_uploader("🖼️ Attach Image (BETA)", type=['png', 'jpg'])
    
    st.divider()
    if st.button("🚪 LOGOUT"):
        del st.session_state.user
        st.rerun()

st.markdown("<h1 class='main-title'>Gobidas AI</h1>", unsafe_allow_html=True)

# Display Chat
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# AI Interaction
if prompt := st.chat_input("How can I help you?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            resp = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=st.session_state.messages
            )
            full_resp = resp.choices[0].message.content
            st.markdown(full_resp)
            st.session_state.messages.append({"role": "assistant", "content": full_resp})
        except Exception as e:
            st.error(f"AI Connection Error: {e}")
