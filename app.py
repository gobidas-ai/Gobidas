import streamlit as st
import os, json, base64
from groq import Groq

# --- 1. CONFIG ---
st.set_page_config(page_title="Gobidas AI", layout="wide")

# Updated to Llama 3.1 8B Instant (Not decommissioned)
MODEL_NAME = "llama-3.1-8b-instant"

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("API Key Error: Check your Streamlit Secrets.")

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
    [data-testid="stHeader"] {{ background: transparent !important; }}
    .stApp {{ 
        background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.85)), url("data:image/jpeg;base64,{bin_str}"); 
        background-size: cover; 
    }}
    .main-title {{ font-weight: 900; color: #FF6D00; text-align: center; font-size: 5rem; text-shadow: 0px 0px 25px #FF6D00; }}
    .stButton>button {{ width: 100%; border: 2px solid #FF6D00 !important; color: white !important; background: rgba(0,0,0,0.2) !important; font-weight: bold; border-radius: 8px; }}
    [data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 1px solid #FF6D00; }}
    .legal-scroll {{ font-size: 0.85rem; color: #ccc; background: rgba(255,109,0,0.1); padding: 15px; border-radius: 10px; border: 1px solid #FF6D00; height: 300px; overflow-y: scroll; line-height: 1.5; }}
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
                st.session_state.messages = [{"role": "system", "content": "You are Gobidas AI."}]
                st.rerun()
            else: st.error("Invalid credentials.")

    with t2:
        u_s = st.text_input("New Username", key="s_u")
        p_s = st.text_input("New Password", type="password", key="s_p")
        
        st.markdown("### Official Terms of Service & Privacy Policy")
        st.markdown("""<div class='legal-scroll'>
        <b>1. ACCEPTANCE OF TERMS</b><br>
        By creating an account, you agree to be bound by these Terms. If you do not agree, you may not use the service.<br><br>
        <b>2. DESCRIPTION OF SERVICE</b><br>
        Gobidas AI is an artificial intelligence interface. Users may interact with the AI for creative and educational purposes.<br><br>
        <b>3. USER CONDUCT</b><br>
        You agree not to use Gobidas AI for:
        - Generating illegal or harmful content.
        - Impersonating others.
        - Attempting to bypass system safety filters.<br><br>
        <b>4. PRIVACY POLICY</b><br>
        - <b>Data Collection:</b> We store your username and password for authentication.
        - <b>Chat Logs:</b> Chat history is saved locally in your current session to provide context.
        - <b>Third Parties:</b> We do not sell your personal data. AI processing is handled by Groq Cloud.<br><br>
        <b>5. NO WARRANTY</b><br>
        The service is provided "as is." We do not guarantee the accuracy of AI-generated responses.
        </div>""", unsafe_allow_html=True)
        agree = st.checkbox("I agree to the Terms and Privacy Policy.")
        
        if st.button("REGISTER"):
            if not agree: st.warning("You must accept the legal terms.")
            elif len(u_s) < 3 or len(p_s) < 6: st.error("Username (3+) or Password (6+) too short.")
            else:
                save_user(u_s, p_s)
                st.success("Account created! Use the LOG IN tab.")
    st.stop()

# --- 4. CHAT INTERFACE & SIDEBAR ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "You are Gobidas AI."}]

with st.sidebar:
    st.title(f"@{st.session_state.user}")
    st.divider()
    st.subheader("Chat Management")
    
    if st.button("🗑️ Clear History"):
        st.session_state.messages = [{"role": "system", "content": "You are Gobidas AI."}]
        st.rerun()

    uploaded_file = st.file_uploader("🖼️ Attach Image", type=['png', 'jpg', 'jpeg'])
    if uploaded_file:
        st.image(uploaded_file, caption="User Upload")
    
    st.divider()
    if st.button("🚪 LOGOUT"):
        del st.session_state.user
        st.rerun()

st.markdown("<h1 class='main-title'>Gobidas AI</h1>", unsafe_allow_html=True)

# History logic
for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]): st.markdown(m["content"])

# Chat Input & AI logic
if prompt := st.chat_input("How can I help you today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Using the new llama-3.1-8b-instant model
            resp = client.chat.completions.create(
                model=MODEL_NAME, 
                messages=st.session_state.messages
            )
            full_ans = resp.choices[0].message.content
            st.markdown(full_ans)
            st.session_state.messages.append({"role": "assistant", "content": full_ans})
        except Exception as e:
            st.error(f"AI System Error: {e}")
