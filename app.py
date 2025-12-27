import streamlit as st
import os, json, base64
from groq import Groq
import streamlit.components.v1 as components

# --- 1. CONFIG ---
st.set_page_config(page_title="Gobidas AI", layout="wide")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Use the keys you got from Google
SITE_KEY = st.secrets.get("RECAPTCHA_SITE_KEY", "PASTE_SITE_KEY_HERE")

USER_DB = "users_db.json"

def load_users():
    if os.path.exists(USER_DB):
        try:
            with open(USER_DB, "r") as f: return json.load(f)
        except: return {"admin": "gobidas2025"}
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
    
    t1, t2 = st.tabs(["LOG IN", "CREATE ACCOUNT"])
    
    with t1:
        u_l = st.text_input("Username", key="login_u")
        p_l = st.text_input("Password", type="password", key="login_p")
        if st.button("LOG IN"):
            users = load_users()
            if u_l in users and users[u_l] == p_l:
                st.session_state.user = u_l
                st.rerun()
            else: st.error("Invalid credentials.")

    with t2:
        u_s = st.text_input("New Username", key="reg_u")
        p_s = st.text_input("New Password", type="password", key="reg_p")
        
        st.write("### Security Check")
        # Official Google reCAPTCHA iframe
        captcha_html = f"""
            <script src="https://www.google.com/recaptcha/api.js" async defer></script>
            <div class="g-recaptcha" data-sitekey="{SITE_KEY}"></div>
        """
        components.html(captcha_html, height=80)
        is_human = st.checkbox("I have completed the 'I'm not a robot' check above")
        
        st.markdown("### Legal Agreements")
        st.markdown("""<div class='legal-box'>
        <b>Terms of Service:</b> Gobidas AI is an experimental tool. No illegal use allowed. <br>
        <b>Privacy Policy:</b> User data is stored for login purposes only.
        </div>""", unsafe_allow_html=True)
        agree = st.checkbox("I accept the Terms and Privacy Policy")
        
        if st.button("CREATE ACCOUNT"):
            if not is_human: st.error("Please solve the CAPTCHA.")
            elif not agree: st.warning("Please accept the terms.")
            elif len(u_s) < 3 or len(p_s) < 6: st.error("Username/Password too short.")
            else:
                save_user(u_s, p_s)
                st.success("Success! Now go to the LOG IN tab.")
    st.stop()

# --- 4. CHAT ---
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
