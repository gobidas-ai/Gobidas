import streamlit as st
import os, json, base64, requests
from groq import Groq
import streamlit.components.v1 as components

# --- 1. CONFIG & KEYS ---
st.set_page_config(page_title="Gobidas AI", layout="wide")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# You MUST get these from the Google reCAPTCHA Admin Console (v2 Checkbox)
SITE_KEY = st.secrets.get("RECAPTCHA_SITE_KEY", "YOUR_SITE_KEY_HERE")

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
        
        # --- OFFICIAL GOOGLE RECAPTCHA V2 ---
        st.write("### Security Check")
        # This renders the official HTML checkbox from Google's servers
        captcha_html = f"""
            <script src="https://www.google.com/recaptcha/api.js" async defer></script>
            <form action="?" method="POST">
              <div class="g-recaptcha" data-sitekey="{SITE_KEY}" data-callback="captchaCallback"></div>
            </form>
            <script>
              function captchaCallback(response) {{
                window.parent.postMessage({{type: 'captcha', value: response}}, '*');
              }}
            </script>
        """
        components.html(captcha_html, height=100)
        
        # Simple verification logic for the launch
        is_human = st.checkbox("I have completed the 'I'm not a robot' check above")
        
        # --- LEGAL ARTICLES ---
        st.markdown("### Legal Agreements")
        st.markdown("""
        <div class='legal-box'>
        <b>Terms of Service:</b> Gobidas AI is an experimental tool. Use at your own risk. 
        No illegal activities or harmful content generation. <br><br>
        <b>Privacy Policy:</b> We store your username locally for login. We do not sell data. 
        History is temporary.
        </div>
        """, unsafe_allow_html=True)
        
        agree = st.checkbox("I accept the Terms and Privacy Policy")
        
        if st.button("CREATE ACCOUNT"):
            if not is_human:
                st.error("Please click the robot check first.")
            elif not agree:
                st.warning("You must accept the legal agreements.")
            elif len(u_sig) < 3:
                st.error("Username too short.")
            else:
                save_user(u_sig, p_sig)
                st.success("Account created! Now go to the 'LOG IN' tab.")
    st.stop()

# --- 4. CHAT INTERFACE ---
st.markdown("<h1 class='main-title'>Gobidas AI</h1>", unsafe_allow_html=True)
# ... [rest of your chat code here]
