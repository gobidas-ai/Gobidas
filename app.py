import streamlit as st
from groq import Groq
import json, os, base64, io
from PIL import Image

# --- 1. THE ACTUAL MASTER OFF SWITCH ---
# This ONLY triggers if you manually set AI_ONLINE = false in Secrets.
if not st.secrets.get("AI_ONLINE", True):
    st.markdown("<h1 style='color:red; text-align:center; font-size:60px; margin-top:100px;'>SORRY OUR AI IS OFF NOW</h1>", unsafe_allow_html=True)
    st.stop()

# --- 2. UI SETUP ---
st.set_page_config(page_title="GOBIDAS BETA", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0A0A0A; color: white; }
    [data-testid="stSidebar"] { background: #111 !important; border-right: 2px solid #FF6D00; }
    .main-title { font-weight: 900; background: linear-gradient(90deg, #FF6D00, #FFAB40); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; font-size: 3.5rem; }
    .stButton>button { background: linear-gradient(90deg, #FF6D00, #FFAB40) !important; color: white !important; font-weight: bold; }
    .stChatMessage { background-color: #161616 !important; border-radius: 15px !important; border: 1px solid #222 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATABASE ---
DB_FILE = "gobidas_db.json"
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {"users": {}, "history": {}}
def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)
db = load_db()

# --- 4. LOGIN ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>GOBIDAS BETA</h1>", unsafe_allow_html=True)
    l_tab, j_tab = st.tabs(["🔒 LOGIN", "✨ JOIN"])
    with l_tab:
        u, p = st.text_input("User"), st.text_input("Pass", type="password")
        if st.button("ENTER"):
            if u in db["users"] and db["users"][u] == p:
                st.session_state.user = u
                st.rerun()
    with j_tab:
        nu, np = st.text_input("New User"), st.text_input("New Pass", type="password")
        if st.button("CREATE"):
            if nu and np:
                db["users"][nu] = np
                db["history"][nu] = []
                save_db(db)
                st.success("Done! Login now.")
    st.stop()

# --- 5. SIDEBAR & VISION PREP ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.title(f"🟠 {st.session_state.user}")
    if st.button("➕ NEW CHAT"):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    img_file = st.file_uploader("🖼️ Upload Image", type=['png', 'jpg', 'jpeg'])

# --- 6. CHAT LOGIC ---
st.markdown("<h1 class='main-title'>GOBIDAS BETA</h1>", unsafe_allow_html=True)
if "messages" not in st.session_state: st.session_state.messages = []

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
                # 1. Clean & Resize Image
                raw_img = Image.open(img_file).convert("RGB")
                raw_img.thumbnail((800, 800))
                buf = io.BytesIO()
                raw_img.save(buf, format="JPEG")
                b64_data = base64.b64encode(buf.getvalue()).decode('utf-8')
                
                # 2. Send specifically for Vision
                response = client.chat.completions.create(
                    model="llama-3.2-11b-vision-preview",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_data}"}}
                        ]
                    }]
                )
            else:
                # 3. Regular Text Chat
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=st.session_state.messages
                )
            
            final_text = response.choices[0].message.content
            st.markdown(final_text)
            st.session_state.messages.append({"role": "assistant", "content": final_text})
            
        except Exception as e:
            # THIS IS THE KEY: If it's a vision error, show the REAL error, not the "OFF" message.
            st.error(f"Vision Error: {e}")
