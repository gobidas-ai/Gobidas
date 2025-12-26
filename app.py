import streamlit as st
from groq import Groq
import json, os, base64, io
from PIL import Image

# --- 1. UI & MODERN CSS ---
st.set_page_config(page_title="GOBIDAS BETA", layout="wide")

def get_base64(file):
    with open(file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Pointing specifically to background.jpg
try:
    bin_str = get_base64('background.jpg')
    st.markdown(f"""
    <style>
    /* Main Background */
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.85)), 
                    url("data:image/jpeg;base64,{bin_str}");
        background-size: cover;
        background-position: center bottom;
        background-attachment: fixed;
    }}

    /* Sidebar - Ultra Dark Glass */
    [data-testid="stSidebar"] {{
        background: rgba(10, 10, 10, 0.85) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 109, 0, 0.3);
    }}

    /* Title - Minimalist Modern */
    .main-title {{
        font-family: 'Inter', sans-serif;
        font-weight: 900;
        letter-spacing: -3px;
        color: #FF6D00;
        text-shadow: 0px 4px 10px rgba(0,0,0,0.5);
        text-align: center;
        font-size: 5.5rem;
        margin-top: -50px;
    }}

    /* Chat Elements */
    .stChatMessage {{
        background: rgba(30, 30, 30, 0.6) !important;
        backdrop-filter: blur(12px);
        border-radius: 12px !important;
        border: 1px solid rgba(255, 109, 0, 0.15) !important;
        margin-bottom: 12px;
    }}

    /* Buttons */
    .stButton>button {{
        border-radius: 8px;
        background: #FF6D00 !important;
        color: white !important;
        border: none !important;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    </style>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    st.error("MISSING FILE: Upload 'background.jpg' to your folder.")

# --- 2. DATA ---
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

# --- 3. LOGIN ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>GOBIDAS</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,1.5,1])
    with col2:
        mode = st.radio("SELECT MODE", ["ACCESS", "REGISTER"], horizontal=True)
        u = st.text_input("ID")
        p = st.text_input("SECRET", type="password")
        if st.button("EXECUTE"):
            if mode == "ACCESS":
                if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.messages = []
                    st.rerun()
            else:
                if u and p:
                    st.session_state.db["users"][u] = p
                    st.session_state.db["history"][u] = []
                    save_db(st.session_state.db)
                    st.success("CREDENTIALS STORED.")
    st.stop()

# --- 4. CORE ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.title(f"USER: {st.session_state.user}")
    if st.button("NEW ARCHIVE"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    
    st.divider()
    img_file = st.file_uploader("VISION UPLOAD", type=['png', 'jpg', 'jpeg'])
    
    st.divider()
    st.write("### RECENT LOGS")
    logs = st.session_state.db["history"].get(st.session_state.user, [])
    for i, log in enumerate(logs):
        if st.button(f"ENTRY {i+1}", key=f"log_{i}"):
            st.session_state.messages = log.get("msgs", [])
            st.session_state.active_idx = i
            st.rerun()

st.markdown("<h1 class='main-title'>GOBIDAS</h1>", unsafe_allow_html=True)

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_file: st.image(img_file, width=300)

    with st.chat_message("assistant"):
        try:
            if img_file:
                img = Image.open(img_file).convert("RGB")
                img.thumbnail((800, 800))
                buf = io.BytesIO()
                img.save(buf, format="JPEG")
                b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                
                res = client.chat.completions.create(
                    model="llama-3.2-11b-vision-preview",
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                    ]}]
                )
            else:
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=st.session_state.messages
                )
            
            txt = res.choices[0].message.content
            st.markdown(txt)
            st.session_state.messages.append({"role": "assistant", "content": txt})
            
            # Auto-save
            h = st.session_state.db["history"].get(st.session_state.user, [])
            if st.session_state.get("active_idx") is None:
                h.append({"name": prompt[:20], "msgs": st.session_state.messages})
                st.session_state.db["history"][st.session_state.user] = h
                st.session_state.active_idx = len(h) - 1
            else:
                idx = st.session_state.active_idx
                st.session_state.db["history"][st.session_state.user][idx]["msgs"] = st.session_state.messages
            save_db(st.session_state.db)
        except Exception as e:
            st.error(f"SYSTEM ERROR: {e}")
