import streamlit as st
from groq import Groq
import json, os, base64, io, time
from PIL import Image
import streamlit.components.v1 as components

# --- 1. UI & STEALTH STYLE ---
st.set_page_config(page_title="Gobidas Beta", layout="wide")

def get_base64(file):
    try:
        with open(file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except Exception as e:
        return ""

# Pre-loading assets to embed them directly in the HTML
bin_str = get_base64('background.jpg')
secret_img_b64 = get_base64('secret_image.png')
secret_audio_b64 = get_base64('secret_music.mp3')

# Main CSS and Hidden Overlay Logic
st.markdown(f"""
<style>
    header, [data-testid="stHeader"], .stDeployButton, [data-testid="stToolbar"], 
    footer, [data-testid="stStatusWidget"], [data-testid="stManageAppButton"] {{
        visibility: hidden !important; display: none !important;
    }}
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.9)), 
                    url("data:image/jpeg;base64,{bin_str}");
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    .main-title {{
        font-weight: 900; color: #FF6D00; text-align: center; font-size: 5rem;
        text-shadow: 0px 0px 20px rgba(255, 109, 0, 0.5); margin-bottom: 5px;
    }}
    
    /* THE SECRET OVERLAY */
    #easterEggOverlay {{
        display: none;
        position: fixed;
        top: 0; left: 0;
        width: 100vw; height: 100vh;
        background-color: #ff8c00;
        z-index: 1000000;
        text-align: center;
    }}
    #easterEggOverlay img {{
        max-height: 80vh; max-width: 90%; margin-top: 5vh; border: 5px solid white;
    }}
    #goBackBtn {{
        display: block; margin: 20px auto; padding: 15px 30px;
        font-size: 20px; cursor: pointer; background: white;
        border: 2px solid black; font-weight: bold; color: black;
    }}

    /* CUSTOM SIDEBAR BUTTON */
    .secret-trigger-btn {{
        background-color: red !important;
        color: white !important;
        width: 100%;
        border: none;
        padding: 10px;
        font-weight: bold;
        cursor: pointer;
        border-radius: 5px;
        margin-top: 10px;
    }}
</style>

<div id="easterEggOverlay">
    <img src="data:image/png;base64,{secret_img_b64}">
    <button id="goBackBtn" onclick="stopSecret()">,, GO BACK"</button>
</div>

<audio id="secretAudio" loop>
    <source src="data:audio/mp3;base64,{secret_audio_b64}" type="audio/mp3">
</audio>

<script>
    function startSecret() {{
        const overlay = window.parent.document.getElementById('easterEggOverlay');
        const audio = window.parent.document.getElementById('secretAudio');
        overlay.style.display = 'block';
        audio.play().catch(e => console.log("Audio play blocked, click page first"));
    }}

    function stopSecret() {{
        document.getElementById('easterEggOverlay').style.display = 'none';
        const audio = document.getElementById('secretAudio');
        audio.pause();
        audio.currentTime = 0;
    }}
</script>
""", unsafe_allow_html=True)

# --- 2. DATABASE ---
DB_FILE = "gobidas_db.json"
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: pass
    return {"users": {}, "history": {}}

if "db" not in st.session_state:
    st.session_state.db = load_db()

# --- 3. LOGIN PAGE ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>GOBIDAS</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("ENTER"):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                st.session_state.user = u
                st.session_state.messages = []
                st.rerun()
    st.stop()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.write(f"Logged in as: **{st.session_state.user}**")
    
    # SETTINGS WITH THE ACTUAL WORKING BUTTON
    with st.expander("⚙️ Settings"):
        components.html("""
            <button class="secret-trigger-btn" onclick="parent.startSecret()">
                SECRET DONT OPEN
            </button>
            <style>
                .secret-trigger-btn {
                    background-color: red; color: white; width: 100%;
                    border: none; padding: 12px; font-weight: bold;
                    cursor: pointer; border-radius: 5px;
                }
            </style>
        """, height=50)

    if st.button("Sign Out"):
        del st.session_state.user
        st.rerun()

# --- 5. MAIN CHAT ---
st.markdown("<h1 class='main-title'>GOBIDAS</h1>", unsafe_allow_html=True)
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Ask Gobidas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        res = client.chat.completions.create(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        )
        ans = res.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
