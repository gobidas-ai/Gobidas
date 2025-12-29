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

# --- 2. INITIALIZE SESSION STATES (SAFETY FIRST) ---
# This prevents the AttributeError you saw
if "user" not in st.session_state: st.session_state.user = None
if "creator_info_active" not in st.session_state: st.session_state.creator_info_active = False
if "nice_man_active" not in st.session_state: st.session_state.nice_man_active = False
if "legal_overlay_active" not in st.session_state: st.session_state.legal_overlay_active = False
if "messages" not in st.session_state: st.session_state.messages = []
if "show_welcome" not in st.session_state: st.session_state.show_welcome = True

bin_str = get_base64('background.jpg')
sec_img_base64 = get_base64('secret_image.png')

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
        height: 400px; overflow-y: scroll; background: rgba(10,10,10,0.9); 
        padding: 30px; border: 1px solid #FF6D00; color: #ccc; border-radius: 10px;
        margin-bottom: 20px; font-size: 0.85rem; line-height: 2;
    }}
    .overlay-container {{
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background-color: black; z-index: 999999;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        text-align: center; color: white; padding: 50px;
    }}
</style>
""", unsafe_allow_html=True)

# --- 3. DATABASE ---
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

# Auto-Login Check
if st.session_state.user is None:
    saved = st.session_state.db.get("current_session")
    if saved:
        st.session_state.user = saved
        hist_list = st.session_state.db.get("history", {}).get(saved, [])
        if hist_list: st.session_state.messages = hist_list[-1].get("msgs", [])

# --- 4. LEGAL TEXT ---
LONG_LEGAL = """
<b>GOBIDAS BETA - OFFICIAL TERMS & PRIVACY PROTOCOL</b><br><br>
<b>1. RULES:</b> Use at your own risk. This is a beta test. Data loss is possible.<br>
<b>2. PRIVACY:</b> We don't track you. Everything is in a local JSON file.<br>
<b>3. AI:</b> Powered by Groq/Llama. Not responsible for AI responses.<br>
<b>4. SECURITY:</b> Keep your password safe. We don't store plain text.<br>
<b>5. ATTACHMENTS:</b> Images are processed but not stored forever.
"""

# --- 5. OVERLAYS (WELCOME, SECRETS, LEGAL) ---
if st.session_state.user and st.session_state.show_welcome:
    st.markdown(f"""
    <div class="overlay-container">
        <h1 style="color:#FF6D00;">WELCOME BACK</h1>
        <p style="font-size:1.5rem;">Thank you for using Gobidas. <br>
        Currently our AI is in beta and you might experience loss of data (losing your user). <br>
        Thank you for trying it out! we are ready for you to use it again!</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("CONTINUE TO CHAT"):
        st.session_state.show_welcome = False
        st.rerun()
    st.stop()

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
    st.markdown(f'<div class="overlay-container"><div class="legal-box" style="width:75%">{LONG_LEGAL}</div></div>', unsafe_allow_html=True)
    render_exit("legal_overlay_active"); st.stop()

# --- 6. LOGIN / SIGN UP ---
if st.session_state.user is None:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 2, 1])
    with col:
        mode = st.radio("Choice", ["Log In", "Sign Up"], horizontal=True, label_visibility="collapsed")
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
                    st.session_state.show_welcome = True
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

# --- 7. SIDEBAR ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.markdown(f"### Logged in: **{st.session_state.user}**")
    img_file = st.file_uploader("📎 ATTACH IMAGE", type=['png', 'jpg', 'jpeg'])
    
    if st.button("Start New Chat"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    
    st.divider()
    st.markdown("### 📄 HISTORY")
    user_logs = st.session_state.db["history"].get(st.session_state.user, [])
    for i, log in enumerate(reversed(user_logs)):
        if st.button(f"Chat: {log.get('name', 'Log')[:15]}", key=f"hist_{i}"):
            st.session_state.messages = log.get("msgs", [])
            st.session_state.active_idx = len(user_logs) - 1 - i
            st.rerun()

    st.divider()
    with st.expander("Settings"):
        if st.button("CREATOR INFO"): st.session_state.creator_info_active = True; st.rerun()
        if st.button("VERY NICE MAN"): st.session_state.nice_man_active = True; st.rerun()
        if st.button("TERMS AND PRIVACY"): st.session_state.legal_overlay_active = True; st.rerun()
        if st.button("LOG OUT"):
            st.session_state.db["current_session"] = None
            save_db(st.session_state.db)
            st.session_state.user = None
            st.rerun()

# --- 8. MAIN CHAT ---
st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Type a message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_file: st.image(img_file, width=200)

    with st.chat_message("assistant"):
        try:
            if img_file:
                img = Image.open(img_file).convert("RGB")
                img.thumbnail((800, 800))
                buf = io.BytesIO()
                img.save(buf, format="JPEG")
                b64 = base64.b64encode(buf.getvalue()).decode()
                res = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}]
                )
            else:
                res = client.chat.completions.create(
                    model="meta-llama/llama-4-maverick-17b-128e-instruct",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                )
            
            ans = res.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            # Save logic
            hist = st.session_state.db["history"].get(st.session_state.user, [])
            chat_save = {"name": prompt[:20], "msgs": st.session_state.messages}
            if st.session_state.get("active_idx") is None:
                hist.append(chat_save)
                st.session_state.active_idx = len(hist) - 1
            else:
                hist[st.session_state.active_idx] = chat_save
            st.session_state.db["history"][st.session_state.user] = hist
            save_db(st.session_state.db)
        except Exception as e:
            st.error(f"Inference Failure: {e}")
