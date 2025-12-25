import streamlit as st
from groq import Groq
import json, os, base64, io
from PIL import Image

# --- 1. GLOBAL SETTINGS ---
st.set_page_config(page_title="GOBIDAS BETA", layout="wide", page_icon="🟠")

# --- 2. THE MASTER KILL SWITCH ---
# (Change AI_ONLINE to false in your Streamlit Secrets to turn off the site)
if not st.secrets.get("AI_ONLINE", True):
    st.markdown("<h1 style='color:red; text-align:center; font-size:60px; margin-top:100px;'>SORRY OUR AI IS OFF NOW</h1>", unsafe_allow_html=True)
    st.stop()

# --- 3. PRO DARK UI ---
st.markdown("""
    <style>
    .stApp { background-color: #0A0A0A; color: white; }
    [data-testid="stSidebar"] { background-color: #111 !important; border-right: 2px solid #FF6D00; }
    .main-title { font-weight: 900; background: linear-gradient(90deg, #FF6D00, #FFAB40); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; font-size: 3.5rem; }
    .stButton>button { background: linear-gradient(90deg, #FF6D00, #FFAB40) !important; color: white !important; border-radius: 10px; border: none; font-weight: bold; height: 3em; width: 100%; }
    .stChatMessage { background-color: #161616 !important; border: 1px solid #222 !important; border-radius: 15px !important; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. DATA HELPERS ---
DB_FILE = "gobidas_db.json"
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {"users": {}, "history": {}}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

def process_image(uploaded_file):
    """Crucial fix: Resizes image to stay under Groq's 4MB limit."""
    img = Image.open(uploaded_file)
    if img.mode in ("RGBA", "P"): img = img.convert("RGB")
    # Reduce size to 800px width max
    img.thumbnail((800, 800))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=70) # Quality 70 keeps it small
    return base64.b64encode(buf.getvalue()).decode('utf-8')

db = load_db()

# --- 5. LOGIN / JOIN ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>GOBIDAS BETA</h1>", unsafe_allow_html=True)
    l_tab, j_tab = st.tabs(["🔒 LOGIN", "✨ JOIN"])
    with l_tab:
        u, p = st.text_input("Username"), st.text_input("Password", type="password")
        if st.button("ENTER"):
            if u in db["users"] and db["users"][u] == p:
                st.session_state.user = u
                st.rerun()
            else: st.error("Access Denied")
    with j_tab:
        nu, np = st.text_input("New User"), st.text_input("New Pass", type="password")
        if st.button("CREATE"):
            if nu and np:
                db["users"][nu] = np
                db["history"][nu] = []
                save_db(db)
                st.success("Account Created! Now Login.")
    st.stop()

# --- 6. AI & SIDEBAR ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.markdown(f"### Welcome, {st.session_state.user}")
    if st.button("➕ NEW CHAT"):
        st.session_state.messages = []
        st.session_state.cid = None
        st.rerun()
    st.markdown("---")
    img_file = st.file_uploader("🖼️ Upload Image", type=['png', 'jpg', 'jpeg'])
    st.markdown("---")
    history = db["history"].get(st.session_state.user, [])
    for i, chat in enumerate(history):
        if st.button(f"🗨️ {chat['name']}", key=f"h_{i}"):
            st.session_state.messages = chat['msgs']
            st.session_state.cid = i
            st.rerun()

# --- 7. CHAT LOGIC ---
st.markdown("<h1 class='main-title'>GOBIDAS BETA</h1>", unsafe_allow_html=True)
if "messages" not in st.session_state: st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command Gobidas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_file: st.image(img_file, width=200)

    with st.chat_message("assistant"):
        try:
            if img_file:
                b64 = process_image(img_file)
                # Model check: llama-3.2-11b-vision-preview is the correct vision model
                res = client.chat.completions.create(
                    model="llama-3.2-11b-vision-preview",
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                    ]}]
                )
            else:
                res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=st.session_state.messages)
            
            ans = res.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})

            # Save to Database
            if st.session_state.get("cid") is None:
                db["history"][st.session_state.user].append({"name": prompt[:20], "msgs": st.session_state.messages})
                st.session_state.cid = len(db["history"][st.session_state.user]) - 1
            else:
                db["history"][st.session_state.user][st.session_state.cid]["msgs"] = st.session_state.messages
            save_db(db)

        except Exception as e:
            # If there's an actual crash, show the Big Red Text
            st.markdown("<h2 style='color:red; text-align:center;'>SORRY OUR AI IS OFF NOW</h2>", unsafe_allow_html=True)
            st.error(f"Technical Reason: {e}")
