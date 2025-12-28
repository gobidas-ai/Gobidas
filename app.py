import streamlit as st
from groq import Groq
import json, os, base64, io, time
from PIL import Image
import streamlit.components.v1 as components

# --- 1. UI & STEALTH STYLE ---
st.set_page_config(page_title="Gobidas Beta", layout="wide")

def get_base64(file):
    try:
        with open(file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    except: return ""

bin_str = get_base64('background.jpg')
st.markdown(f"""
<style>
    header, [data-testid="stHeader"], .stDeployButton, [data-testid="stToolbar"], 
    footer, [data-testid="stStatusWidget"], [data-testid="stManageAppButton"] {{
        visibility: hidden !important; display: none !important;
    }}
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.9)), 
                    url("data:image/jpeg;base64,{bin_str}");
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    .main-title {{
        font-weight: 900; color: #FF6D00; text-align: center; font-size: 5rem;
        text-shadow: 0px 0px 20px rgba(255, 109, 0, 0.5); margin-bottom: 5px;
    }}
    .welcome-msg {{ text-align: center; color: #aaa; font-size: 1.1rem; margin-bottom: 30px; }}
    .stButton>button {{
        width: 100%; border-radius: 10px; background: transparent !important;
        color: white !important; border: 1px solid #FF6D00 !important;
        font-weight: 600; transition: 0.2s all; height: 3em;
    }}
    .stButton>button:hover:not(:disabled) {{
        background: #FF6D00 !important; color: black !important;
    }}
    [data-testid="stSidebar"] {{
        background: rgba(0, 0, 0, 0.95) !important;
        backdrop-filter: blur(20px); border-right: 1px solid #FF6D00;
    }}
    .legal-box {{
        background: rgba(255,255,255,0.05); padding: 15px; border-radius: 8px;
        font-size: 0.8rem; color: #999; height: 250px; overflow-y: scroll; border: 1px solid rgba(255,109,0,0.2);
    }}
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

# --- 3. LOGIN PAGE ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>GOBIDAS</h1>", unsafe_allow_html=True)
    st.markdown("<p class='welcome-msg'>Secure access to Llama 4 Scout & Maverick</p>", unsafe_allow_html=True)
    
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        mode = st.radio("Access Mode", ["Log In", "Sign Up"], horizontal=True, label_visibility="collapsed")
        u = st.text_input("Username", placeholder="Username")
        p = st.text_input("Password", type="password", placeholder="Password")
        
        st.write("### Terms and Policy")
        st.markdown("""<div class='legal-box'>
        <b>1. Usage:</b> You are accessing an experimental AI interface. <br><br>
        <b>2. Models:</b> This app utilizes Llama 4 Scout (Vision) and Maverick (Text). Outputs may be inaccurate.<br><br>
        <b>3. Privacy:</b> Your data is stored locally in your session database. We do not sell or share personal information.<br><br>
        <b>4. Storage:</b> Chat history is kept for 30 days before being automatically cleared from the local file.<br><br>
        <b>5. Responsibility:</b> You are responsible for all content generated. Do not use for illegal purposes.
        </div>""", unsafe_allow_html=True)
        
        agree = st.checkbox("I agree to the terms and privacy policy")
        
        if st.button("ENTER", disabled=not agree):
            db = st.session_state.db
            if mode == "Log In":
                if u in db["users"] and db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.messages = []
                    st.rerun()
                else: st.error("Invalid Username or Password")
            else:
                if u and p:
                    db["users"][u] = p
                    db["history"][u] = []
                    save_db(db)
                    st.success("Account created! Switch to Log In.")
    st.stop()

# --- 4. SIDEBAR & HISTORY ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.write(f"Logged in as: **{st.session_state.user}**")
    if st.button("New Chat"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    
    st.divider()
    img_file = st.file_uploader("Image Upload (Vision)", type=['png', 'jpg', 'jpeg'])
    
    st.divider()
    st.write("#### History")
    logs = st.session_state.db["history"].get(st.session_state.user, [])
    for i, log in enumerate(reversed(logs)):
        # Formatting history names to Title Case (No more all caps)
        chat_name = log.get('name', 'New Chat').title()
        if st.button(f" {chat_name[:25]}", key=f"h_{i}"):
            st.session_state.messages = log.get("msgs", [])
            st.session_state.active_idx = len(logs) - 1 - i
            st.rerun()
    
    st.divider()
    if st.button("Sign Out"):
        del st.session_state.user
        st.rerun()

# --- 5. MAIN CHAT ---
st.markdown("<h1 class='main-title'>GOBIDAS</h1>", unsafe_allow_html=True)

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Ask Gobidas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_file: st.image(img_file, width=300)

    with st.chat_message("assistant"):
        try:
            if img_file:
                # MODEL: LLAMA 4 SCOUT
                img = Image.open(img_file).convert("RGB")
                img.thumbnail((800, 800))
                buf = io.BytesIO()
                img.save(buf, format="JPEG")
                b64 = base64.b64encode(buf.getvalue()).decode()
                
                res = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                    ]}]
                )
            else:
                # MODEL: LLAMA 4 MAVERICK
                res = client.chat.completions.create(
                    model="meta-llama/llama-4-maverick-17b-128e-instruct",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                )
            
            ans = res.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            # Update History
            hist = st.session_state.db["history"].get(st.session_state.user, [])
            chat_entry = {"name": prompt[:30], "msgs": st.session_state.messages, "timestamp": time.time()}
            if st.session_state.get("active_idx") is None:
                hist.append(chat_entry)
                st.session_state.active_idx = len(hist) - 1
            else:
                hist[st.session_state.active_idx] = chat_entry
            st.session_state.db["history"][st.session_state.user] = hist
            save_db(st.session_state.db)
        except Exception as e:
            st.error(f"Error: {e}")
