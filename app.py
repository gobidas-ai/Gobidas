import streamlit as st
import os
import json
import base64
import random
from groq import Groq

# --- 1. CONFIG ---
st.set_page_config(page_title="Gobidas AI", layout="wide")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# File where user accounts are stored
USER_DB = "users_db.json"

def load_users():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f: return json.load(f)
    return {"admin": "gobidas2025"} # Default admin

def save_user(username, password):
    users = load_users()
    users[username] = password
    with open(USER_DB, "w") as f:
        json.dump(users, f)

# --- 2. THEME & UI ---
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
    .main-title {{ font-weight: 900; color: #FF6D00; text-align: center; font-size: 5rem; text-shadow: 0px 0px 25px #FF6D00; margin-bottom: 10px; }}
    .stButton>button {{ width: 100%; border: 2px solid #FF6D00 !important; color: white !important; background: rgba(0,0,0,0.2) !important; font-weight: bold; border-radius: 8px; }}
    .stButton>button:hover {{ background: #FF6D00 !important; color: black !important; }}
    .legal-text {{ font-size: 0.8rem; color: #999; background: rgba(255,109,0,0.05); padding: 10px; border-radius: 5px; border-left: 2px solid #FF6D00; }}
</style>
""", unsafe_allow_html=True)

# --- 3. GATEWAY (LOGIN & SIGN UP) ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["LOG IN", "CREATE ACCOUNT"])
    
    with tab1:
        u_login = st.text_input("Username", key="l_u").strip()
        p_login = st.text_input("Password", type="password", key="l_p")
        if st.button("ENTER SYSTEM"):
            users = load_users()
            if u_login in users and users[u_login] == p_login:
                st.session_state.user = u_login
                st.rerun()
            else: st.error("Invalid credentials.")

    with tab2:
        u_sig = st.text_input("Choose Username", key="s_u").strip()
        p_sig = st.text_input("Choose Password", type="password", key="s_p")
        
        # --- THE OFFICIAL CAPTCHA CHECK ---
        st.write("### Security Check")
        # Real-world CAPTCHA alternative: Logic challenge
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        captcha_ans = st.text_input(f"What is {num1} + {num2}? (Robot Check)")
        
        # --- TERMS & POLICY ---
        with st.expander("Terms of Service & Privacy Policy"):
            st.markdown("""
            <div class='legal-text'>
            <b>1. Data Collection:</b> We store your username and password locally for login purposes.<br>
            <b>2. AI Usage:</b> Gobidas AI is powered by Groq. Do not share sensitive personal data.<br>
            <b>3. Liability:</b> User assumes all responsibility for generated content.
            </div>
            """, unsafe_allow_html=True)
        agree = st.checkbox("I agree to the Terms and Policies")
        
        if st.button("REGISTER"):
            if not agree:
                st.warning("You must agree to the terms.")
            elif captcha_ans != str(num1 + num2):
                st.error("CAPTCHA failed. Are you a robot?")
            elif len(u_sig) < 3 or len(p_sig) < 6:
                st.error("Username (3+) and Password (6+) too short.")
            else:
                save_user(u_sig, p_sig)
                st.success("Account created! Please log in.")

    st.stop()

# --- 4. CHAT INTERFACE ---
with st.sidebar:
    st.title(f"@{st.session_state.user}")
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()
    st.file_uploader("🖼️ Attach Image (Coming Soon)", type=['png', 'jpg'])
    if st.button("🚪 LOGOUT"):
        del st.session_state.user
        st.rerun()

st.markdown("<h1 class='main-title'>Gobidas AI</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "You are Gobidas AI."}]

for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Message Gobidas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        resp = client.chat.completions.create(model="llama3-8b-8192", messages=st.session_state.messages)
        st.markdown(resp.choices[0].message.content)
        st.session_state.messages.append({"role": "assistant", "content": resp.choices[0].message.content})
