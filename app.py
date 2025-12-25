import streamlit as st
from groq import Groq
import json, os, base64, io
from PIL import Image

# --- 1. CONFIG & UI ---
st.set_page_config(page_title="GOBIDAS BETA", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0A0A0A; color: white; }
    [data-testid="stSidebar"] { background: #111 !important; border-right: 2px solid #FF6D00; }
    .main-title { font-weight: 900; background: linear-gradient(90deg, #FF6D00, #FFAB40); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; font-size: 3rem; }
    .stButton>button { background: linear-gradient(90deg, #FF6D00, #FFAB40) !important; color: white !important; font-weight: bold; border: none; }
    .stChatMessage { background-color: #161616 !important; border: 1px solid #222 !important; border-radius: 10px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ---
DB_FILE = "gobidas_db.json"

def load_db():
    try:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r") as f:
                return json.load(f)
    except:
        pass
    return {"users": {}, "history": {}}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f)

# Initialize session data
if "db" not in st.session_state:
    st.session_state.db = load_db()

# --- 3. LOGIN / JOIN ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>GOBIDAS BETA</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Login", "Join"])
    
    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("LOG IN"):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                st.session_state.user = u
                st.rerun()
            else: st.error("Invalid Credentials")
            
    with tab2:
        nu = st.text_input("New Username")
        np = st.text_input("New Password", type="password")
        if st.button("CREATE ACCOUNT"):
            if nu and np:
                st.session_state.db["users"][nu] = np
                st.session_state.db["history"][nu] = []
                save_db(st.session_state.db)
                st.success("Success! Log in now.")
    st.stop()

# --- 4. SIDEBAR (Explicit Rendering) ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Force Sidebar to appear
with st.sidebar:
    st.subheader(f"User: {st.session_state.user}")
    
    if st.button("➕ NEW CHAT"):
        st.session_state.messages = []
        st.session_state.chat_idx = None
        st.rerun()

    st.markdown("---")
    img_file = st.file_uploader("🖼️ Analyze Image", type=['png', 'jpg', 'jpeg'])

    st.markdown("---")
    st.write("📂 **HISTORY**")
    user_history = st.session_state.db["history"].get(st.session_state.user, [])
    for i, chat in enumerate(user_history):
        if st.button(f"🗨️ {chat['name']}", key=f"hist_btn_{i}"):
            st.session_state.messages = chat['msgs']
            st.session_state.chat_idx = i
            st.rerun()

# --- 5. CHAT INTERFACE ---
st.markdown("<h1 class='main-title'>GOBIDAS BETA</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display current messages
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# User Input
if prompt := st.chat_input("Command Gobidas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_file: st.image(img_file, width=200)

    with st.chat_message("assistant"):
        try:
            if img_file:
                # 1. Image Prep
                pil_img = Image.open(img_file).convert("RGB")
                pil_img.thumbnail((800, 800))
                b_io = io.BytesIO()
                pil_img.save(b_io, format="JPEG")
                b64_str = base64.b64encode(b_io.getvalue()).decode('utf-8')
                
                # 2. Vision Call
                response = client.chat.completions.create(
                    model="llama-3.2-11b-vision-preview",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_str}"}}
                        ]
                    }]
                )
            else:
                # 3. Text Call
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=st.session_state.messages
                )
            
            ans = response.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})

            # 4. Save to History
            if st.session_state.get("chat_idx") is None:
                st.session_state.db["history"][st.session_state.user].append({
                    "name": prompt[:20], 
                    "msgs": st.session_state.messages
                })
                st.session_state.chat_idx = len(st.session_state.db["history"][st.session_state.user]) - 1
            else:
                idx = st.session_state.chat_idx
                st.session_state.db["history"][st.session_state.user][idx]["msgs"] = st.session_state.messages
            
            save_db(st.session_state.db)

        except Exception as e:
            st.error(f"API Error: {str(e)}")
