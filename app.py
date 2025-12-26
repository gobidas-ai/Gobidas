import streamlit as st
from groq import Groq
import json, os, base64, io, time
from PIL import Image
import streamlit.components.v1 as components

# --- 1. CONFIG & ABSOLUTE STEALTH CSS ---
st.set_page_config(page_title="Gobidas Beta", layout="wide", initial_sidebar_state="expanded")

def get_base64(file):
    if os.path.exists(file):
        with open(file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

bin_str = get_base64('background.jpg')

st.markdown(f"""
<style>
    /* 1. NUCLEAR OPTION TO HIDE HEADER & FOOTER */
    header, [data-testid="stHeader"], [data-testid="stToolbar"], .stDeployButton {{
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }}
    
    footer, [data-testid="stFooter"], [data-testid="stStatusWidget"] {{
        display: none !important;
        visibility: hidden !important;
    }}

    /* Specific fix for the 'Manage app' button in the bottom right */
    button[title="Manage app"], [data-testid="stManageAppButton"] {{
        display: none !important;
    }}

    /* 2. HIDE SIDEBAR COLLAPSE BUTTON */
    [data-testid="stSidebarCollapseButton"] {{
        display: none !important;
    }}

    /* 3. LOCK SIDEBAR WIDTH */
    section[data-testid="stSidebar"] {{
        width: 320px !important;
        min-width: 320px !important;
        background-color: rgba(10, 10, 10, 0.98) !important;
        border-right: 2px solid #FF6D00 !important;
    }}

    /* 4. MAIN APP BACKGROUND & TITLES */
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), 
                    url("data:image/jpeg;base64,{bin_str if bin_str else ''}");
        background-size: cover;
        background-attachment: fixed;
    }}
    
    .main-title {{
        font-weight: 900; 
        color: #FF6D00; 
        text-align: center; 
        font-size: 5rem;
        text-shadow: 0px 0px 25px rgba(255, 109, 0, 0.6);
        margin-top: -50px; /* Pull up since header is gone */
    }}

    /* 5. BUTTON & INPUT STYLING */
    .stButton>button {{
        width: 100%; border-radius: 10px; border: 1px solid #FF6D00 !important;
        color: white !important; background: transparent; font-weight: bold;
    }}
    .stButton>button:hover {{
        background: #FF6D00 !important; color: black !important;
        box-shadow: 0px 0px 15px rgba(255, 109, 0, 0.4);
    }}
    
    /* Make chat input look cleaner */
    [data-testid="stChatInput"] {{
        border: 1px solid rgba(255, 109, 0, 0.3) !important;
        border-radius: 15px !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- 2. JAVASCRIPT REINFORCEMENT ---
# This script runs every half second to delete the 'Manage app' element if it spawns
components.html("""
<script>
    const hideExtra = () => {
        const selectors = [
            'button[title="Manage app"]',
            '[data-testid="stManageAppButton"]',
            'header',
            '.stDeployButton',
            'footer'
        ];
        selectors.forEach(s => {
            const el = window.parent.document.querySelector(s);
            if (el) el.style.display = 'none';
        });
    };
    setInterval(hideExtra, 500);
</script>
""", height=0)

# --- 3. DATABASE & LEGAL ---
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
    st.markdown("## Comprehensive Terms of Service & Privacy Agreement")
    st.error("### **BETA VERSION NOTICE**\nGobidas Artificial Intelligence is in a Beta testing phase. Users acknowledge that the Software is provided 'as-is'.")
    st.markdown("### 1. Limitation of Liability")
    st.write("Gobidas acts as an interface for third-party LLMs (Meta/Groq). The developer is NOT responsible for AI-generated output.")
    st.markdown("### 2. Privacy Policy")
    st.write("Credentials and chat logs are stored in a local JSON file. All entries are purged after 30 days of inactivity.")

# --- 4. LOGIN FLOW ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.8, 1])
    with c2:
        mode = st.radio(" ", ["Log In", "Sign Up"], horizontal=True)
        u = st.text_input("Name")
        p = st.text_input("Password", type="password")
        agree = st.checkbox("I agree to the 30-day retention policy and liability terms")
        
        if st.button("Access System", disabled=not agree):
            if mode == "Log In":
                if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.messages = []
                    st.rerun()
                else: st.error("Authentication Failed.")
            else:
                if u and p:
                    st.session_state.db["users"][u] = p
                    st.session_state.db["history"][u] = []
                    save_db(st.session_state.db)
                    st.success("Account created successfully.")
        
        with st.expander("Full Legal Documentation"):
            show_legal()
    st.stop()

# --- 5. SIDEBAR (STABILIZED) ---
with st.sidebar:
    st.title(f"@{st.session_state.user}")
    
    if st.button("➕ New Session"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    
    img_file = st.file_uploader("Vision Input", type=['png', 'jpg', 'jpeg'])
    
    st.divider()
    st.write("### Chat Archives")
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
    if st.button("⚙️ Control Panel"):
        st.session_state.show_settings = not st.session_state.get("show_settings", False)
    
    if st.session_state.get("show_settings"):
        if st.button("Terminate Session (Logout)"):
            del st.session_state.user
            st.rerun()
        with st.expander("Legal & Privacy"):
            show_legal()

# --- 6. CHAT INTERFACE ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Command input..."):
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
                b64_str = base64.b64encode(buf.getvalue()).decode('utf-8')
                
                res = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_str}"}}
                    ]}]
                )
            else:
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile", 
                    messages=st.session_state.messages
                )
            
            ans = res.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            # Save Logic
            history = st.session_state.db["history"].get(st.session_state.user, [])
            chat_title = prompt[:20] + "..." if len(prompt) > 20 else prompt
            chat_entry = {"name": chat_title, "msgs": st.session_state.messages, "ts": time.time()}
            
            if st.session_state.get("active_idx") is None:
                history.append(chat_entry)
                st.session_state.active_idx = len(history) - 1
            else:
                history[st.session_state.active_idx] = chat_entry
            
            st.session_state.db["history"][st.session_state.user] = history
            save_db(st.session_state.db)
            
        except Exception as e:
            st.error(f"System Overload: {e}")
