import streamlit as st
from groq import Groq
import json, os, base64

# --- 1. LUXURY UI CONFIG ---
st.set_page_config(page_title="Gobidas Pro", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0A0A0A; color: white; }
    [data-testid="stSidebar"] { background-color: #111 !important; border-right: 1px solid #FF6D00; }
    .main-title { font-weight: 900; background: linear-gradient(90deg, #FF6D00, #FFAB40); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; font-size: 3rem; }
    .stButton>button { background: linear-gradient(90deg, #FF6D00, #FFAB40) !important; color: white !important; border-radius: 10px; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOCAL STORAGE LOGIC (No Database Needed) ---
DATA_FILE = "system_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f: return json.load(f)
    return {"users": {}, "chats": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f)

data = load_data()

# --- 3. ACCOUNTS / LOGIN ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>GOBIDAS SYSTEM</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Login", "Create Account"])
    
    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Enter System"):
            if u in data["users"] and data["users"][u] == p:
                st.session_state.user = u
                st.rerun()
            else: st.error("Access Denied")
            
    with tab2:
        new_u = st.text_input("New User")
        new_p = st.text_input("New Pass", type="password")
        if st.button("Register"):
            if new_u in data["users"]: st.error("User exists")
            else:
                data["users"][new_u] = new_p
                data["chats"][new_u] = []
                save_data(data)
                st.success("Account Created!")
    st.stop()

# --- 4. THE AI BRAIN ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- 5. SIDEBAR (History) ---
with st.sidebar:
    st.title(f"🟠 {st.session_state.user}")
    if st.button("➕ NEW CHAT"):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("### YOUR HISTORY")
    user_chats = data["chats"].get(st.session_state.user, [])
    for i, history_chat in enumerate(user_chats):
        if st.button(f"🗨️ {history_chat['title']}", key=f"hist_{i}"):
            st.session_state.messages = history_chat['msgs']
            st.rerun()

# --- 6. MAIN CHAT & VISION ---
st.markdown("<h1 class='main-title'>Gobidas Vision</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []

# IMAGE UPLOADER
img = st.sidebar.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Speak to Gobidas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img: st.image(img, width=250)

    with st.chat_message("assistant"):
        if img:
            # Use the Vision Model
            b64_img = base64.b64encode(img.getvalue()).decode('utf-8')
            response = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}]}]
            ).choices[0].message.content
        else:
            # Regular Text Model
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.messages
            ).choices[0].message.content
        
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # SAVE TO HISTORY
        if len(st.session_state.messages) <= 2: # New chat detected
            data["chats"][st.session_state.user].append({"title": prompt[:20], "msgs": st.session_state.messages})
        else: # Update existing last chat
            data["chats"][st.session_state.user][-1]["msgs"] = st.session_state.messages
        save_data(data)
