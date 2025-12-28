import streamlit as st
from groq import Groq
import json, os, base64, io, time
from PIL import Image
import streamlit.components.v1 as components

# --- 1. UI & TOTAL STEALTH STYLE ---
st.set_page_config(page_title="Gobidas Beta", layout="wide")

def get_base64(file):
    try:
        with open(file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except: return ""

# Session state for secret mode toggle
if "secret_active" not in st.session_state:
    st.session_state.secret_active = False

bin_str = get_base64('background.jpg')
# Fetching secret files based on your updated names
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
    .welcome-text {{
        text-align: center; color: #bbb; font-size: 1.2rem; margin-top: -20px; margin-bottom: 30px;
    }}
    .stButton>button {{
        width: 100%; border-radius: 12px; background: transparent !important;
        color: white !important; border: 2px solid #FF6D00 !important;
        font-weight: 600; transition: 0.3s all ease-in-out; height: 3em;
    }}
    .stButton>button:hover:not(:disabled) {{
        background: #FF6D00 !important; box-shadow: 0px 0px 30px rgba(255, 109, 0, 0.9);
        color: black !important;
    }}
    .legal-box {{
        height: 450px; overflow-y: scroll; background: rgba(0,0,0,0.6); 
        padding: 25px; border: 1px solid #FF6D00; color: #ccc; border-radius: 10px;
        line-height: 1.8; font-size: 0.95rem;
    }}
    /* SECRET OVERLAY */
    .secret-container {{
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background-color: black; z-index: 999999;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }}
    .secret-img {{
        max-width: 100%; max-height: 100%; object-fit: contain;
    }}
</style>
""", unsafe_allow_html=True)

# --- 2. SECRET FEATURE LOGIC ---
if st.session_state.secret_active:
    st.markdown(f"""
    <div class="secret-container">
        <img src="data:image/png;base64,{sec_img_base64}" class="secret-img">
        <audio autoplay loop>
            <source src="data:audio/mp3;base64,{sec_audio_base64}" type="audio/mp3">
        </audio>
    </div>
    """, unsafe_allow_html=True)
    
    # Positioned at the bottom for easy exit
    if st.button("EXIT SENSIBLE INFO"):
        st.session_state.secret_active = False
        st.rerun()
    st.stop()

# --- 3. STORAGE & DB ---
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

# --- 4. EXTENDED TERMS & POLICY ---
def show_legal_content():
    st.markdown("### Gobidas Global Terms of Service & Privacy Protocol")
    st.markdown("""<div class='legal-box'>
        <b>ARTICLE 1: AGREEMENT TO TERMS</b><br>
        These Terms of Service constitute a legally binding agreement made between you, whether personally or on behalf of an entity, and Gobidas AI regarding your access to and use of the platform. By checking the agreement box, you confirm you have read and understood the entirety of these protocols.<br><br>
        <b>ARTICLE 2: INTELLECTUAL PROPERTY RIGHTS</b><br>
        Unless otherwise indicated, the Site is our proprietary property and all source code, databases, functionality, software, website designs, audio, video, text, photographs, and graphics on the Site. Your outputs are governed by the Meta Llama Community License.<br><br>
        <b>ARTICLE 3: BETA PHASE DISCLAIMER</b><br>
        You acknowledge that Gobidas is currently in an experimental "Beta" phase. The interface utilizes high-parameter neural networks (Llama 4 Scout and Maverick). These models are prone to generating "hallucinations"—outputs that are factually incorrect or nonsensical. Users are advised to verify all critical information independently.<br><br>
        <b>ARTICLE 4: USER DATA & PRIVACY PROTOCOL</b><br>
        Data privacy is fundamental to our architecture. All chat logs and credentials are stored within a local JSON-based database (`gobidas_db.json`). We do not utilize persistent cloud storage for your conversations. To optimize local performance, any logs older than 30 standard days are subject to automated deletion.<br><br>
        <b>ARTICLE 5: PROHIBITED ACTIVITIES</b><br>
        Users may not access or use the Site for any purpose other than that for which we make the Site available. Prohibited activities include, but are not limited to:
        <ul>
            <li>Attempting to bypass security measures or access restricted system files.</li>
            <li>Generating content intended to harass, threaten, or promote violence.</li>
            <li>Using the AI to develop malware or engage in phishing operations.</li>
            <li>Using automated scripts to scrape data from the interface.</li>
        </ul><br>
        <b>ARTICLE 6: LIMITATION OF LIABILITY</b><br>
        In no event will we or our developers be liable to you or any third party for any direct, indirect, consequential, exemplary, incidental, special, or punitive damages, including lost profit, lost revenue, or loss of data arising from your use of the AI.<br><br>
        <b>ARTICLE 7: GOVERNING LAW</b><br>
        These terms and your use of the Site are governed by and construed in accordance with the laws of the jurisdiction in which the developer resides, without regard to its conflict of law principles.
    </div>""", unsafe_allow_html=True)

# --- 5. LOGIN LOGIC ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    st.markdown("<p class='welcome-text'>Secure access to Llama 4 Scout & Maverick Engines.</p>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 1.8, 1])
    with col:
        mode = st.radio("Access Mode", ["Log In", "Sign Up"], horizontal=True, label_visibility="collapsed")
        u = st.text_input("Name", placeholder="Username")
        p = st.text_input("Password", type="password", placeholder="Password")
        
        show_legal_content()
        agree = st.checkbox("I verify that I have read and agree to all Articles above")
        
        if st.button("ENTER", disabled=not agree):
            db = st.session_state.db
            if mode == "Log In":
                if u in db["users"] and db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.messages = []
                    st.rerun()
                else: st.error("Access Denied: Invalid Username/Password.")
            else:
                if u and p:
                    db["users"][u] = p
                    db["history"][u] = []
                    save_db(db)
                    st.success("Account Created. Select 'Log In' to proceed.")
    st.stop()

# --- 6. SIDEBAR & SETTINGS ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.markdown(f"### Logged: **{st.session_state.user}**")
    if st.button("New Chat"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    
    st.divider()
    with st.expander("⚙️ System Settings"):
        if st.button("SENSIBLE INFO"):
            st.session_state.secret_active = True
            st.rerun()
            
    img_file = st.file_uploader("Upload Image (Vision Engine)", type=['png', 'jpg', 'jpeg'])
    
    st.divider()
    st.write("#### History Logs")
    logs = st.session_state.db["history"].get(st.session_state.user, [])
    for i, log in enumerate(reversed(logs)):
        chat_name = log.get('name', 'Chat Session').title()
        if st.button(f"📄 {chat_name[:22]}", key=f"h_{i}"):
            st.session_state.messages = log.get("msgs", [])
            st.session_state.active_idx = len(logs) - 1 - i
            st.rerun()
            
    if st.button("Sign Out Session"):
        del st.session_state.user
        st.rerun()

# --- 7. CHAT INTERFACE ---
st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Command Gobidas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_file: st.image(img_file, width=300)

    with st.chat_message("assistant"):
        try:
            if img_file:
                # LLAMA 4 SCOUT (VISION)
                img = Image.open(img_file).convert("RGB")
                img.thumbnail((800, 800))
                buf = io.BytesIO()
                img.save(buf, format="JPEG")
                b64 = base64.b64encode(buf.getvalue()).decode()
                res = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                    ]}]
                )
            else:
                # LLAMA 4 MAVERICK (TEXT)
                res = client.chat.completions.create(
                    model="meta-llama/llama-4-maverick-17b-128e-instruct",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                )
            
            ans = res.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            # Save History with auto-naming
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
            st.error(f"System Inference Error: {e}")
