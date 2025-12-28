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
    except: return ""

bin_str = get_base64('background.jpg')
secret_img_b64 = get_base64('secret_image.png')
secret_audio_b64 = get_base64('secret_music.mp3')

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
    .welcome-msg {{ text-align: center; color: #aaa; font-size: 1.1rem; margin-bottom: 30px; }}
    .stButton>button {{
        width: 100%; border-radius: 10px; background: transparent !important;
        color: white !important; border: 1px solid #FF6D00 !important;
        font-weight: 600; transition: 0.2s all; height: 3em;
    }}
    .stButton>button:hover:not(:disabled) {{
        background: #FF6D00 !important; color: black !important;
    }}
    [data-testid="stSidebar"] {{
        background: rgba(0, 0, 0, 0.95) !important;
        backdrop-filter: blur(20px); border-right: 1px solid #FF6D00;
    }}
    .legal-box {{
        background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px;
        font-size: 0.8rem; color: #999; height: 250px; overflow-y: scroll; border: 1px solid rgba(255,109,0,0.2);
    }}

    /* --- SECRET OVERLAY --- */
    #easterEggOverlay {{
        display: none;
        position: fixed;
        top: 0; left: 0;
        width: 100vw; height: 100vh;
        background-color: #ff8c00;
        z-index: 9999999 !important;
        text-align: center;
    }}
    #easterEggOverlay img {{
        max-height: 80vh; max-width: 90%; margin-top: 5vh;
    }}
    #goBackBtn {{
        display: block; margin: 20px auto; padding: 15px 30px;
        font-size: 20px; cursor: pointer; background: white;
        border: 2px solid black; font-weight: bold; color: black;
    }}
</style>

<div id="easterEggOverlay">
    <img src="data:image/png;base64,{secret_img_b64}">
    <button id="goBackBtn" onclick="window.parent.document.getElementById('easterEggOverlay').style.display='none'; window.parent.document.getElementById('secretAudio').pause();">,, GO BACK"</button>
</div>

<audio id="secretAudio" loop>
    <source src="data:audio/mp3;base64,{secret_audio_b64}" type="audio/mp3">
</audio>

<script>
    window.activateSecret = function() {{
        const overlay = window.parent.document.getElementById('easterEggOverlay');
        const audio = window.parent.document.getElementById('secretAudio');
        overlay.style.display = 'block';
        audio.play();
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

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

if "db" not in st.session_state:
    st.session_state.db = load_db()

# --- 3. LOGIN PAGE ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>GOBIDAS</h1>", unsafe_allow_html=True)
    st.markdown("<p class='welcome-msg'>Secure access to Llama 4 Scout & Maverick</p>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        mode = st.radio("Access Mode", ["Log In", "Sign Up"], horizontal=True, label_visibility="collapsed")
        u = st.text_input("Username", placeholder="Username")
        p = st.text_input("Password", type="password", placeholder="Password")
        
        st.write("### Terms and Policy")
        st.markdown("<div class='legal-box'><b>1. Experimental AI</b><br><b>2. Privacy:</b> Local storage only.<br><b>3. Responsibility:</b> You own the content.</div>", unsafe_allow_html=True)
        
        agree = st.checkbox("I agree to the terms")
        
        if st.button("ENTER", disabled=not agree):
            db = st.session_state.db
            if mode == "Log In":
                if u in db["users"] and db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.messages = []
                    st.rerun()
                else: st.error("Invalid credentials")
            else:
                if u and p:
                    db["users"][u] = p
                    db["history"][u] = []
                    save_db(db)
                    st.success("Account created! Switch to Log In.")
    st.stop()

# --- 4. SIDEBAR & HISTORY ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.write(f"Logged in as: **{st.session_state.user}**")
    
    # WORKING SECRET BUTTON
    with st.expander("⚙️ Settings"):
        components.html("""
            <button onclick="window.parent.activateSecret()" style="background:red; color:white; width:100%; border:none; padding:10px; font-weight:bold; cursor:pointer; border-radius:5px;">
                SECRET DONT OPEN
            </button>
        """, height=50)

    if st.button("New Chat"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    
    st.divider()
    img_file = st.file_uploader("Image Upload (Vision)", type=['png', 'jpg', 'jpeg'])
    
    st.divider()
    st.write("#### History")
    logs = st.session_state.db["history"].get(st.session_state.user, [])
    for i, log in enumerate(reversed(logs)):
        chat_name = log.get('name', 'New Chat').title()
        if st.button(f" {chat_name[:25]}", key=f"h_{i}"):
            st.session_state.messages = log.get("msgs", [])
            st.session_state.active_idx = len(logs) - 1 - i
            st.rerun()
    
    st.divider()
    if st.button("Sign Out"):
        del st.session_state.user
        st.rerun()

# --- 5. MAIN CHAT ---
st.markdown("<h1 class='main-title'>GOBIDAS</h1>", unsafe_allow_html=True)

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Ask Gobidas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_file: st.image(img_file, width=300)

    with st.chat_message("assistant"):
        try:
            res = client.chat.completions.create(
                model="meta-llama/llama-4-maverick-17b-128e-instruct",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            )
            ans = res.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            # Update History Logic
            hist = st.session_state.db["history"].get(st.session_state.user, [])
            chat_entry = {"name": prompt[:30], "msgs": st.session_state.messages, "timestamp": time.time()}
            if st.session_state.get("active_idx") is None:
                hist.append(chat_entry)
                st.session_state.active_idx = len(hist) - 1
            else:
                hist[st.session_state.active_idx] = chat_entry
            st.session_state.db["history"][st.session_state.user] = hist
            save_db(st.session_state.db)
        except Exception as e:
            st.error(f"Error: {e}")
