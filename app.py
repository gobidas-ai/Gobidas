import streamlit as st
from groq import Groq
import json, os, base64, io
from PIL import Image

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="GOBIDAS BETA", layout="wide")

def get_base64(file):
    with open(file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

# Using background.jpg
try:
    bin_str = get_base64('background.jpg')
    st.markdown(f"""
    <style>
    /* Background Image */
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), 
                    url("data:image/jpeg;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    /* Modern Glass Sidebar */
    [data-testid="stSidebar"] {{
        background: rgba(0, 0, 0, 0.7) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid #FF6D00;
    }}

    /* Glow Title */
    .main-title {{
        font-family: 'Inter', sans-serif;
        font-weight: 900;
        color: #FF6D00;
        text-align: center;
        font-size: 5rem;
        text-shadow: 0px 0px 20px rgba(255, 109, 0, 0.6);
        margin-bottom: 40px;
    }}

    /* Glow Buttons */
    .stButton>button {{
        width: 100%;
        border-radius: 10px;
        background: transparent !important;
        color: white !important;
        border: 2px solid #FF6D00 !important;
        font-weight: 700;
        transition: 0.4s all ease;
    }}

    /* THE HOVER LIGHT-UP EFFECT */
    .stButton>button:hover {{
        background: #FF6D00 !important;
        box-shadow: 0px 0px 30px rgba(255, 109, 0, 0.8);
        color: black !important;
        transform: scale(1.02);
    }}

    /* Clean Chat Boxes */
    .stChatMessage {{
        background: rgba(255, 255, 255, 0.03) !important;
        backdrop-filter: blur(10px);
        border-radius: 15px !important;
        border: 1px solid rgba(255, 109, 0, 0.2) !important;
    }}
    </style>
    """, unsafe_allow_html=True)
except:
    st.error("Put 'background.jpg' in your folder!")

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

# --- 3. SIMPLE LOGIN ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>GOBIDAS</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1,1.5,1])
    with c2:
        mode = st.radio(" ", ["ENTER", "JOIN"], horizontal=True)
        u = st.text_input("NAME")
        p = st.text_input("PASSWORD", type="password")
        if st.button("GO"):
            if mode == "ENTER":
                if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.messages = []
                    st.rerun()
            else:
                if u and p:
                    st.session_state.db["users"][u] = p
                    st.session_state.db["history"][u] = []
                    save_db(st.session_state.db)
                    st.success("SAVED! NOW CLICK ENTER.")
    st.stop()

# --- 4. CHAT INTERFACE ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.title(f"Hi, {st.session_state.user}")
    if st.button("NEW CHAT"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    
    st.divider()
    img_file = st.file_uploader("SEND IMAGE", type=['png', 'jpg', 'jpeg'])
    
    st.divider()
    st.write("PAST CHATS")
    logs = st.session_state.db["history"].get(st.session_state.user, [])
    for i, log in enumerate(logs):
        if st.button(f"Chat {i+1}", key=f"chat_{i}"):
            st.session_state.messages = log.get("msgs", [])
            st.session_state.active_idx = i
            st.rerun()

st.markdown("<h1 class='main-title'>GOBIDAS</h1>", unsafe_allow_html=True)

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Ask anything..."):
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
            
            answer = res.choices[0].message.content
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
            # Save progress
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
            st.error(f"Error: {e}")
