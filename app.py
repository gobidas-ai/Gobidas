import streamlit as st
from groq import Groq
import pandas as pd
from supabase import create_client
import base64

# --- 1. PRO UI ---
st.set_page_config(page_title="Gobidas Vision", layout="wide", page_icon="🟠")
st.markdown("""
    <style>
    .stApp { background-color: #0A0A0A; color: white; }
    [data-testid="stSidebar"] { background-color: #111 !important; }
    .stButton>button { background: #FF6D00 !important; color: white; border-radius: 10px; width: 100%; }
    .main-title { font-weight: 900; background: linear-gradient(90deg, #FF6D00, #FFAB40); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CONNECT DATABASE & AI ---
db = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def encode_image(image_file):
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

# --- 3. AUTHENTICATION ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title' style='text-align:center;'>GOBIDAS SYSTEM</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Login", "Join System"])
    
    with tab1:
        u = st.text_input("Username", key="l_u")
        p = st.text_input("Password", type="password", key="l_p")
        if st.button("Access"):
            res = db.table("profiles").select("*").eq("username", u).eq("password", p).execute()
            if res.data:
                st.session_state.user = u
                st.rerun()
            else: st.error("Invalid Credentials")
            
    with tab2:
        new_u = st.text_input("New Username")
        new_p = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            try:
                db.table("profiles").insert({"username": new_u, "password": new_p}).execute()
                st.success("Account Created! You can now login.")
            except: st.error("Username taken.")
    st.stop()

# --- 4. SIDEBAR & HISTORY ---
with st.sidebar:
    st.title(f"🟠 {st.session_state.user}")
    if st.button("➕ NEW CHAT"):
        st.session_state.chat_id = None
        st.session_state.messages = []
        st.rerun()

    st.markdown("### HISTORY")
    hist = db.table("chats").select("id, title").eq("username", st.session_state.user).order("id", desc=True).execute()
    for chat in hist.data:
        if st.button(f"🗨️ {chat['title']}", key=f"h_{chat['id']}"):
            res = db.table("chats").select("messages").eq("id", chat['id']).execute()
            st.session_state.messages = res.data[0]['messages']
            st.session_state.chat_id = chat['id']
            st.rerun()

# --- 5. CHAT & VISION ---
st.markdown("<h1 class='main-title'>Gobidas Vision</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state: st.session_state.messages = []
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# Image Upload
img_file = st.sidebar.file_uploader("Upload Image to Analyze", type=['png', 'jpg', 'jpeg'])

if prompt := st.chat_input("Ask about the image or chat..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_file: st.image(img_file, width=300)

    with st.chat_message("assistant"):
        if img_file:
            # Use Llama Vision Model
            base64_image = encode_image(img_file)
            chat_completion = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }]
            )
        else:
            chat_completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=st.session_state.messages
            )
            
        response = chat_completion.choices[0].message.content
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Auto-Save to Database
        if "chat_id" not in st.session_state or st.session_state.chat_id is None:
            new_chat = db.table("chats").insert({
                "username": st.session_state.user, 
                "title": prompt[:20], 
                "messages": st.session_state.messages
            }).execute()
            st.session_state.chat_id = new_chat.data[0]['id']
        else:
            db.table("chats").update({"messages": st.session_state.messages}).eq("id", st.session_state.chat_id).execute()
