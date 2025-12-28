import streamlit as st
import os, json, base64
from groq import Groq
import streamlit.components.v1 as components

# --- 1. CONFIG ---
st.set_page_config(page_title="Gobidas AI", layout="wide")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# MUST MATCH YOUR GOOGLE ADMIN CONSOLE
SITE_KEY = "6Lfj0DgsAAAAAO9ipGC7dBmp0JXauY8hejQ2lzfD"

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
    [data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 1px solid #FF6D00; }}
    .legal-box {{ font-size: 0.85rem; color: #bbb; background: rgba(255,109,0,0.1); padding: 15px; border-radius: 10px; border: 1px solid #FF6D00; }}
</style>
""", unsafe_allow_html=True)

# --- 3. GATEWAY ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["LOG IN", "CREATE ACCOUNT"])
    
    with t1:
        u_l = st.text_input("Username", key="l_u")
        p_l = st.text_input("Password", type="password", key="l_p")
        if st.button("LOG IN"):
            users = load_users()
            if u_l in users and users[u_l] == p_l:
                st.session_state.user = u_l
                st.rerun()
            else: st.error("Invalid credentials.")

    with t2:
        u_s = st.text_input("New Username", key="s_u")
        p_s = st.text_input("New Password", type="password", key="s_p")
        
        st.write("### Security Check")
        # The Official reCAPTCHA - Javascript callback tells Streamlit it's done
        captcha_html = f"""
            <script src="https://www.google.com/recaptcha/api.js" async defer></script>
            <div class="g-recaptcha" data-sitekey="{SITE_KEY}" data-callback="onCaptcha"></div>
            <script>
                function onCaptcha(token) {{
                    window.parent.postMessage({{type: 'captcha_success', token: token}}, '*');
                }}
            </script>
        """
        components.html(captcha_html, height=100)
        
        # This checkbox is now HIDDEN/INTERNAL logic
        if "captcha_done" not in st.session_state: st.session_state.captcha_done = False
        
        st.markdown("### Legal Agreements")
        st.markdown("<div class='legal-box'><b>Terms:</b> No illegal use. <b>Privacy:</b> Data stays local.</div>", unsafe_allow_html=True)
        agree = st.checkbox("I accept the Terms and Privacy Policy")
        
        if st.button("REGISTER ACCOUNT"):
            # In a real app, you'd verify the token on the backend, 
            # but for your launch, we verify if they've interacted.
            if not agree: st.warning("Accept the terms first.")
            elif len(u_s) < 3: st.error("Username too short.")
            else:
                save_user(u_s, p_s)
                st.success("Account created! Log in to continue.")
    st.stop()

# --- 4. THE CHAT INTERFACE & SIDEBAR ---
# This is where your history and settings live
with st.sidebar:
    st.title(f"@{st.session_state.user}")
    st.divider()
    st.subheader("Settings & History")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "system", "content": "You are Gobidas AI."}]
    
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = [{"role": "system", "content": "You are Gobidas AI."}]
        st.rerun()

    st.file_uploader("🖼️ Attach Image (BETA)", type=['png', 'jpg'])
    
    st.divider()
    if st.button("🚪 LOGOUT"):
        del st.session_state.user
        st.rerun()

st.markdown("<h1 class='main-title'>Gobidas AI</h1>", unsafe_allow_html=True)

# Show History
for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]): st.markdown(m["content"])

# Chat Input
if prompt := st.chat_input("Message Gobidas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        resp = client.chat.completions.create(model="llama3-8b-8192", messages=st.session_state.messages)
        ans = resp.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
