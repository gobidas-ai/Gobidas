import streamlit as st
from groq import Groq
import json, os, base64, io
from PIL import Image

# --- 1. PAGE CONFIG & UI ---
st.set_page_config(page_title="GOBIDAS BETA", layout="wide", page_icon="🟠")

st.markdown("""
    <style>
    .stApp { background-color: #0A0A0A; color: white; }
    [data-testid="stSidebar"] { background: #111 !important; border-right: 2px solid #FF6D00; }
    .main-title { font-weight: 900; background: linear-gradient(90deg, #FF6D00, #FFAB40); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; font-size: 3.5rem; }
    .stButton>button { background: linear-gradient(90deg, #FF6D00, #FFAB40) !important; color: white !important; border-radius: 10px; border: none; font-weight: bold; }
    .stChatMessage { background-color: #161616 !important; border-radius: 15px !important; margin-bottom: 10px; border: 1px solid #222 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ---
DB_FILE = "gobidas_db.json"
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {"users": {}, "history": {}}
def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)
db = load_db()

# --- 3. LOGIN ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>GOBIDAS BETA</h1>", unsafe_allow_html=True)
    l_tab, j_tab = st.tabs(["🔒 LOGIN", "✨ JOIN"])
    with l_tab:
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("ENTER"):
            if u in db["users"] and db["users"][u] == p:
                st.session_state.user = u
                st.rerun()
    with j_tab:
        nu = st.text_input("New User")
        np = st.text_input("New Pass", type="password")
        if st.button("CREATE"):
            if nu and np:
                db["users"][nu] = np
                db["history"][nu] = []
                save_db(db)
                st.success("Account Created!")
    st.stop()

# --- 4. SIDEBAR & AI ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.title(f"🟠 {st.session_state.user}")
    if st.button("➕ NEW CHAT"):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    img_file = st.file_uploader("🖼️ Upload Image", type=['png', 'jpg', 'jpeg'])

# --- 5. CHAT LOGIC ---
st.markdown("<h1 class='main-title'>GOBIDAS BETA</h1>", unsafe_allow_html=True)
if "messages" not in st.session_state: st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command Gobidas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_file: st.image(img_file, width=250)

    with st.chat_message("assistant"):
        if img_file:
            # IMAGE PATH
            img = Image.open(img_file).convert("RGB")
            img.thumbnail((800, 800))
            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            
            response = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                    ]
                }]
            )
        else:
            # TEXT PATH
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.messages
            )
        
        ans = response.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
