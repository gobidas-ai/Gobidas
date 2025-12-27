import streamlit as st
import os
import json
import base64
from groq import Groq
from streamlit_recaptcha import streamlit_recaptcha

# --- 1. CONFIG ---
st.set_page_config(page_title="Gobidas AI", layout="wide")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

USER_DB = "users_db.json"

def load_users():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f: return json.load(f)
    return {"admin": "gobidas2025"}

def save_user(username, password):
    users = load_users()
    users[username] = password
    with open(USER_DB, "w") as f:
        json.dump(users, f)

# --- 2. THEME ---
def get_base64(file):
    try:
        with open(file, 'rb') as f: return base64.b64encode(f.read()).decode()
    except: return ""

bin_str = get_base64('background.jpg')
st.markdown(f"""
<style>
    .stApp {{ 
        background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("data:image/jpeg;base64,{bin_str}"); 
        background-size: cover; 
    }}
    .main-title {{ font-weight: 900; color: #FF6D00; text-align: center; font-size: 5rem; text-shadow: 0px 0px 25px #FF6D00; }}
    .stButton>button {{ width: 100%; border: 2px solid #FF6D00 !important; color: white !important; background: rgba(0,0,0,0.2) !important; font-weight: bold; border-radius: 8px; }}
    .legal-box {{ font-size: 0.85rem; color: #bbb; background: rgba(255,109,0,0.1); padding: 15px; border-radius: 10px; border: 1px solid #FF6D00; margin-bottom: 20px; }}
</style>
""", unsafe_allow_html=True)

# --- 3. GATEWAY ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["LOG IN", "CREATE ACCOUNT"])
    
    with tab1:
        u_login = st.text_input("Username", key="l_u")
        p_login = st.text_input("Password", type="password", key="l_p")
        if st.button("LOG IN"):
            users = load_users()
            if u_login in users and users[u_login] == p_login:
                st.session_state.user = u_login
                st.rerun()
            else: st.error("Invalid Credentials")

    with tab2:
        u_sig = st.text_input("New Username", key="s_u")
        p_sig = st.text_input("New Password", type="password", key="s_p")
        
        # --- THE OFFICIAL GOOGLE CAPTCHA ---
        # This renders the exact box from your image
        captcha_valid = streamlit_recaptcha(
            site_key=st.secrets["RECAPTCHA_SITE_KEY"],
            secret_key=st.secrets["RECAPTCHA_SECRET_KEY"]
        )
        
        # --- OFFICIAL TERMS & POLICY ---
        st.markdown("### Legal Agreements")
        st.markdown("""
        <div class='legal-box'>
        <b>Terms of Service</b><br>
        By creating an account, you agree that Gobidas AI is an experimental tool. 
        You agree not to use the service for illegal activities or to generate harmful content. 
        Data is stored locally for session management.<br><br>
        <b>Privacy Policy</b><br>
        We do not sell your data. Your chat history is stored during your active session. 
        Cookies are used only for authentication purposes.
        </div>
        """, unsafe_allow_html=True)
        
        agree = st.checkbox("I accept the Terms of Service and Privacy Policy")
        
        if st.button("CREATE ACCOUNT"):
            if not captcha_valid:
                st.error("Please complete the 'I'm not a robot' check.")
            elif not agree:
                st.warning("You must accept the legal agreements to continue.")
            elif len(u_sig) < 3 or len(p_sig) < 6:
                st.error("Username/Password too short.")
            else:
                save_user(u_sig, p_sig)
                st.success("Account created! You can now log in.")
    st.stop()

# --- 4. CHAT INTERFACE ---
st.markdown("<h1 class='main-title'>Gobidas AI</h1>", unsafe_allow_html=True)
# ... (rest of your chat code goes here)
