import streamlit as st
import pandas as pd
import smtplib, random, time, os, base64, requests
from email.mime.text import MIMEText
from groq import Groq

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="Gobidas AI", layout="wide")

# Client setup - Ensure GROQ_API_KEY is in Streamlit Secrets
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

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
    .main-title {{ font-weight: 900; color: #FF6D00; text-align: center; font-size: 5rem; text-shadow: 0px 0px 25px #FF6D00; margin-bottom: 0px; }}
    .stButton>button {{ width: 100%; border: 2px solid #FF6D00 !important; color: white !important; background: rgba(0,0,0,0.3) !important; font-weight: bold; border-radius: 8px; }}
    .stButton>button:hover {{ background: #FF6D00 !important; color: black !important; }}
    [data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 1px solid #FF6D00; }}
    .legal-box {{ font-size: 0.8rem; color: #888; background: rgba(255,109,0,0.05); padding: 15px; border-radius: 5px; border-left: 3px solid #FF6D00; margin-bottom: 10px; }}
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE & EMAIL HELPERS ---
def load_db():
    try:
        sheet_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
        # This split logic ensures we get a clean CSV download even if the link format varies
        csv_url = sheet_url.split('/edit')[0] + '/export?format=csv'
        df = pd.read_csv(csv_url)
        # Force column names to lowercase and strip whitespace to prevent KeyError
        df.columns = [str(c).strip().lower() for c in df.columns]
        return df
    except Exception as e:
        # Fallback to avoid crashing the login screen
        return pd.DataFrame(columns=["email", "password"])

def send_otp(target_email):
    otp = str(random.randint(111111, 999999))
    sender = "gobidasai@gmail.com"
    pwd = st.secrets["EMAIL_PASSWORD"]
    msg = MIMEText(f"Your Gobidas Verification Code: {otp}")
    msg['Subject'] = "Gobidas Access Code"
    msg['From'] = f"Gobidas AI <{sender}>"
    msg['To'] = target_email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, pwd)
            server.sendmail(sender, target_email, msg.as_string())
        return otp
    except: return None

# --- 3. LOGIN / SIGNUP FLOW ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    if "step" not in st.session_state: st.session_state.step = "input"
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.session_state.step == "input":
            mode = st.radio("GATEWAY", ["LOG IN", "SIGN UP"], horizontal=True)
            u_email = st.text_input("EMAIL").lower().strip()
            u_pass = st.text_input("PASSWORD", type="password")
            
            with st.expander("⚖️ LEGAL ARTICLES & PRIVACY POLICY"):
                st.markdown("<div class='legal-box'><b>Art. 1:</b> Data used for auth only. <b>Art. 2:</b> Experimental AI. <b>Art. 3:</b> Agree to 2025 Safety Rules.</div>", unsafe_allow_html=True)
            agree = st.checkbox("I agree to the Legal Articles")

            if st.button("PROCEED", disabled=not agree):
                db = load_db()
                if mode == "LOG IN":
                    if "email" in db.columns and "password" in db.columns:
                        match = db[(db['email'] == u_email) & (db['password'] == u_pass)]
                        if not match.empty:
                            st.session_state.user = u_email
                            st.rerun()
                        else: st.error("Access Denied. Check credentials.")
                    else: st.error("Database Error: Headers 'email' or 'password' not found.")
                else:
                    if "@" in u_email and len(u_pass) > 5:
                        code = send_otp(u_email)
                        if code:
                            st.session_state.temp = {"e": u_email, "p": u_pass, "c": code}
                            st.session_state.step = "verify"
                            st.rerun()
                        else: st.error("Email failed. Check App Password.")
                    else: st.error("Enter valid email and 6+ char password.")

        elif st.session_state.step == "verify":
            st.warning(f"Verification code sent to {st.session_state.temp['e']}")
            user_code = st.text_input("ENTER 6-DIGIT CODE")
            
            v_col1, v_col2 = st.columns(2)
            with v_col1:
                if st.button("COMPLETE SIGNUP"):
                    if user_code == st.session_state.temp['c']:
                        # REPLACE WITH YOUR ACTUAL DEPLOYED SCRIPT URL
                        SCRIPT_URL = "PASTE_YOUR_APPS_SCRIPT_URL_HERE"
                        params = {"email": st.session_state.temp["e"], "password": st.session_state.temp["p"]}
                        try:
                            requests.get(SCRIPT_URL, params=params)
                            st.session_state.user = st.session_state.temp["e"]
                            st.success("Account Live!")
                            time.sleep(1)
                            st.rerun()
                        except: st.error("Database Write Failed.")
                    else: st.error("Incorrect code.")
            with v_col2:
                if st.button("BACK TO LOGIN"):
                    st.session_state.step = "input"
                    st.rerun()
    st.stop()

# --- 4. CHAT INTERFACE ---
# Initialize session messages with a system prompt to avoid BadRequestError
if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    st.session_state.messages = [{"role": "system", "content": "You are Gobidas AI, a helpful, advanced assistant."}]

# Sidebar setup
with st.sidebar:
    st.title(f"@{st.session_state.user.split('@')[0]}")
    st.divider()
    st.subheader("History & Settings")
    if st.button("🗑️ Clear History"):
        st.session_state.messages = [{"role": "system", "content": "You are Gobidas AI."}]
        st.rerun()
    
    st.file_uploader("🖼️ Attach Image (Coming Soon)", type=['png', 'jpg'])
    st.divider()
    if st.button("🚪 LOGOUT"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

st.markdown("<h1 class='main-title'>Gobidas AI</h1>", unsafe_allow_html=True)

# Display messages (skip system prompt)
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("How can I help?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            # Preparing payload
            payload = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            
            completion = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=payload,
                temperature=0.7
            )
            response_text = completion.choices[0].message.content
            st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
        except Exception as e:
            st.error(f"AI Error: {e}")
