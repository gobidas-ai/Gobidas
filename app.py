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

if "secret_active" not in st.session_state:
    st.session_state.secret_active = False

bin_str = get_base64('background.jpg')
sec_img_base64 = get_base64('secret_image.png')
sec_audio_base64 = get_base64('secret_music.mp3')

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
    [data-testid="stSidebar"] {{
        background: rgba(0, 0, 0, 0.95) !important;
        backdrop-filter: blur(25px); border-right: 2px solid #FF6D00;
    }}
    .main-title {{
        font-weight: 900; color: #FF6D00; text-align: center; font-size: 5.5rem;
        text-shadow: 0px 0px 25px rgba(255, 109, 0, 0.6); margin-bottom: 0px;
    }}
    .stButton>button {{
        width: 100%; border-radius: 12px; background: transparent !important;
        color: white !important; border: 2px solid #FF6D00 !important;
        font-weight: 600; height: 3em;
    }}
    .stButton>button:hover:not(:disabled) {{
        background: #FF6D00 !important; color: black !important;
    }}
    .secret-container {{
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background-color: black; z-index: 999999;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }}
    .secret-img {{ max-width: 100%; max-height: 85%; object-fit: contain; }}
    .exit-btn-container {{ position: fixed; bottom: 20px; z-index: 1000000; width: 200px; }}
</style>
""", unsafe_allow_html=True)

# --- 2. SECRET FEATURE ---
if st.session_state.secret_active:
    st.markdown(f'<div class="secret-container"><img src="data:image/png;base64,{sec_img_base64}" class="secret-img"><audio autoplay loop><source src="data:audio/mp3;base64,{sec_audio_base64}" type="audio/mp3"></audio></div>', unsafe_allow_html=True)
    _, btn_col, _ = st.columns([1, 0.5, 1])
    with btn_col:
        st.markdown('<div class="exit-btn-container">', unsafe_allow_html=True)
        if st.button("EXIT INFO"):
            st.session_state.secret_active = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --- 3. DATABASE ---
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

# --- 4. LOGIN LOGIC ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.8, 1])
    with col:
        mode = st.radio("Access Mode", ["Log In", "Sign Up"], horizontal=True, label_visibility="collapsed")
        u = st.text_input("Username", placeholder="Username")
        p = st.text_input("Password", type="password", placeholder="Password")
        agree = st.checkbox("I verify that I have read and agree to all terms")
        if st.button("ENTER", disabled=not agree):
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
                    st.success("Account Created.")
    st.stop()

# --- 5. SIDEBAR ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.markdown(f"### Logged: **{st.session_state.user}**")
    if st.button("New Chat"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    st.divider()
    with st.expander("⚙️ System Settings"):
        if st.button("SMALL INFO ABOUT THE CREATOR"):
            st.session_state.secret_active = True
            st.rerun()
    img_file = st.file_uploader("Upload Image (Vision Engine)", type=['png', 'jpg', 'jpeg'])
    st.divider()
    logs = st.session_state.db["history"].get(st.session_state.user, [])
    for i, log in enumerate(reversed(logs)):
        if st.button(f"📄 {log.get('name', 'Chat').title()[:22]}", key=f"h_{i}"):
            st.session_state.messages = log.get("msgs", [])
            st.session_state.active_idx = len(logs) - 1 - i
            st.rerun()
    if st.button("Sign Out Session"):
        del st.session_state.user
        st.rerun()

# --- 6. CHAT & IMAGE GENERATION ---
st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "gen_img_url" in msg:
            st.image(msg["gen_img_url"], use_container_width=True)

if prompt := st.chat_input("Command Gobidas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_file: st.image(img_file, width=300)

    with st.chat_message("assistant"):
        trigger_words = ["generate image", "draw", "create image", "make an image", "generate an image", "show me an image"]
        
        if any(word in prompt.lower() for word in trigger_words):
            # This is the "Loading Circle" (Spinner)
            with st.spinner("Gobidas is accessing Nano Banana Engines..."):
                clean_prompt = prompt.lower()
                for word in trigger_words:
                    clean_prompt = clean_prompt.replace(word, "")
                
                # Using an image generation placeholder logic
                gen_url = f"https://pollinations.ai/p/{clean_prompt.strip().replace(' ', '_')}?width=1024&height=1024&seed={int(time.time())}&nologo=true"
                
                # Small delay to make the loading circle feel real
                time.sleep(2) 
                
                st.markdown(f"**Image Generated for:** {prompt}")
                st.image(gen_url, use_container_width=True)
                
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"I have processed your request for: {prompt}",
                    "gen_img_url": gen_url
                })
        else:
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
            except Exception as e:
                st.error(f"Error: {e}")
        
        # Save History
        hist = st.session_state.db["history"].get(st.session_state.user, [])
        chat_data = {"name": prompt[:30], "msgs": st.session_state.messages, "timestamp": time.time()}
        if st.session_state.get("active_idx") is None:
            hist.append(chat_data)
            st.session_state.active_idx = len(hist) - 1
        else:
            hist[st.session_state.active_idx] = chat_data
        st.session_state.db["history"][st.session_state.user] = hist
        save_db(st.session_state.db)
