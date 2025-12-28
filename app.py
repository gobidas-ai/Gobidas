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
st.markdown(f"""
<style>
    header, [data-testid="stHeader"], .stDeployButton, [data-testid="stToolbar"], 
    footer, [data-testid="stStatusWidget"], [data-testid="stManageAppButton"] {{
        visibility: hidden !important; display: none !important;
    }}
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.85)), 
                    url("data:image/jpeg;base64,{bin_str}");
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    .main-title {{
        font-weight: 900; color: #FF6D00; text-align: center; font-size: 5.5rem;
        text-shadow: 0px 0px 25px rgba(255, 109, 0, 0.6); margin-bottom: 5px;
    }}
    .welcome-msg {{ text-align: center; color: #eee; font-size: 1.3rem; margin-bottom: 40px; font-weight: 300; }}
    .stButton>button {{
        width: 100%; border-radius: 12px; background: transparent !important;
        color: white !important; border: 2px solid #FF6D00 !important;
        font-weight: 700; transition: 0.3s all; height: 3.5em; text-transform: uppercase;
    }}
    .stButton>button:hover:not(:disabled) {{
        background: #FF6D00 !important; color: black !important;
        box-shadow: 0px 0px 30px rgba(255, 109, 0, 0.8);
    }}
    [data-testid="stSidebar"] {{
        background: rgba(0, 0, 0, 0.9) !important;
        backdrop-filter: blur(20px); border-right: 2px solid #FF6D00;
    }}
    .legal-text {{
        background: rgba(0,0,0,0.4); padding: 15px; border-radius: 10px;
        border: 1px solid rgba(255, 109, 0, 0.2); font-size: 0.85rem; color: #ccc;
        height: 300px; overflow-y: auto; margin-bottom: 20px;
    }}
</style>
""", unsafe_allow_html=True)

# --- 2. STORAGE ---
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

# --- 3. LOGIN & WELCOME SCREEN ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>GOBIDAS</h1>", unsafe_allow_html=True)
    st.markdown("<p class='welcome-msg'>Welcome. Please log in to access the Llama 4 network.</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        mode = st.radio("Select Action", ["Log In", "Sign Up"], horizontal=True, label_visibility="collapsed")
        u = st.text_input("Name", placeholder="Username")
        p = st.text_input("Password", type="password", placeholder="Password")
        
        st.markdown("**TERMS AND PRIVACY POLICY**")
        st.markdown("""<div class='legal-text'>
        <b>1. Introduction</b><br>Welcome to Gobidas. By accessing our AI, you agree to these terms.<br><br>
        <b>2. Beta Disclaimer</b><br>This service is in Beta. We use Llama 4 Scout and Maverick. These models are experimental and may generate inaccurate, biased, or offensive content.<br><br>
        <b>3. Data Usage</b><br>We store your data locally in a JSON format. We do not transmit your personal data to third parties, except for prompts sent to Groq Cloud for processing.<br><br>
        <b>4. User Responsibility</b><br>You are solely responsible for the prompts you enter. Illegal use of this AI will result in immediate account termination.<br><br>
        <b>5. Intellectual Property</b><br>Outputs generated are subject to the Llama 4 Community License. Do not claim sole authorship of AI-generated works.<br><br>
        <b>6. Auto-Deletion</b><br>To maintain system performance, chat histories older than 30 days are automatically purged from our local database.<br><br>
        <b>7. No Warranty</b><br>Gobidas is provided "as-is" without any warranties of any kind regarding reliability or availability.
        </div>""", unsafe_allow_html=True)
        
        agree = st.checkbox("I agree to the Terms and Privacy Policy")
        
        if st.button("ENTER", disabled=not agree):
            db = st.session_state.db
            if mode == "Log In":
                if u in db["users"] and db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.messages = []
                    st.rerun()
                else: st.error("Invalid credentials.")
            else:
                if u and p:
                    db["users"][u] = p
                    db["history"][u] = []
                    save_db(db)
                    st.success("Account created! Please switch to Log In.")
    st.stop()

# --- 4. CHAT SYSTEM (THE MODELS) ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.markdown(f"### User: {st.session_state.user}")
    if st.button("New Chat"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    
    st.divider()
    img_file = st.file_uploader("Upload Image (Scout Vision)", type=['png', 'jpg', 'jpeg'])
    
    st.divider()
    st.write("Recent Activity")
    logs = st.session_state.db["history"].get(st.session_state.user, [])
    for i, log in enumerate(reversed(logs)):
        if st.button(f" {log.get('name', 'Chat')[:20]}", key=f"h_{i}"):
            st.session_state.messages = log.get("msgs", [])
            st.session_state.active_idx = len(logs) - 1 - i
            st.rerun()
    
    if st.button("Log Out"):
        del st.session_state.user
        st.rerun()

st.markdown("<h1 class='main-title'>GOBIDAS</h1>", unsafe_allow_html=True)

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Message Gobidas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_file: st.image(img_file, width=300)

    with st.chat_message("assistant"):
        try:
            if img_file:
                # BACK TO LLAMA 4 SCOUT (VISION)
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
                # BACK TO LLAMA 4 MAVERICK (TEXT)
                res = client.chat.completions.create(
                    model="meta-llama/llama-4-maverick-17b-128e-instruct",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                )
            
            ans = res.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            # Save to History
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
            st.error(f"Engine Error: {e}")
