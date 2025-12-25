import streamlit as st
from groq import Groq
import json, os, base64

# --- 1. SET PAGE CONFIG (MUST BE FIRST) ---
st.set_page_config(page_title="GOBIDAS BETA", layout="wide", page_icon="🟠")

# --- 2. LUXURY DARK UI ---
st.markdown("""
    <style>
    .stApp { background-color: #0A0A0A; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #111 !important; border-right: 2px solid #FF6D00; }
    .main-title { font-size: 3.5rem; font-weight: 900; background: linear-gradient(90deg, #FF6D00, #FFAB40); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 20px; }
    .stButton>button { background: linear-gradient(90deg, #FF6D00, #FFAB40) !important; color: white !important; font-weight: bold !important; border-radius: 12px; border: none; height: 3em; transition: 0.3s; }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0px 0px 15px #FF6D00; }
    .stChatMessage { background-color: #161616 !important; border: 1px solid #222 !important; border-radius: 15px !important; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOCAL DATABASE (Account Storage) ---
DB_FILE = "gobidas_db.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return json.load(f)
    return {"users": {}, "history": {}}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

db = load_db()

# --- 4. LOGIN / JOIN SYSTEM ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>GOBIDAS BETA</h1>", unsafe_allow_html=True)
    login_tab, join_tab = st.tabs(["🔒 LOGIN", "✨ CREATE ACCOUNT"])
    
    with login_tab:
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("LOG IN"):
            if u in db["users"] and db["users"][u] == p:
                st.session_state.user = u
                st.rerun()
            else: st.error("Wrong info. Try again.")
            
    with join_tab:
        nu = st.text_input("New Username", key="j_u")
        np = st.text_input("New Password", type="password", key="j_p")
        if st.button("JOIN SYSTEM"):
            if nu in db["users"]: st.error("Name taken.")
            elif nu and np:
                db["users"][nu] = np
                db["history"][nu] = []
                save_db(db)
                st.success("Account created! Now go to the Login tab.")
    st.stop()

# --- 5. THE AI BRAIN (Groq) ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 6. SIDEBAR (History & Image Upload) ---
with st.sidebar:
    st.markdown(f"<h2 style='color:#FF6D00;'>User: {st.session_state.user}</h2>", unsafe_allow_html=True)
    
    if st.button("➕ START NEW CHAT"):
        st.session_state.messages = []
        st.session_state.current_chat_id = None
        st.rerun()

    st.markdown("---")
    st.write("🖼️ **IMAGE ANALYSIS**")
    img = st.file_uploader("Upload image for AI to see", type=['png', 'jpg', 'jpeg'])
    
    st.markdown("---")
    st.write("📂 **PAST CHATS**")
    user_chats = db["history"].get(st.session_state.user, [])
    for idx, chat in enumerate(user_chats):
        if st.button(f"🗨️ {chat['name']}", key=f"chat_{idx}"):
            st.session_state.messages = chat['content']
            st.session_state.current_chat_id = idx
            st.rerun()

# --- 7. MAIN CHAT INTERFACE ---
st.markdown("<h1 class='main-title'>GOBIDAS BETA</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Show previous messages
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# User Input
if prompt := st.chat_input("Command the AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img: st.image(img, width=300)

    with st.chat_message("assistant"):
        # Image Analysis vs Text Analysis
from PIL import Image
import io

def process_image(uploaded_file):
    """Resizes image if too large and encodes to base64."""
    img = Image.open(uploaded_file)
    # Resize if larger than 1024px to keep it under the 4MB Groq limit
    if max(img.size) > 1024:
        img.thumbnail((1024, 1024))
    
    buffered = io.BytesIO()
    # Convert to RGB if it's a PNG with transparency (prevents errors)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    img.save(buffered, format="JPEG", quality=85)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- REPLACE YOUR CHAT INPUT LOGIC WITH THIS ---
if prompt := st.chat_input("Command the AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img: st.image(img, width=300)

    with st.chat_message("assistant"):
        try:
            if img:
                # Use the new helper function
                b64_string = process_image(img)
                completion = client.chat.completions.create(
                    model="llama-3.2-11b-vision-preview",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_string}"}}
                        ]
                    }]
                )
            else:
                completion = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=st.session_state.messages
                )
            
            response = completion.choices[0].message.content
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Save to history logic...
            # (Keep your existing history saving code here)

        except Exception as e:
            st.error(f"AI Error: {str(e)}")
            st.info("Tip: Try a smaller image or a different file format.")
        # Save to Database History
        if st.session_state.get("current_chat_id") is None:
            db["history"][st.session_state.user].append({"name": prompt[:20], "content": st.session_state.messages})
            st.session_state.current_chat_id = len(db["history"][st.session_state.user]) - 1
        else:
            cid = st.session_state.current_chat_id
            db["history"][st.session_state.user][cid]["content"] = st.session_state.messages
        save_db(db)
