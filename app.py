import streamlit as st
from groq import Groq
import json, os, base64, io
from PIL import Image

# --- 1. UI & BACKGROUND CONFIG ---
st.set_page_config(page_title="GOBIDAS BETA", layout="wide")

def get_base64(file):
    with open(file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Tries to load your background.png
try:
    bin_str = get_base64('background.png')
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    [data-testid="stSidebar"] {{
        background: rgba(10, 10, 10, 0.9) !important;
        border-right: 2px solid #FF6D00;
    }}
    .main-title {{
        font-weight: 900;
        color: #FF6D00;
        text-align: center;
        font-size: 4rem;
        text-transform: uppercase;
    }}
    .stChatMessage {{
        background: rgba(20, 20, 20, 0.8) !important;
        backdrop-filter: blur(10px);
        border-radius: 15px !important;
        border: 1px solid #FF6D00 !important;
        margin-bottom: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)
except FileNotFoundError:
    st.error("MISSING FILE: Upload 'background.png' to your GitHub repo!")

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

# --- 3. ACCESS CONTROL ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>GOBIDAS BETA</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["LOGIN", "SIGN UP"])
    with tab1:
        u, p = st.text_input("Username"), st.text_input("Password", type="password")
        if st.button("LOGIN"):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                st.session_state.user = u
                st.session_state.messages = []
                st.rerun()
    with tab2:
        nu, np = st.text_input("New Username"), st.text_input("New Password", type="password")
        if st.button("REGISTER"):
            if nu and np:
                st.session_state.db["users"][nu] = np
                st.session_state.db["history"][nu] = []
                save_db(st.session_state.db)
                st.success("Account Created.")
    st.stop()

# --- 4. SIDEBAR & HISTORY ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.header(f"USER: {st.session_state.user}")
    if st.button("NEW CHAT"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    
    st.markdown("---")
    img_file = st.file_uploader("UPLOAD IMAGE", type=['png', 'jpg', 'jpeg'])
    
    st.markdown("---")
    st.subheader("HISTORY")
    user_logs = st.session_state.db["history"].get(st.session_state.user, [])
    for i, log in enumerate(user_logs):
        if st.button(f"Chat {i+1}: {log.get('name', 'Log')}", key=f"log_{i}"):
            st.session_state.messages = log.get("msgs", [])
            st.session_state.active_idx = i
            st.rerun()

# --- 5. CHAT LOGIC ---
st.markdown("<h1 class='main-title'>GOBIDAS BETA</h1>", unsafe_allow_html=True)

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_file: st.image(img_file, width=250)

    with st.chat_message("assistant"):
        try:
            if img_file:
                # Process Image
                img = Image.open(img_file).convert("RGB")
                img.thumbnail((800, 800))
                buf = io.BytesIO()
                img.save(buf, format="JPEG")
                b64_data = base64.b64encode(buf.getvalue()).decode('utf-8')
                
                # Vision Model
                response = client.chat.completions.create(
                    model="llama-3.2-11b-vision-preview",
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"}}
                    ]}]
                )
            else:
                # Text Model
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=st.session_state.messages
                )
            
            output = response.choices[0].message.content
            st.markdown(output)
            st.session_state.messages.append({"role": "assistant", "content": output})
            
            # Auto-save History
            user_hist = st.session_state.db["history"].get(st.session_state.user, [])
            if st.session_state.get("active_idx") is None:
                user_hist.append({"name": prompt[:15], "msgs": st.session_state.messages})
                st.session_state.db["history"][st.session_state.user] = user_hist
                st.session_state.active_idx = len(user_hist) - 1
            else:
                idx = st.session_state.active_idx
                st.session_state.db["history"][st.session_state.user][idx]["msgs"] = st.session_state.messages
            save_db(st.session_state.db)

        except Exception as e:
            st.error(f"FATAL ERROR: {e}")
