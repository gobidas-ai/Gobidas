import streamlit as st
from groq import Groq
import json, os, base64, io
from PIL import Image

# --- 1. UI SETUP ---
st.set_page_config(page_title="GOBIDAS BETA", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0A0A0A; color: white; }
    [data-testid="stSidebar"] { background: #111 !important; border-right: 2px solid #FF6D00; min-width: 260px !important; }
    .main-title { font-weight: 900; background: linear-gradient(90deg, #FF6D00, #FFAB40); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; font-size: 3rem; }
    .stButton>button { background: linear-gradient(90deg, #FF6D00, #FFAB40) !important; color: white !important; border-radius: 8px; border: none; width: 100%; font-weight: bold; }
    .stChatMessage { background-color: #161616 !important; border-radius: 12px !important; border: 1px solid #222 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ---
DB_FILE = "gobidas_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, dict) and "users" in data and "history" in data:
                    return data
        except: pass
    return {"users": {}, "history": {}}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

if "db" not in st.session_state:
    st.session_state.db = load_db()

# --- 3. LOGIN / JOIN ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>GOBIDAS BETA</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["Login", "Join"])
    with t1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("LOG IN"):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                st.session_state.user = u
                st.session_state.messages = [] # Initialize messages on login
                st.rerun()
    with t2:
        nu = st.text_input("New User")
        np = st.text_input("New Pass", type="password")
        if st.button("SIGN UP"):
            if nu and np:
                st.session_state.db["users"][nu] = np
                st.session_state.db["history"][nu] = []
                save_db(st.session_state.db)
                st.success("Account Created! Use Login tab.")
    st.stop()

# --- 4. SIDEBAR ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.markdown(f"### 🟠 User: {st.session_state.user}")
    if st.button("➕ NEW CHAT", use_container_width=True):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    
    st.markdown("---")
    img_file = st.file_uploader("🖼️ Analyze Image", type=['png', 'jpg', 'jpeg'])
    
    st.markdown("---")
    st.write("📂 **YOUR CHATS**")
    
    # SAFE HISTORY LOOP
    user_history = st.session_state.db["history"].get(st.session_state.user, [])
    for i, chat in enumerate(user_history):
        try:
            chat_name = chat.get('name', f"Chat {i}")
            # Dynamic key prevents DuplicateWidgetID error
            if st.button(f"🗨️ {chat_name}", key=f"hist_{st.session_state.user}_{i}"):
                st.session_state.messages = chat.get('msgs', [])
                st.session_state.active_idx = i
                st.rerun()
        except Exception:
            continue

# --- 5. CHAT ENGINE ---
st.markdown("<h1 class='main-title'>GOBIDAS BETA</h1>", unsafe_allow_html=True)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Show conversation
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Message Gobidas..."):
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
                b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                
                # USING 90B VISION (11B is decommissioned)
                res = client.chat.completions.create(
                    model="llama-3.2-90b-vision-preview", 
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
            
            ans = res.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            # Save History with validation
            if st.session_state.user not in st.session_state.db["history"]:
                st.session_state.db["history"][st.session_state.user] = []
                
            current_hist = st.session_state.db["history"][st.session_state.user]
            if st.session_state.get("active_idx") is None:
                current_hist.append({"name": prompt[:20], "msgs": st.session_state.messages})
                st.session_state.active_idx = len(current_hist) - 1
            else:
                current_hist[st.session_state.active_idx]["msgs"] = st.session_state.messages
            
            save_db(st.session_state.db)
            
        except Exception as e:
            st.error(f"API Error: {e}")
