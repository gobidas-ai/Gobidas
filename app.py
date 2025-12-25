import streamlit as st
from groq import Groq
import json, os, base64

# --- 1. LUXURY PRO UI ---
st.set_page_config(page_title="Gobidas Pro", layout="wide", page_icon="🟠")

st.markdown("""
    <style>
    .stApp { background-color: #0A0A0A; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #111 !important; border-right: 1px solid #FF6D00; }
    .main-title { font-size: 3rem; font-weight: 900; background: linear-gradient(90deg, #FF6D00, #FFAB40); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }
    .stButton>button { background: linear-gradient(90deg, #FF6D00, #FFAB40) !important; color: white !important; font-weight: bold !important; border-radius: 12px; border: none; width: 100%; }
    .stChatMessage { background-color: #161616 !important; border: 1px solid #222 !important; border-radius: 15px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOCAL DATA STORAGE (The "Account" Memory) ---
DATA_FILE = "user_database.json"

def load_db():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f: return json.load(f)
    return {"users": {}, "history": {}}

def save_db(db):
    with open(DATA_FILE, "w") as f: json.dump(db, f)

db_data = load_db()

# --- 3. AUTHENTICATION (Login/Join Tabs) ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>GOBIDAS PRO</h1>", unsafe_allow_html=True)
    tab_login, tab_join = st.tabs(["🔒 LOGIN", "✨ JOIN SYSTEM"])
    
    with tab_login:
        u = st.text_input("Username", key="login_u")
        p = st.text_input("Password", type="password", key="login_p")
        if st.button("ACCESS SYSTEM"):
            if u in db_data["users"] and db_data["users"][u] == p:
                st.session_state.user = u
                st.rerun()
            else: st.error("Invalid Username or Password")
            
    with tab_join:
        new_u = st.text_input("Choose Username", key="join_u")
        new_p = st.text_input("Choose Password", type="password", key="join_p")
        if st.button("CREATE ACCOUNT"):
            if new_u in db_data["users"]: st.error("Username already taken!")
            elif new_u and new_p:
                db_data["users"][new_u] = new_p
                db_data["history"][new_u] = []
                save_db(db_data)
                st.success("Account Created! Go to Login tab.")
    st.stop()

# --- 4. SIDEBAR (History & New Chat) ---
with st.sidebar:
    st.markdown(f"<h2 style='color:#FF6D00;'>Hello, {st.session_state.user}</h2>", unsafe_allow_html=True)
    if st.button("➕ NEW SESSION"):
        st.session_state.messages = []
        st.session_state.active_chat_index = None
        st.rerun()
    
    st.markdown("---")
    st.write("📂 **PAST CHATS**")
    user_history = db_data["history"].get(st.session_state.user, [])
    for i, chat in enumerate(user_history):
        if st.button(f"🗨️ {chat['title']}", key=f"hist_{i}"):
            st.session_state.messages = chat['msgs']
            st.session_state.active_chat_index = i
            st.rerun()

# --- 5. AI ENGINE & VISION ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.markdown("<h1 class='main-title'>Gobidas Vision</h1>", unsafe_allow_html=True)
if "messages" not in st.session_state: st.session_state.messages = []

# Vision Uploader
uploaded_img = st.sidebar.file_uploader("🖼️ Analyze Image", type=['png', 'jpg', 'jpeg'])

# Display Chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# Chat Input
if prompt := st.chat_input("Command the AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_img: st.image(uploaded_img, width=300)

    with st.chat_message("assistant"):
        if uploaded_img:
            # Llama-3.2 Vision Model
            b64_img = base64.b64encode(uploaded_img.getvalue()).decode('utf-8')
            comp = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}]}]
            )
        else:
            # Standard Text Model
            comp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=st.session_state.messages)
        
        ans = comp.choices[0].message.content
        st.markdown(ans)
        st.session_state.messages.append({"role": "assistant", "content": ans})
        
        # SAVE TO LOCAL DB
        if st.session_state.get("active_chat_index") is None:
            db_data["history"][st.session_state.user].append({"title": prompt[:20], "msgs": st.session_state.messages})
            st.session_state.active_chat_index = len(db_data
