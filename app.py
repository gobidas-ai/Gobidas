import streamlit as st
from groq import Groq
import json, os, base64, io
from PIL import Image

# --- 1. LUXURY UI CONFIG ---
st.set_page_config(page_title="GOBIDAS BETA", layout="wide", page_icon="🟠")

st.markdown("""
    <style>
    .stApp { background-color: #0A0A0A; color: white; }
    [data-testid="stSidebar"] { background-color: #111 !important; border-right: 2px solid #FF6D00; }
    .main-title { font-weight: 900; background: linear-gradient(90deg, #FF6D00, #FFAB40); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; font-size: 3.5rem; margin-bottom: 10px; }
    .stButton>button { background: linear-gradient(90deg, #FF6D00, #FFAB40) !important; color: white !important; border-radius: 10px; border: none; font-weight: bold; height: 3em; width: 100%; }
    .stChatMessage { background-color: #161616 !important; border: 1px solid #222 !important; border-radius: 15px !important; margin-bottom: 10px; }
    .stChatInputContainer { border-radius: 15px !important; border: 1px solid #333 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE & IMAGE HELPERS ---
DB_FILE = "gobidas_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {"users": {}, "history": {}}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

def process_image(uploaded_file):
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
    img.thumbnail((1024, 1024)) # Keep under 4MB
    buffered = io.BytesIO()
    img.save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

db = load_db()

# --- 3. LOGIN / JOIN SYSTEM ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>GOBIDAS BETA</h1>", unsafe_allow_html=True)
    l_tab, j_tab = st.tabs(["🔒 LOGIN", "✨ JOIN SYSTEM"])
    
    with l_tab:
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("ENTER SYSTEM"):
            if u in db["users"] and db["users"][u] == p:
                st.session_state.user = u
                st.rerun()
            else: st.error("Access Denied")
            
    with j_tab:
        nu = st.text_input("New User", key="j_u")
        np = st.text_input("New Password", type="password", key="j_p")
        if st.button("CREATE ACCOUNT"):
            if nu in db["users"]: st.error("User already exists!")
            elif nu and np:
                db["users"][nu] = np
                db["history"][nu] = []
                save_db(db)
                st.success("Success! Now Login.")
    st.stop()

# --- 4. SIDEBAR & AI CONFIG ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.markdown(f"<h2 style='color:#FF6D00;'>User: {st.session_state.user}</h2>", unsafe_allow_html=True)
    if st.button("➕ NEW SESSION"):
        st.session_state.messages = []
        st.session_state.cid = None
        st.rerun()
    
    st.markdown("---")
    img_file = st.file_uploader("🖼️ Analyze Image", type=['png', 'jpg', 'jpeg'])
    
    st.markdown("---")
    st.write("📂 **SAVED CHATS**")
    user_history = db["history"].get(st.session_state.user, [])
    for i, chat in enumerate(user_history):
        if st.button(f"🗨️ {chat['name']}", key=f"h_{i}"):
            st.session_state.messages = chat['msgs']
            st.session_state.cid = i
            st.rerun()

# --- 5. MAIN CHAT ENGINE ---
st.markdown("<h1 class='main-title'>GOBIDAS BETA</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command Gobidas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_file: st.image(img_file, width=300)

    with st.chat_message("assistant"):
        try:
            if img_file:
                b64 = process_image(img_file)
                comp = client.chat.completions.create(
                    model="llama-3.2-11b-vision-preview",
                    messages=[{"role": "user", "content": [{"type":"text","text":prompt}, {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}]
                )
            else:
                comp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=st.session_state.messages)
            
            ans = comp.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})

            # Save to Database
            if st.session_state.get("cid") is None:
                db["history"][st.session_state.user].append({"name": prompt[:20], "msgs": st.session_state.messages})
                st.session_state.cid = len(db["history"][st.session_state.user]) - 1
            else:
                db["history"][st.session_state.user][st.session_state.cid]["msgs"] = st.session_state.messages
            save_db(db)

        except Exception:
            st.error("⚠️ Sorry, our AI is off right now.")
