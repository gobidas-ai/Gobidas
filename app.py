import streamlit as st
from groq import Groq
import json, os, base64, io, time
from PIL import Image

# --- 1. CONFIG & REFINED UI ---
st.set_page_config(page_title="Gobidas Beta", layout="wide", initial_sidebar_state="expanded")

def get_base64(file):
    if os.path.exists(file):
        with open(file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

bin_str = get_base64('background.jpg')

st.markdown(f"""
<style>
    /* 1. HIDE ALL TOP-RIGHT ICONS (GITHUB, SHARE, ETC.) */
    [data-testid="stHeader"] {{
        background: transparent !important;
    }}
    header[data-testid="stHeader"] > div:first-child {{
        display: none !important;
    }}
    
    /* 2. BRING BACK & STYLE THE COLLAPSE BUTTON (The '<<' and '>>' button) */
    [data-testid="stSidebarCollapseButton"] {{
        visibility: visible !important;
        display: block !important;
        color: #FF6D00 !important;
        background: rgba(0,0,0,0.8) !important;
        border: 2px solid #FF6D00 !important;
        border-radius: 8px !important;
        z-index: 999999 !important;
        opacity: 1 !important; /* Made visible again */
    }}
    
    /* 3. REMOVE FOOTER & DEPLOY BUTTON */
    footer, .stDeployButton, [data-testid="stStatusWidget"] {{
        display: none !important;
    }}

    /* 4. SIDEBAR DESIGN */
    [data-testid="stSidebar"] {{
        background-color: rgba(10, 10, 10, 0.98) !important;
        border-right: 2px solid #FF6D00;
        min-width: 320px !important;
    }}

    /* 5. MAIN APP DESIGN */
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), 
                    url("data:image/jpeg;base64,{bin_str if bin_str else ''}");
        background-size: cover;
        background-attachment: fixed;
    }}
    
    .main-title {{
        font-weight: 900; color: #FF6D00; text-align: center; font-size: 5.5rem;
        text-shadow: 0px 0px 35px rgba(255, 109, 0, 0.8);
        margin-top: -60px;
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

# --- 2. DATABASE & ELABORATE LEGAL DOCS ---
DB_FILE = "gobidas_db.json"
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                return json.load(f)
        except: pass
    return {"users": {}, "history": {}}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

if "db" not in st.session_state:
    st.session_state.db = load_db()

def show_legal():
    st.markdown("## 📜 GOVERNANCE, PRIVACY & LEGAL PROTOCOLS (Privacy & Terms")
    
    st.error("### **ARTICLE I: USER ACKNOWLEDGMENT OF BETA STATUS**")
    st.write("""
    **** Gobidas is currently in a pre-release Beta phase. By utilizing this interface, the user acknowledges that the software is provided without warranty of any kind. 
    **** AI responses are generated via probabilistic models. Users must independently verify any information provided by the system before taking action.
    """)

    st.markdown("### **ARTICLE II: LIMITATION OF LIABILITY & INDEMNITY CLAUSE**")
    st.write("""
    **** The developer acts only as a provider of the Graphical User Interface (GUI). The underlying intelligence is provided by Meta (Llama) and processed by Groq Cloud. 
    **** The developer shall not be held responsible for any loss, injury, or legal dispute resulting from AI hallucinations, biased outputs, or data transmission errors.
    **** The user agrees to fully indemnify and hold the developer harmless from any and all claims, including third-party legal actions, stemming from the user's activities within the app.
    """)

    st.markdown("### **ARTICLE III: DATA SOVEREIGNTY & PRIVACY PRESERVATION**")
    st.write("""
    **** All user credentials and conversational logs are stored exclusively in a local JSON database on the hosting environment. No personal data is harvested for marketing or secondary monetization.
    **** To ensure maximum security, the system enforces a strict 30-day (720-hour) data retention window. Histories exceeding this duration are automatically and permanently purged.
    **** All external communications with inference engines are secured via industry-standard TLS encryption.
    """)

# --- 3. LOGIN / SIGN UP FLOW ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas BETA</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.8, 1])
    with c2:
        mode = st.radio("GATEWAY ACCESS", ["LOG IN", "SIGN UP"], horizontal=True)
        u = st.text_input("USERNAME")
        p = st.text_input("PASSWORD", type="password")
        agree = st.checkbox("I confirm agreement to the Privacy & Terms")
        
        if st.button("ENTER SYSTEM", disabled=not agree):
            if mode == "LOG IN":
                if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.messages = []
                    st.rerun()
                else: st.error("ACCESS DENIED: INCORRECT CREDENTIALS")
            else:
                if u and p:
                    st.session_state.db["users"][u] = p
                    st.session_state.db["history"][u] = []
                    save_db(st.session_state.db)
                    st.success("CREDENTIALS REGISTERED. PROCEED TO LOG IN.")
        st.divider()
        with st.expander("REVIEW FULL LEGAL DOCUMENTATION"): show_legal()
    st.stop()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title(f"@{st.session_state.user}")
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    
    img_file = st.file_uploader("Add images:", type=['png', 'jpg', 'jpeg'])
    
    st.divider()
    st.write("### Chats")
    hist_list = st.session_state.db["history"].get(st.session_state.user, [])
    for i in range(len(hist_list)-1, -1, -1):
        chat = hist_list[i]
        c_chat, c_del = st.columns([0.8, 0.2])
        with c_chat:
            if st.button(chat.get('name', 'Session'), key=f"open_{i}"):
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
    if st.button("⚙️ settings"):
        st.session_state.show_settings = not st.session_state.get("show_settings", False)
    if st.session_state.get("show_settings"):
        if st.button("Log out"):
            del st.session_state.user
            st.rerun()
        with st.expander("Privacy & Terms"): show_legal()

# --- 5. CHAT ENGINE ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Ask Gobidas BETA"):
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
            
            # Auto-Save
            history = st.session_state.db["history"].get(st.session_state.user, [])
            chat_title = prompt[:22] + "..." if len(prompt) > 22 else prompt
            chat_entry = {"name": chat_title, "msgs": st.session_state.messages, "ts": time.time()}
            if st.session_state.get("active_idx") is None:
                history.append(chat_entry); st.session_state.active_idx = len(history) - 1
            else:
                history[st.session_state.active_idx] = chat_entry
            st.session_state.db["history"][st.session_state.user] = history
            save_db(st.session_state.db)
        except Exception as e: st.error(f"ENGINE ERROR: {e}")
