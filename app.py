import streamlit as st
import pandas as pd
import smtplib, random, time, os, base64, requests
from email.mime.text import MIMEText
from groq import Groq

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="Gobidas AI", layout="wide")

# Client setup
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
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.8)), url("data:image/jpeg;base64,{bin_str}"); 
        background-size: cover; 
    }}
    .main-title {{ font-weight: 900; color: #FF6D00; text-align: center; font-size: 5rem; text-shadow: 0px 0px 25px #FF6D00; }}
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
        csv_url = sheet_url.replace("/edit?usp=sharing", "/export?format=csv")
        df = pd.read_csv(csv_url)
        # Clean column names to prevent KeyError
        df.columns = df.columns.str.strip().str.lower()
        return df
    except:
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
                st.markdown("""
                <div class='legal-box'>
                <b>Article 1: Data Usage</b><br>Email used for auth only.<br><br>
                <b>Article 2: AI Conduct</b><br>Experimental AI. Do not share secrets.<br><br>
                <b>Article 3: User Agreement</b><br>Agree to 2025 AI Safety guidelines.
                </div>
                """, unsafe_allow_html=True)
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
                    else: st.error("Database Error: Headers not found.")
                else:
                    if "@" in u_email and len(u_pass) > 5:
                        code = send_otp(u_email)
                        if code:
                            st.session_state.temp = {"e": u_email, "p": u_pass, "c": code}
                            st.session_state.step = "verify"
                            st.rerun()
                    else: st.error("Enter valid email and 6+ char password.")

        elif st.session_state.step == "verify":
            st.warning(f"Verification code sent to {st.session_state.temp['e']}")
            user_code = st.text_input("ENTER 6-DIGIT CODE")
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("COMPLETE REGISTRATION"):
                    if user_code == st.session_state.temp['c']:
                        # PASTE YOUR WEB APP URL BELOW
                        SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwhux-1szSANvsASiyjx5qZHluO3MZnF1uOjnif_lkqDvNtGCfYjilOXcQMnP3zCd1VHA/exec"
                        params = {"email": st.session_state.temp["e"], "password": st.session_state.temp["p"]}
                        try:
                            requests.get(SCRIPT_URL, params=params)
                            st.session_state.user = st.session_state.temp["e"]
                            st.success("Account Created!")
                            time.sleep(1)
                            st.rerun()
                        except: st.error("Connection error.")
                    else: st.error("Incorrect code.")
            
            with col_b:
                if st.button("BACK TO LOGIN"):
                    st.session_state.step = "input"
                    st.rerun()
    st.stop()

# --- 4. CHAT INTERFACE ---
st.sidebar.title(f"@{st.session_state.user.split('@')[0]}")
if st.sidebar.button("LOGOUT"):
    del st.session_state.user
    st.rerun()

st.markdown("<h1 class='main-title'>Gobidas AI</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("How can I help?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        resp = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        )
        full_resp = resp.choices[0].message.content
        st.markdown(full_resp)
    st.session_state.messages.append({"role": "assistant", "content": full_resp})
