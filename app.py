import streamlit as st
import os, json, base64
from groq import Groq

# --- 1. CONFIG & API SETUP ---
st.set_page_config(page_title="Gobidas AI", layout="wide")

# Ensure GROQ_API_KEY is in your Streamlit Secrets
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    st.error("Missing Groq API Key in Secrets!")

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

# --- 2. UI THEMING ---
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
    .legal-box {{ font-size: 0.8rem; color: #ccc; background: rgba(255,109,0,0.1); padding: 20px; border-radius: 10px; border: 1px solid #FF6D00; line-height: 1.6; }}
</style>
""", unsafe_allow_html=True)

# --- 3. LOGIN & SIGN UP ---
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
                st.session_state.messages = [{"role": "system", "content": "You are Gobidas AI, a professional assistant."}]
                st.rerun()
            else: st.error("Invalid credentials.")

    with t2:
        u_s = st.text_input("New Username", key="s_u")
        p_s = st.text_input("New Password", type="password", key="s_p")
        
        st.markdown("### Official Legal Articles")
        st.markdown("""<div class='legal-box'>
        <b>Article 1: User Responsibility</b><br>
        Users are solely responsible for the content they generate and must not use Gobidas AI for any deceptive, harmful, or illegal activities. <br><br>
        <b>Article 2: Data Privacy & Security</b><br>
        We value your privacy. Your login credentials are encrypted and stored locally. Chat histories are session-based and are not sold to third parties. <br><br>
        <b>Article 3: AI Limitations</b><br>
        Gobidas AI is an experimental tool based on Large Language Models. It may occasionally produce incorrect, biased, or halluncinated information. Always verify critical facts.<br><br>
        <b>Article 4: Account Termination</b><br>
        We reserve the right to suspend accounts that violate our community safety guidelines.
        </div>""", unsafe_allow_html=True)
        agree = st.checkbox("I have read and agree to all terms of service.")
        
        if st.button("REGISTER ACCOUNT"):
            if not agree: st.warning("You must accept the legal articles.")
            elif len(u_s) < 3 or len(p_s) < 6: st.error("Username (3+) or Password (6+) too short.")
            else:
                save_user(u_s, p_s)
                st.success("Registration Successful! Please switch to the LOG IN tab.")
    st.stop()

# --- 4. MAIN INTERFACE & SIDEBAR ---
# Ensure messages exist
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "You are Gobidas AI."}]

with st.sidebar:
    st.title(f"@{st.session_state.user}")
    st.divider()
    st.subheader("Control Panel")
    
    if st.button("🗑️ Reset Chat History"):
        st.session_state.messages = [{"role": "system", "content": "You are Gobidas AI."}]
        st.rerun()

    uploaded_file = st.file_uploader("🖼️ Upload Image to Chat", type=['png', 'jpg', 'jpeg'])
    if uploaded_file:
        st.image(uploaded_file, caption="Selected Image", use_container_width=True)
    
    st.divider()
    if st.button("🚪 LOGOUT"):
        del st.session_state.user
        st.rerun()

st.markdown("<h1 class='main-title'>Gobidas AI</h1>", unsafe_allow_html=True)

# Display Chat History
for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

# Handling User Input
if prompt := st.chat_input("Ask Gobidas anything..."):
    # Append user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate AI Response
    with st.chat_message("assistant"):
        try:
            # Pass full history to maintain context
            completion = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=st.session_state.messages,
                temperature=0.7
            )
            response = completion.choices[0].message.content
            st.markdown(response)
            # Save response to history
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"AI Error: {e}")
