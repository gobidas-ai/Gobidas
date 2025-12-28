import streamlit as st
from groq import Groq
import json, os, base64, io, time
from PIL import Image

# --- 1. UI & TOTAL STEALTH STYLE ---
st.set_page_config(page_title="Gobidas Beta", layout="wide")

def get_base64(file):
    try:
        with open(file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except: return ""

# Initialize Session States correctly to prevent refresh errors
if "creator_info_active" not in st.session_state:
    st.session_state.creator_info_active = False
if "nice_man_active" not in st.session_state:
    st.session_state.nice_man_active = False
if "legal_overlay_active" not in st.session_state:
    st.session_state.legal_overlay_active = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_idx" not in st.session_state:
    st.session_state.active_idx = None

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
        background: linear-gradient(rgba(0,0,0,0.8), rgba(0,0,0,0.95)), 
                    url("data:image/jpeg;base64,{bin_str}");
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    [data-testid="stSidebar"] {{
        background: rgba(0, 0, 0, 0.95) !important;
        backdrop-filter: blur(25px); border-right: 2px solid #FF6D00;
    }}
    .main-title {{
        font-weight: 900; color: #FF6D00; text-align: center; font-size: 5.5rem;
        text-shadow: 0px 0px 25px rgba(255, 109, 0, 0.6); margin-bottom: 10px;
    }}
    .stButton>button {{
        width: 100%; border-radius: 12px; background: transparent !important;
        color: white !important; border: 2px solid #FF6D00 !important;
        font-weight: 600; transition: 0.3s all ease; height: 3em;
    }}
    .stButton>button:hover:not(:disabled) {{
        background: #FF6D00 !important; box-shadow: 0px 0px 30px rgba(255, 109, 0, 0.9);
        color: black !important;
    }}
    .legal-scroll-box {{
        height: 250px; overflow-y: scroll; background: rgba(0,0,0,0.7); 
        padding: 20px; border: 1px solid #FF6D00; color: #ddd; border-radius: 10px;
        margin-bottom: 20px; font-size: 0.85rem; line-height: 1.6;
    }}
    .overlay-container {{
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background-color: black; z-index: 999999;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }}
    .overlay-content {{ max-width: 90%; max-height: 80%; object-fit: contain; }}
    .exit-btn-wrap {{ position: fixed; bottom: 40px; z-index: 1000000; width: 250px; }}
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE & LOGIC ---
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

# Auto-Login Logic (Fixing the Refresh Bug)
if "user" not in st.session_state:
    saved_user = st.session_state.db.get("current_session")
    if saved_user:
        st.session_state.user = saved_user
        # Pre-load the last chat history if it exists
        user_history = st.session_state.db.get("history", {}).get(saved_user, [])
        if user_history:
            st.session_state.messages = user_history[-1].get("msgs", [])
            st.session_state.active_idx = len(user_history) - 1

# --- 3. OVERLAYS ---
LEGAL_TEXT = "<b>GOBIDAS PROTOCOL</b><br>Data is local. Privacy is absolute. AI is experimental."

def render_exit_button(state_key):
    _, col, _ = st.columns([1, 0.6, 1])
    with col:
        if st.button("RETURN TO COMMAND", key=f"exit_{state_key}"):
            st.session_state[state_key] = False
            st.rerun()

if st.session_state.creator_info_active:
    st.markdown(f'<div class="overlay-container"><img src="data:image/png;base64,{sec_img_base64}" class="overlay-content"></div>', unsafe_allow_html=True)
    render_exit_button("creator_info_active"); st.stop()

if st.session_state.nice_man_active:
    st.markdown(f'<div class="overlay-container"><video class="overlay-content" autoplay loop><source src="data:video/mp4;base64,{video_base64}" type="video/mp4"></video></div>', unsafe_allow_html=True)
    render_exit_button("nice_man_active"); st.stop()

if st.session_state.legal_overlay_active:
    st.markdown(f'<div class="overlay-container"><div class="legal-scroll-box" style="width:70%">{LEGAL_TEXT}</div></div>', unsafe_allow_html=True)
    render_exit_button("legal_overlay_active"); st.stop()

# --- 4. AUTH SCREEN ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.8, 1])
    with col:
        mode = st.radio("Access", ["Log In", "Sign Up"], horizontal=True)
        u = st.text_input("User", placeholder="Identify...")
        p = st.text_input("Key", type="password", placeholder="Secret Key...")
        remember = st.checkbox("Keep me logged in")
        if st.button("INITIALIZE"):
            db = st.session_state.db
            if mode == "Log In":
                if u in db["users"] and db["users"][u] == p:
                    st.session_state.user = u
                    if remember:
                        db["current_session"] = u
                        save_db(db)
                    st.rerun()
                else: st.error("Access Denied.")
            else:
                if u and p:
                    db["users"][u] = p
                    db["history"][u] = []
                    save_db(db)
                    st.success("Authorized.")
    st.stop()

# --- 5. MAIN CHAT ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.markdown(f"### Access: **{st.session_state.user}**")
    if st.button("New Command"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    st.divider()
    with st.expander("⚙️ System Config"):
        if st.button("CREATOR INFO"): st.session_state.creator_info_active = True; st.rerun()
        if st.button("VERY NICE MAN"): st.session_state.nice_man_active = True; st.rerun()
        if st.button("LOG OUT"):
            st.session_state.db["current_session"] = None
            save_db(st.session_state.db)
            del st.session_state.user
            st.rerun()
    img_file = st.file_uploader("Visual Scan", type=['png', 'jpg', 'jpeg'])

st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)

# Render history safely
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Command Gobidas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            res = client.chat.completions.create(
                model="meta-llama/llama-4-maverick-17b-128e-instruct",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            )
            ans = res.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            # Auto-save history
            hist = st.session_state.db["history"].get(st.session_state.user, [])
            chat_data = {"name": prompt[:20], "msgs": st.session_state.messages, "timestamp": time.time()}
            if st.session_state.active_idx is None:
                hist.append(chat_data)
                st.session_state.active_idx = len(hist) - 1
            else:
                hist[st.session_state.active_idx] = chat_data
            st.session_state.db["history"][st.session_state.user] = hist
            save_db(st.session_state.db)
        except Exception as e:
            st.error(f"Inference Failure: {e}")
