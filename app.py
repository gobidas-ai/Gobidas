import streamlit as st
from groq import Groq
import json, os, base64, io, time
from PIL import Image

# --- 1. UI & STYLE ---
st.set_page_config(page_title="Gobidas Beta", layout="wide")

def get_base64(file):
    try:
        with open(file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except: return ""

# Initialize Session States
if "creator_info_active" not in st.session_state: st.session_state.creator_info_active = False
if "nice_man_active" not in st.session_state: st.session_state.nice_man_active = False
if "legal_overlay_active" not in st.session_state: st.session_state.legal_overlay_active = False
if "messages" not in st.session_state: st.session_state.messages = []

bin_str = get_base64('background.jpg')
sec_img_base64 = get_base64('secret_image.png')
sec_audio_base64 = get_base64('secret_music.mp3')

try:
    with open("ssstik.io_@hicc319_1766964298508.mp4", "rb") as v_file:
        video_bytes = v_file.read()
    video_base64 = base64.b64encode(video_bytes).decode()
except:
    video_base64 = ""

st.markdown(f"""
<style>
    header, [data-testid="stHeader"], .stDeployButton, [data-testid="stToolbar"], 
    footer, [data-testid="stStatusWidget"], [data-testid="stManageAppButton"] {{
        visibility: hidden !important; display: none !important;
    }}
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.85), rgba(0,0,0,0.95)), 
                    url("data:image/jpeg;base64,{bin_str}");
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    [data-testid="stSidebar"] {{
        background: rgba(0, 0, 0, 0.95) !important;
        border-right: 2px solid #FF6D00;
    }}
    .main-title {{
        font-weight: 900; color: #FF6D00; text-align: center; font-size: 5.5rem;
        text-shadow: 0px 0px 25px rgba(255, 109, 0, 0.6); margin-bottom: 10px;
    }}
    .stButton>button {{
        width: 100%; border-radius: 12px; background: transparent !important;
        color: white !important; border: 2px solid #FF6D00 !important;
        font-weight: 600; height: 3.5em;
    }}
    .stButton>button:hover {{
        background: #FF6D00 !important; color: black !important;
    }}
    .legal-box {{
        height: 400px; overflow-y: scroll; background: rgba(20,20,20,0.8); 
        padding: 25px; border: 1px solid #FF6D00; color: #bbb; border-radius: 10px;
        margin-bottom: 20px; font-size: 0.8rem; line-height: 1.8;
    }}
    .overlay-container {{
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background-color: black; z-index: 999999;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }}
</style>
""", unsafe_allow_html=True)

# --- 2. THE LONG TERMS & PRIVACY ---
LONG_LEGAL = """
<b>GOBIDAS BETA - COMPREHENSIVE TERMS OF SERVICE & PRIVACY POLICY</b><br><br>
<b>1. ACCEPTANCE OF TERMS</b><br>
By accessing the Gobidas Neural Interface, you agree to be bound by these Terms of Service. If you do not agree, disconnect immediately. This is an experimental platform provided "as is" without any warranties of any kind.<br><br>
<b>2. USER CONDUCT</b><br>
Users are prohibited from using Gobidas for any illegal activities. You are responsible for all commands issued under your identification. Do not share your Secret Key with anyone.<br><br>
<b>3. PRIVACY & DATA STORAGE</b><br>
Gobidas operates on a "Zero-Knowledge" principle. We do not track your location, your hardware ID, or your personal identity. All chat logs are stored in a local JSON file on the host server. Deleting a chat history entry removes it from the database permanently. We do not sell data to third parties.<br><br>
<b>4. NEURAL ENGINES</b><br>
This application uses Groq's high-speed inference technology and Meta's Llama 4 models. Use of these models is subject to Meta's Open-Source AI License. Gobidas is a custom wrapper designed for speed and stealth.<br><br>
<b>5. INTELLECTUAL PROPERTY</b><br>
The Gobidas UI, custom CSS animations, and database architecture are proprietary. Unauthorized cloning of the Gobidas source code is prohibited.<br><br>
<b>6. LIMITATION OF LIABILITY</b><br>
In no event shall the creators of Gobidas be liable for any direct, indirect, incidental, or consequential damages arising out of the use or inability to use this service. The AI may generate inaccurate or biased information.<br><br>
<b>7. AMENDMENTS</b><br>
We reserve the right to modify these terms at any time. Your continued use of the system constitutes acceptance of new terms.<br><br>
<b>8. COOKIES & PERSISTENCE</b><br>
If you select "Remember Me", your identification is stored in a session variable to prevent the need for re-authentication on every refresh. Log out to clear this data.
"""

# --- 3. DATABASE & AUTH ---
DB_FILE = "gobidas_db.json"
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: pass
    return {"users": {}, "history": {}, "current_session": None}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

if "db" not in st.session_state:
    st.session_state.db = load_db()

# Persistent Login Check
if "user" not in st.session_state:
    saved = st.session_state.db.get("current_session")
    if saved:
        st.session_state.user = saved
        user_hist = st.session_state.db.get("history", {}).get(saved, [])
        if user_hist: st.session_state.messages = user_hist[-1].get("msgs", [])

# Overlays
def render_exit(key):
    if st.button("GO BACK"):
        st.session_state[key] = False
        st.rerun()

if st.session_state.creator_info_active:
    st.markdown(f'<div class="overlay-container"><img src="data:image/png;base64,{sec_img_base64}" style="max-height:80%"></div>', unsafe_allow_html=True)
    render_exit("creator_info_active"); st.stop()

if st.session_state.nice_man_active:
    st.markdown(f'<div class="overlay-container"><video style="max-height:80%" autoplay loop><source src="data:video/mp4;base64,{video_base64}" type="video/mp4"></video></div>', unsafe_allow_html=True)
    render_exit("nice_man_active"); st.stop()

if st.session_state.legal_overlay_active:
    st.markdown(f'<div class="overlay-container"><div class="legal-box" style="width:70%">{LONG_LEGAL}</div></div>', unsafe_allow_html=True)
    render_exit("legal_overlay_active"); st.stop()

# Login Screen
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        mode = st.radio("Choose", ["Log In", "Sign Up"], horizontal=True, label_visibility="collapsed")
        u = st.text_input("Type your Username", placeholder="Username")
        p = st.text_input("Type your Password", type="password", placeholder="Password")
        st.markdown(f'<div class="legal-box">{LONG_LEGAL}</div>', unsafe_allow_html=True)
        remember = st.checkbox("Keep me logged in")
        agree = st.checkbox("I have read and agree to the Terms and Privacy")
        
        btn_text = "CONTINUE" if mode == "Log In" else "SIGN UP"
        if st.button(btn_text, disabled=not agree):
            db = st.session_state.db
            if mode == "Log In":
                if u in db["users"] and db["users"][u] == p:
                    st.session_state.user = u
                    if remember:
                        db["current_session"] = u
                        save_db(db)
                    st.rerun()
                else: st.error("Incorrect details.")
            else:
                if u and p:
                    db["users"][u] = p
                    db["history"][u] = []
                    save_db(db)
                    st.success("Account created! Now Log In.")
    st.stop()

# --- 4. MAIN CHAT ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.markdown(f"### Logged in as: **{st.session_state.user}**")
    if st.button("Start New Chat"):
        st.session_state.messages = []
        st.rerun()
    st.divider()
    with st.expander("Settings"):
        if st.button("CREATOR INFO"): st.session_state.creator_info_active = True; st.rerun()
        if st.button("VERY NICE MAN"): st.session_state.nice_man_active = True; st.rerun()
        if st.button("TERMS AND PRIVACY"): st.session_state.legal_overlay_active = True; st.rerun()
        if st.button("LOG OUT"):
            st.session_state.db["current_session"] = None
            save_db(st.session_state.db)
            del st.session_state.user
            st.rerun()

st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Type a message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            res = client.chat.completions.create(
                model="meta-llama/llama-4-maverick-17b-128e-instruct",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            )
            ans = res.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            # Save history
            hist = st.session_state.db["history"].get(st.session_state.user, [])
            hist.append({"name": prompt[:20], "msgs": st.session_state.messages})
            st.session_state.db["history"][st.session_state.user] = hist
            save_db(st.session_state.db)
        except Exception as e:
            st.error(f"Error: {e}")
