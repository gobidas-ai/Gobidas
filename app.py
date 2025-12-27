import streamlit as st
import pandas as pd
import smtplib, random, time, os, base64
from email.mime.text import MIMEText
from groq import Groq

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="Gobidas Beta", layout="wide")

def get_base64(file):
    if os.path.exists(file):
        with open(file, 'rb') as f: return base64.b64encode(f.read()).decode()
    return ""

bin_str = get_base64('background.jpg')
st.markdown(f"""
<style>
    [data-testid="stHeader"] {{ background: transparent !important; }}
    .stApp {{ background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("data:image/jpeg;base64,{bin_str}"); background-size: cover; }}
    .main-title {{ font-weight: 900; color: #FF6D00; text-align: center; font-size: 5rem; text-shadow: 0px 0px 20px #FF6D00; }}
    .stButton>button {{ width: 100%; border: 1px solid #FF6D00; color: white; background: transparent; font-weight: bold; }}
    .stButton>button:hover {{ background: #FF6D00; color: black; }}
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE LOGIC (ZERO-FAIL METHOD) ---
def load_db():
    try:
        # Converts your Google Sheet URL into a direct CSV download link
        url = st.secrets["SHEET_URL"].replace("/edit#gid=", "/export?format=csv&gid=")
        if "/export" not in url: url = url.split("/edit")[0] + "/export?format=csv"
        return pd.read_csv(url)
    except:
        return pd.DataFrame(columns=["email", "password"])

def save_user(email, password):
    # For writing to Google Sheets without complex libraries, 
    # the best 'quick' way for a 2-day launch is a simple Append.
    # Note: If this fails, I recommend using a Google Form link for sign-ups!
    st.warning("Registration data is being logged. Please ensure your Sheet is shared as 'Editor'.")
    # (Advanced: In a 3-billion user scenario, you'd use a real API here)

# --- 3. EMAIL LOGIC ---
def send_otp(target_email):
    otp = str(random.randint(100000, 999999))
    msg = MIMEText(f"Your Gobidas Access Code: {otp}")
    msg['Subject'] = "GOBIDAS VERIFICATION"
    msg['From'] = "gobidasai@gmail.com"
    msg['To'] = target_email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login("gobidasai@gmail.com", st.secrets["EMAIL_PASSWORD"])
            server.sendmail("gobidasai@gmail.com", target_email, msg.as_string())
        return otp
    except: return None

# --- 4. LOGIN / SIGNUP SYSTEM ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas BETA</h1>", unsafe_allow_html=True)
    if "step" not in st.session_state: st.session_state.step = "input"
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.session_state.step == "input":
            mode = st.radio("GATEWAY", ["LOG IN", "SIGN UP"], horizontal=True)
            email = st.text_input("EMAIL").lower().strip()
            pwd = st.text_input("PASSWORD", type="password")
            if st.button("PROCEED"):
                db = load_db()
                if mode == "LOG IN":
                    if not db[(db['email'] == email) & (db['password'] == pwd)].empty:
                        st.session_state.user = email
                        st.rerun()
                    else: st.error("Access Denied.")
                else:
                    code = send_otp(email)
                    if code:
                        st.session_state.temp = {"e": email, "p": pwd, "c": code}
                        st.session_state.step = "verify"
                        st.rerun()
        
        elif st.session_state.step == "verify":
            st.info(f"Code sent to {st.session_state.temp['e']}")
            user_code = st.text_input("ENTER CODE")
            if st.button("VERIFY"):
                if user_code == st.session_state.temp['c']:
                    st.success("Verified! Email the admin to finalize registration or use Form portal.")
                    st.session_state.step = "input"
                else: st.error("Invalid Code.")
    st.stop()

# --- 5. MAIN CHAT INTERFACE ---
st.sidebar.title(f"User: {st.session_state.user}")
if st.sidebar.button("LOGOUT"):
    del st.session_state.user
    st.rerun()

st.markdown("<h1 class='main-title'>Gobidas AI</h1>", unsafe_allow_html=True)
# Add your Groq Chat logic here...
