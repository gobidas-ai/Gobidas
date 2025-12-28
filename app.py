import streamlit as st
from groq import Groq
import json, os, base64, io, time
from PIL import Image

# --- 1. UI & STEALTH HEADER STYLE ---
st.set_page_config(page_title="Gobidas Beta", layout="wide", initial_sidebar_state="expanded")

def get_base64(file):
    try:
        with open(file, 'rb') as f: return base64.b64encode(f.read()).decode()
    except: return ""

bin_str = get_base64('background.jpg')

st.markdown(f"""
<style>
    /* 1. RESTORE HEADER BUT HIDE GITHUB ICON ONLY */
    header[data-testid="stHeader"] {{
        visibility: visible !important;
        background: rgba(0,0,0,0.5) !important;
    }}
    
    /* Target the specific GitHub icon button in the header */
    .stApp a[href*="github.com"], 
    .stApp [data-testid="stHeader"] svg[viewBox*="github"],
    [data-testid="stHeaderActionElements"] button:has(svg[viewBox*="0 0 16 16"]) {{
        display: none !important;
        visibility: hidden !important;
    }}

    /* 2. HIDE STREAMLIT WATERMARK & PROFILE ICON (Bottom Right) */
    footer, [data-testid="stStatusWidget"], [data-testid="stManageAppButton"] {{
        visibility: hidden !important;
        display: none !important;
    }}

    /* 3. APP BACKGROUND & SIDEBAR */
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.85)), 
                    url("data:image/jpeg;base64,{bin_str}");
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    
    [data-testid="stSidebar"] {{
        background: rgba(0, 0, 0, 0.95) !important;
        backdrop-filter: blur(25px); border-right: 2px solid #FF6D00;
    }}
    
    .main-title {{
        font-weight: 900; color: #FF6D00; text-align: center; font-size: 5rem;
        text-shadow: 0px 0px 25px rgba(255, 109, 0, 0.6);
    }}
    
    .stButton>button {{
        width: 100%; border-radius: 12px; background: transparent !important;
        color: white !important; border: 2px solid #FF6D00 !important;
    }}

    .legal-box {{
        font-size: 0.8rem; color: #bbb; background: rgba(255,109,0,0.1); 
        padding: 15px; border-radius: 8px; border: 1px solid rgba(255,109,0,0.4);
    }}
</style>
""", unsafe_allow_html=True)

# --- 2. STORAGE SYSTEM ---
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

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("### Gobidas Controls")
    if "user" in st.session_state:
        st.markdown(f"👤 **User:** {st.session_state.user}")
        if st.button("➕ New Chat"):
            st.session_state.messages = []
            st.session_state.active_idx = None
            st.rerun()
        
        st.divider()
        img_file = st.file_uploader("🖼️ Attach Image", type=['png', 'jpg', 'jpeg'])
        
        st.divider()
        st.write("📂 History")
        logs = st.session_state.db["history"].get(st.session_state.user, [])
        for i, log in enumerate(reversed(logs)):
            if st.button(f"💬 {log.get('name', 'Chat')[:20]}", key=f"h_{i}"):
                st.session_state.messages = log.get("msgs", [])
                st.session_state.active_idx = len(logs) - 1 - i
                st.rerun()
        
        if st.button("🚪 Logout"):
            del st.session_state.user
            st.rerun()

# --- 4. LOGIN & TERMS SCREEN ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        mode = st.radio(" ", ["Log In", "Sign Up"], horizontal=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        st.markdown("<div class='legal-box'>Data stored for 30 days. No illegal prompts.</div>", unsafe_allow_html=True)
        agree = st.checkbox("I agree to the Terms")
        
        if st.button("Access System", disabled=not agree):
            if mode == "Log In":
                if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.messages = []
                    st.rerun()
                else: st.error("Access Denied.")
            else:
                if u and p:
                    st.session_state.db["users"][u] = p
                    st.session_state.db["history"][u] = []
                    save_db(st.session_state.db)
                    st.success("Account Created! Now Log In.")
    st.stop()

# --- 5. CHAT ENGINE (Llama 3.2 90B Vision) ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
st.markdown("<h1 class='main-title'>Gobidas AI</h1>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "image" in msg: st.image(msg["image"], width=400)

if prompt := st.chat_input("Ask Gobidas..."):
    msg_entry = {"role": "user", "content": prompt}
    if img_file: msg_entry["image"] = img_file.getvalue()
    st.session_state.messages.append(msg_entry)
    
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_file: st.image(img_file, width=400)

    with st.chat_message("assistant"):
        try:
            if img_file:
                img = Image.open(img_file).convert("RGB")
                img.thumbnail((800, 800))
                buf = io.BytesIO()
                img.save(buf, format="JPEG")
                b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                
                res = client.chat.completions.create(
                    model="llama-3.2-90b-vision-preview",
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                    ]}]
                )
            else:
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                )
            
            ans = res.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            hist = st.session_state.db["history"].get(st.session_state.user, [])
            chat_summary = {"name": prompt[:25], "msgs": st.session_state.messages, "timestamp": time.time()}
            
            if st.session_state.get("active_idx") is None:
                hist.append(chat_summary)
                st.session_state.db["history"][st.session_state.user] = hist
                st.session_state.active_idx = len(hist) - 1
            else:
                st.session_state.db["history"][st.session_state.user][st.session_state.active_idx] = chat_summary
            save_db(st.session_state.db)
        except Exception as e:
            st.error(f"Error: {e}")
