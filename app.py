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

# Session state for secret overlays
if "creator_info_active" not in st.session_state:
    st.session_state.creator_info_active = False
if "nice_man_active" not in st.session_state:
    st.session_state.nice_man_active = False
if "legal_overlay_active" not in st.session_state:
    st.session_state.legal_overlay_active = False

bin_str = get_base64('background.jpg')
sec_img_base64 = get_base64('secret_image.png')
sec_audio_base64 = get_base64('secret_music.mp3')

# Loading the specific video file
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
        height: 300px; overflow-y: scroll; background: rgba(0,0,0,0.7); 
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

# --- 2. LEGAL CONTENT DEFINITION ---
LEGAL_TEXT = """
<b>GOBIDAS BETA - TERMS & PRIVACY PROTOCOL</b><br><br>
1. <b>Data Sovereignty:</b> All user logs and chat histories are stored in a local JSON architecture. No data is sold or transmitted to third-party advertisers.<br><br>
2. <b>Neural Network Usage:</b> This interface utilizes Llama 4 Scout and Maverick engines via the Groq API. Users must comply with Meta's Acceptable Use Policy.<br><br>
3. <b>Content Responsibility:</b> The creator of Gobidas is not liable for AI-generated outputs. Use at your own risk.<br><br>
4. <b>Experimental Features:</b> Some modules (Visual Analysis) are in Alpha. Expect occasional inference delays.<br><br>
5. <b>Privacy:</b> We do not track IP addresses or location data. Your session remains isolated to this browser instance.<br><br>
6. <b>Zero Persistence:</b> Deleting a chat log removes it permanently from the local database.
"""

# --- 3. OVERLAY LOGIC ---
def render_exit_button(state_key):
    _, col, _ = st.columns([1, 0.6, 1])
    with col:
        st.markdown('<div class="exit-btn-wrap">', unsafe_allow_html=True)
        if st.button("RETURN TO COMMAND"):
            st.session_state[state_key] = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.creator_info_active:
    st.markdown(f'<div class="overlay-container"><img src="data:image/png;base64,{sec_img_base64}" class="overlay-content"><audio autoplay loop><source src="data:audio/mp3;base64,{sec_audio_base64}" type="audio/mp3"></audio></div>', unsafe_allow_html=True)
    render_exit_button("creator_info_active")
    st.stop()

if st.session_state.nice_man_active:
    st.markdown(f'<div class="overlay-container"><video class="overlay-content" autoplay loop><source src="data:video/mp4;base64,{video_base64}" type="video/mp4"></video></div>', unsafe_allow_html=True)
    render_exit_button("nice_man_active")
    st.stop()

if st.session_state.legal_overlay_active:
    st.markdown(f'<div class="overlay-container"><div style="width: 70%;" class="legal-scroll-box">{LEGAL_TEXT}</div></div>', unsafe_allow_html=True)
    render_exit_button("legal_overlay_active")
    st.stop()

# --- 4. DATABASE & LOGIN ---
DB_FILE = "gobidas_db.json"
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: pass
    return {"users": {}, "history": {}}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

if "db" not in st.session_state:
    st.session_state.db = load_db()

if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.8, 1])
    with col:
        mode = st.radio("Access", ["Log In", "Sign Up"], horizontal=True)
        u = st.text_input("User", placeholder="Identify...")
        p = st.text_input("Key", type="password", placeholder="Secret Key...")
        st.markdown(f'<div class="legal-scroll-box">{LEGAL_TEXT}</div>', unsafe_allow_html=True)
        agree = st.checkbox("I accept the Gobidas Terms & Privacy Protocol")
        if st.button("INITIALIZE", disabled=not agree):
            db = st.session_state.db
            if mode == "Log In":
                if u in db["users"] and db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.messages = []
                    st.rerun()
                else: st.error("Access Denied.")
            else:
                if u and p:
                    db["users"][u] = p
                    db["history"][u] = []
                    save_db(db)
                    st.success("Authorized. Please Log In.")
    st.stop()

# --- 5. SIDEBAR & SETTINGS ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.markdown(f"### Access: **{st.session_state.user}**")
    if st.button("New Command"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    
    st.divider()
    with st.expander("⚙️ System Config"):
        if st.button("SMALL INFO ABOUT THE CREATOR"):
            st.session_state.creator_info_active = True
            st.rerun()
        if st.button("VERY NICE MAN"):
            st.session_state.nice_man_active = True
            st.rerun()
        if st.button("📜 VIEW LEGAL TERMS"):
            st.session_state.legal_overlay_active = True
            st.rerun()
        if st.button("LOG OUT SESSION"):
            del st.session_state.user
            st.rerun()
            
    img_file = st.file_uploader("Visual Scan", type=['png', 'jpg', 'jpeg'])
    st.divider()
    logs = st.session_state.db["history"].get(st.session_state.user, [])
    for i, log in enumerate(reversed(logs)):
        if st.button(f"📄 {log.get('name', 'Log').title()[:22]}", key=f"h_{i}"):
            st.session_state.messages = log.get("msgs", [])
            st.session_state.active_idx = len(logs) - 1 - i
            st.rerun()

# --- 6. CHAT ---
st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Command Gobidas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

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
            
            hist = st.session_state.db["history"].get(st.session_state.user, [])
            chat_data = {"name": prompt[:30], "msgs": st.session_state.messages, "timestamp": time.time()}
            if st.session_state.get("active_idx") is None:
                hist.append(chat_data)
                st.session_state.active_idx = len(hist) - 1
            else:
                hist[st.session_state.active_idx] = chat_data
            st.session_state.db["history"][st.session_state.user] = hist
            save_db(st.session_state.db)
        except Exception as e:
            st.error(f"Inference Failure: {e}")
