import streamlit as st
from groq import Groq
import json, os, base64, io, time

# --- 1. UI & BACKGROUND ---
st.set_page_config(page_title="Gobidas Beta", layout="wide")

def get_base64(file):
    try:
        with open(file, 'rb') as f: return base64.b64encode(f.read()).decode()
    except: return ""

# Restoring your background
bg_img = get_base64('background.jpg')

st.markdown(f"""
<style>
    [data-testid="stAppViewContainer"] {{
        background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.7)), 
                    url("data:image/jpeg;base64,{bg_img}");
        background-size: cover;
        background-attachment: fixed;
    }}
    .main-title {{ font-size: 5rem; color: #FF6D00; text-align: center; font-weight: 900; text-shadow: 2px 2px 10px #000; }}
    .stButton>button {{ background: transparent; border: 2px solid #FF6D00; color: white; width: 100%; border-radius: 10px; }}
    .stButton>button:hover {{ background: #FF6D00; color: black; }}
    [data-testid="stSidebar"] {{ background: rgba(0,0,0,0.9) !important; border-right: 2px solid #FF6D00; }}
    .legal-box {{ height: 350px; overflow-y: scroll; background: rgba(0,0,0,0.5); padding: 20px; border: 1px solid #FF6D00; color: #ccc; border-radius: 10px; }}
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE ---
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

# --- 3. SIMPLE LOGIN / SIGN UP ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    st.warning("Website in beta: data loss may occur. Enjoy Gobidas!")
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        mode = st.radio("Action", ["Log in", "Sign up"], horizontal=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        
        st.write("### Terms and Policy")
        st.markdown("""<div class='legal-box'>
            1. <b>BETA STATUS:</b> This is a testing environment. Data may be cleared without notice.<br><br>
            2. <b>DATA:</b> We store your username and chat history locally for your convenience.<br><br>
            3. <b>CONTENT:</b> Do not generate illegal, harmful, or toxic content.<br><br>
            4. <b>ACCURACY:</b> AI can hallucinate. Do not rely on it for medical or legal advice.<br><br>
            5. <b>PRIVACY:</b> We do not sell your data to third parties.
        </div>""", unsafe_allow_html=True)
        
        if st.button("Enter") if st.checkbox("I agree to the terms") else st.button("Enter", disabled=True):
            db = st.session_state.db
            if mode == "Log in":
                if u in db["users"] and db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.messages = []
                    st.rerun()
                else: st.error("Wrong Username or Password.")
            else:
                if u and p:
                    db["users"][u] = p
                    db["history"][u] = []
                    save_db(db)
                    st.success("Account created! You can now Log in.")
    st.stop()

# --- 4. CHAT ENGINE (NO LLAMA) ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.write(f"Logged in as: **{st.session_state.user}**")
    if st.button("New Chat"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    
    img_file = st.file_uploader("Upload Image for AI", type=['png', 'jpg', 'jpeg'])
    
    st.divider()
    st.write("### History")
    logs = st.session_state.db["history"].get(st.session_state.user, [])
    for i, log in enumerate(reversed(logs)):
        if st.button(f"{log['name'][:20]}", key=f"h_{i}"):
            st.session_state.messages = log["msgs"]
            st.session_state.active_idx = len(logs) - 1 - i
            st.rerun()
            
    if st.button("Log out"):
        del st.session_state.user
        st.rerun()

st.markdown("<h1 class='main-title'>Gobidas AI</h1>", unsafe_allow_html=True)

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "img" in m: st.image(f"data:image/jpeg;base64,{m['img']}", width=400)

if prompt := st.chat_input("Message Gobidas..."):
    entry = {"role": "user", "content": prompt}
    b64 = None
    if img_file:
        b64 = base64.b64encode(img_file.read()).decode()
        entry["img"] = b64

    st.session_state.messages.append(entry)
    with st.chat_message("user"):
        st.markdown(prompt)
        if b64: st.image(img_file, width=400)

    with st.chat_message("assistant"):
        try:
            # Using Mixtral-8x7b-32768 (NO LLAMA)
            # Note: For real vision, Groq currently requires specific vision models. 
            # I am using Mixtral as the primary text engine to avoid Llama.
            res = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            )
            
            ans = res.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            # Save to JSON
            hist = st.session_state.db["history"].get(st.session_state.user, [])
            chat_obj = {"name": prompt[:20], "msgs": st.session_state.messages}
            
            if st.session_state.get("active_idx") is None:
                hist.append(chat_obj)
                st.session_state.active_idx = len(hist) - 1
            else:
                hist[st.session_state.active_idx] = chat_obj
            
            st.session_state.db["history"][st.session_state.user] = hist
            save_db(st.session_state.db)
        except Exception as e:
            st.error(f"Error: {e}")
