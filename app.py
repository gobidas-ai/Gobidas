import streamlit as st
from groq import Groq
import json, os, base64, io
from PIL import Image

# --- 1. UI & YOUR EXACT PNG BACKGROUND ---
st.set_page_config(page_title="GOBIDAS BETA", layout="wide")

# Function to convert your local PNG to base64 for the CSS
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Look specifically for background.png
try:
    bin_str = get_base64_of_bin_file('background.png')
    bg_img_style = f"""
    <style>
    .stApp {{
        background-image: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("data:image/png;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    </style>
    """
    st.markdown(bg_img_style, unsafe_allow_html=True)
except FileNotFoundError:
    st.error("Error: 'background.png' not found. Make sure the file is in your folder!")
    st.markdown("<style>.stApp {background-color: #0e1117;}</style>", unsafe_allow_html=True)

st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background: rgba(10, 10, 10, 0.95) !important;
        border-right: 3px solid #FF6D00;
    }
    .main-title {
        font-weight: 900;
        background: linear-gradient(90deg, #FF6D00, #FFAB40);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        font-size: 4.5rem;
    }
    .stChatMessage {
        background: rgba(25, 25, 25, 0.8) !important;
        backdrop-filter: blur(12px);
        border-radius: 18px !important;
        border: 1px solid rgba(255, 109, 0, 0.3) !important;
        color: white !important;
    }
    .stButton>button {
        background: linear-gradient(90deg, #FF6D00, #FFAB40) !important;
        color: white !important;
        border-radius: 10px;
        font-weight: bold;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ---
DB_FILE = "gobidas_db.json"
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except: pass
    return {"users": {}, "history": {}}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

if "db" not in st.session_state:
    st.session_state.db = load_db()

# --- 3. LOGIN ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>GOBIDAS BETA</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["🔒 ENTER", "✨ JOIN"])
    with t1:
        u, p = st.text_input("User"), st.text_input("Pass", type="password")
        if st.button("INITIALIZE"):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                st.session_state.user = u
                st.session_state.messages = []
                st.rerun()
    with t2:
        nu, np = st.text_input("New User"), st.text_input("New Pass", type="password")
        if st.button("CREATE DATA"):
            if nu and np:
                st.session_state.db["users"][nu] = np
                st.session_state.db["history"][nu] = []
                save_db(st.session_state.db)
                st.success("Identity Created!")
    st.stop()

# --- 4. SIDEBAR ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.markdown(f"# 🟠 {st.session_state.user}")
    if st.button("➕ NEW SESSION"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    
    st.markdown("---")
    img_file = st.file_uploader("🖼️ IMAGE ANALYZER", type=['png', 'jpg', 'jpeg'])
    
    st.markdown("---")
    st.write("📂 **LOGS**")
    user_chats = st.session_state.db["history"].get(st.session_state.user, [])
    for i, chat in enumerate(user_chats):
        name = chat.get("name", f"Log {i}")
        if st.button(f"🗨️ {name}", key=f"h_{i}"):
            st.session_state.messages = chat.get("msgs", [])
            st.session_state.active_idx = i
            st.rerun()

# --- 5. CORE ENGINE ---
st.markdown("<h1 class='main-title'>GOBIDAS BETA</h1>", unsafe_allow_html=True)

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Input Command..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_file: st.image(img_file, width=300)

    with st.chat_message("assistant"):
        try:
            if img_file:
                # Prepare image for AI
                img = Image.open(img_file).convert("RGB")
                img.thumbnail((800, 800))
                buf = io.BytesIO()
                img.save(buf, format="JPEG")
                b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                
                # Using current stable vision model
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
            
            ans = res.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            # Save to History Database
            user_hist = st.session_state.db["history"].get(st.session_state.user, [])
            if st.session_state.get("active_idx") is None:
                user_hist.append({"name": prompt[:20], "msgs": st.session_state.messages})
                st.session_state.db["history"][st.session_state.user] = user_hist
                st.session_state.active_idx = len(user_hist) - 1
            else:
                idx = st.session_state.active_idx
                st.session_state.db["history"][st.session_state.user][idx]["msgs"] = st.session_state.messages
            save_db(st.session_state.db)

        except Exception as e:
            st.error(f"ENGINE ERROR: {e}")
