import streamlit as st
from groq import Groq
import json, os, base64, io, time
from PIL import Image
import streamlit.components.v1 as components

# --- 1. CONFIG & FORCE-OPEN CSS ---
st.set_page_config(page_title="Gobidas Beta", layout="wide", initial_sidebar_state="expanded")

def get_base64(file):
    if os.path.exists(file):
        with open(file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

bin_str = get_base64('background.jpg')

st.markdown(f"""
<style>
    /* 1. HIDE ALL TRASH (GITHUB, SHARE, MANAGE APP) */
    [data-testid="stHeader"] {{ background: transparent !important; }}
    header[data-testid="stHeader"] > div:nth-child(1) {{ display: none !important; }}
    .stDeployButton, footer, [data-testid="stStatusWidget"], .stActionButton {{
        display: none !important; visibility: hidden !important;
    }}
    
    /* 2. FORCE SIDEBAR TO STAY VISIBLE */
    section[data-testid="stSidebar"] {{
        display: block !important;
        visibility: visible !important;
        background-color: rgba(10, 10, 10, 0.98) !important;
        border-right: 2px solid #FF6D00 !important;
        z-index: 1000001 !important;
    }}

    /* 3. STYLE THE TOGGLE BUTTON (IN CASE IT CLOSES) */
    [data-testid="stSidebarCollapseButton"] {{
        visibility: visible !important;
        display: block !important;
        color: #FF6D00 !important;
        background: rgba(0,0,0,0.8) !important;
        border-radius: 8px !important;
        border: 2px solid #FF6D00 !important;
        position: fixed !important;
        top: 10px !important;
        left: 10px !important;
        z-index: 1000002 !important;
    }}

    /* 4. GLOBAL DESIGN */
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.75)), 
                    url("data:image/jpeg;base64,{bin_str if bin_str else ''}");
        background-size: cover; background-attachment: fixed;
    }}
    .main-title {{
        font-weight: 900; color: #FF6D00; text-align: center; font-size: 5.5rem;
        text-shadow: 0px 0px 35px rgba(255, 109, 0, 0.8);
        margin-top: -40px;
    }}
    .stButton>button {{
        width: 100%; border-radius: 12px; border: 1px solid #FF6D00 !important;
        color: white !important; background: transparent; font-weight: 800;
        text-transform: uppercase;
    }}
    .stButton>button:hover {{
        background: #FF6D00 !important; color: black !important;
    }}
</style>
""", unsafe_allow_html=True)

# THE 100ms CLEANER
components.html("""
<script>
    const forceUI = () => {
        const doc = window.parent.document;
        // Kill Manage App
        doc.querySelectorAll('button').forEach(btn => {
            if (btn.innerText.includes('Manage app')) btn.parentElement.style.display = 'none';
        });
        // Ensure sidebar is expanded if it tries to hide
        const sidebar = doc.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {
            sidebar.style.display = 'block';
            sidebar.style.visibility = 'visible';
        }
    };
    setInterval(forceUI, 100);
</script>
""", height=0)

# --- 2. DATABASE & LEGAL ---
DB_FILE = "gobidas_db.json"
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                now = time.time()
                for u in data.get("history", {}):
                    data["history"][u] = [c for c in data["history"][u] if (now - c.get("ts", now)) < 2592000]
                return data
        except: pass
    return {"users": {}, "history": {}}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

if "db" not in st.session_state:
    st.session_state.db = load_db()

def show_legal():
    st.markdown("## 📜 OFFICIAL TERMS OF SERVICE & PRIVACY POLICY")
    st.error("### **BETA NOTICE**\nGobidas AI is in Beta. Use at your own risk.")
    st.write("**LIABILITY:** Gobidas is a UI for third-party LLMs (Meta/Groq). The developer is NOT responsible for AI-generated content.")
    st.write("**PRIVACY:** Data is stored locally in a JSON file and automatically deleted after 30 days.")

# --- 3. LOGIN SCREEN ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        mode = st.radio("SELECT MODE", ["LOG IN", "SIGN UP"], horizontal=True)
        u = st.text_input("USERNAME")
        p = st.text_input("PASSWORD", type="password")
        agree = st.checkbox("I AGREE TO THE TERMS AND PRIVACY POLICY")
        
        if st.button("ENTER", disabled=not agree):
            if mode == "LOG IN":
                if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.messages = []
                    st.rerun()
                else: st.error("INVALID CREDENTIALS")
            else:
                if u and p:
                    st.session_state.db["users"][u] = p
                    st.session_state.db["history"][u] = []
                    save_db(st.session_state.db)
                    st.success("ACCOUNT CREATED! LOG IN NOW.")
        with st.expander("VIEW FULL LEGAL DOCS"): show_legal()
    st.stop()

# --- 4. SIDEBAR (ALWAYS ACTIVE) ---
with st.sidebar:
    st.title(f"@{st.session_state.user}")
    if st.button("➕ NEW SESSION"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    
    img_file = st.file_uploader("VISION UPLOAD", type=['png', 'jpg', 'jpeg'])
    
    st.divider()
    st.write("### CHAT HISTORY")
    hist_list = st.session_state.db["history"].get(st.session_state.user, [])
    for i in range(len(hist_list)-1, -1, -1):
        chat = hist_list[i]
        c_chat, c_del = st.columns([0.8, 0.2])
        with c_chat:
            if st.button(chat.get('name', 'Log'), key=f"open_{i}"):
                st.session_state.messages = chat.get("msgs", [])
                st.session_state.active_idx = i
                st.rerun()
        with c_del:
            if st.button("🗑️", key=f"del_{i}"):
                hist_list.pop(i)
                st.session_state.db["history"][st.session_state.user] = hist_list
                save_db(st.session_state.db)
                if st.session_state.get("active_idx") == i:
                    st.session_state.messages = []
                    st.session_state.active_idx = None
                st.rerun()

    st.divider()
    if st.button("⚙️ SETTINGS"):
        st.session_state.show_settings = not st.session_state.get("show_settings", False)
    if st.session_state.get("show_settings"):
        if st.button("TERMINATE SESSION"):
            del st.session_state.user
            st.rerun()
        with st.expander("LEGAL DOCS"): show_legal()

# --- 5. CHAT ENGINE ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("COMMAND INPUT..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_file: st.image(img_file, width=300)

    with st.chat_message("assistant"):
        try:
            if img_file:
                img = Image.open(img_file).convert("RGB")
                img.thumbnail((800, 800)); buf = io.BytesIO()
                img.save(buf, format="JPEG")
                b64_str = base64.b64encode(buf.getvalue()).decode('utf-8')
                res = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_str}"}}]}]
                )
            else:
                res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=st.session_state.messages)
            
            ans = res.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            # Save
            history = st.session_state.db["history"].get(st.session_state.user, [])
            chat_title = prompt[:22] + "..." if len(prompt) > 22 else prompt
            chat_entry = {"name": chat_title, "msgs": st.session_state.messages, "ts": time.time()}
            if st.session_state.get("active_idx") is None:
                history.append(chat_entry); st.session_state.active_idx = len(history) - 1
            else:
                history[st.session_state.active_idx] = chat_entry
            st.session_state.db["history"][st.session_state.user] = history
            save_db(st.session_state.db)
        except Exception as e: st.error(f"ERROR: {e}")
