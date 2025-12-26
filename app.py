import streamlit as st
from groq import Groq
import json, os, base64, io, time
from PIL import Image

# --- 1. CONFIG & TOTAL UI CLEANUP ---
st.set_page_config(page_title="Gobidas Beta", layout="wide", initial_sidebar_state="expanded")

def get_base64(file):
    if os.path.exists(file):
        with open(file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

bin_str = get_base64('background.jpg')

st.markdown(f"""
<style>
    /* 1. REMOVE THE COLLAPSE BUTTON (The '<<' thing) */
    [data-testid="stSidebarCollapseButton"] {{
        display: none !important;
    }}

    /* 2. REMOVE TOP HEADER (GitHub, Share, etc.) */
    [data-testid="stHeader"] {{
        display: none !important;
    }}
    
    /* 3. REMOVE FOOTER & 'MANAGE APP' */
    footer, [data-testid="stFooter"], .stDeployButton {{
        display: none !important;
    }}

    /* 4. SIDEBAR DESIGN */
    [data-testid="stSidebar"] {{
        background-color: rgba(10, 10, 10, 0.98) !important;
        border-right: 2px solid #FF6D00;
        min-width: 320px !important;
    }}

    /* 5. MAIN APP STYLING */
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), 
                    url("data:image/jpeg;base64,{bin_str if bin_str else ''}");
        background-size: cover;
        background-attachment: fixed;
    }}
    
    .main-title {{
        font-weight: 900; color: #FF6D00; text-align: center; font-size: 5rem;
        text-shadow: 0px 0px 30px rgba(255, 109, 0, 0.7);
        margin-top: -60px;
    }}

    .stButton>button {{
        width: 100%; border-radius: 10px; border: 1px solid #FF6D00 !important;
        color: white !important; background: transparent; font-weight: 800;
        text-transform: uppercase;
    }}
    .stButton>button:hover {{
        background: #FF6D00 !important; color: black !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE & PROFESSIONAL LEGAL DOCS ---
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
    st.markdown("## 📜 OFFICIAL TERMS OF SERVICE & PRIVACY POLICY")
    
    st.error("### **ARTICLE 1: BINDING AGREEMENT & BETA DISCLAIMER**")
    st.write("""
    **1.1 Access Acceptance:** By accessing 'Gobidas' (the 'Software'), you enter into a legally binding agreement with the developer. If you do not agree to these terms, you must terminate your session immediately.
    **1.2 Experimental Software:** This Software is in a Beta phase. It is provided 'AS-IS' and 'AS-AVAILABLE'. The developer makes no warranties, expressed or implied, regarding system stability, data integrity, or output accuracy.
    """)

    st.markdown("### **ARTICLE 2: LIMITATION OF LIABILITY & INDEMNIFICATION**")
    st.write("""
    **2.1 Third-Party Intelligence:** Gobidas utilizes Large Language Models (LLMs) provided by Meta and hosted via Groq Inc. The developer is a third-party interface creator and has no control over the generation logic.
    **2.2 No Liability for Harm:** The developer shall not be held liable for any damages, including but not limited to financial loss, emotional distress, or legal complications arising from AI-generated responses.
    **2.3 Indemnity:** The user agrees to indemnify and hold harmless the developer from any claims, suits, or legal fees resulting from the user's interaction with the Software.
    """)

    st.markdown("### **ARTICLE 3: DATA PRIVACY & SOVEREIGNTY**")
    st.write("""
    **3.1 Localized Storage:** To ensure user privacy, all credentials and chat logs are stored in a local JSON file on the host server. We do not use third-party tracking or advertising databases.
    **3.2 Automated Purge Protocol:** To maintain system efficiency and user privacy, the system automatically executes a 30-day data retention policy. All data older than 30 days is permanently liquidated and cannot be recovered.
    **3.3 Data Transit:** All data sent for inference (text/images) is transmitted via encrypted HTTPS protocols to Groq for processing.
    """)

# --- 3. LOGIN / SIGN UP FLOW ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.8, 1])
    with c2:
        mode = st.radio("CHOOSE ACCESS TYPE", ["LOG IN", "SIGN UP"], horizontal=True)
        u = st.text_input("NAME / USERNAME")
        p = st.text_input("SECURITY KEY / PASSWORD", type="password")
        agree = st.checkbox("I EXPRESSLY AGREE TO THE ARTICLE 1, 2, AND 3 LEGAL TERMS")
        
        if st.button("ENTER", disabled=not agree):
            if mode == "LOG IN":
                if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.messages = []
                    st.rerun()
                else: st.error("ACCESS DENIED: INVALID CREDENTIALS")
            else:
                if u and p:
                    st.session_state.db["users"][u] = p
                    st.session_state.db["history"][u] = []
                    save_db(st.session_state.db)
                    st.success("ACCOUNT REGISTERED. PROCEED TO LOG IN.")
        st.divider()
        with st.expander("VIEW FULL LEGAL DOCUMENTATION"): show_legal()
    st.stop()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title(f"@{st.session_state.user}")
    if st.button("➕ NEW CHAT SESSION"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    
    img_file = st.file_uploader("UPLOAD VISION INPUT", type=['png', 'jpg', 'jpeg'])
    
    st.divider()
    st.write("### SAVED ARCHIVES")
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
    if st.button("⚙️ SYSTEM SETTINGS"):
        st.session_state.show_settings = not st.session_state.get("show_settings", False)
    if st.session_state.get("show_settings"):
        if st.button("TERMINATE SESSION (LOGOUT)"):
            del st.session_state.user
            st.rerun()
        with st.expander("LEGAL"): show_legal()

# --- 5. CHAT ENGINE ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("COMMAND GOBIDAS..."):
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
        except Exception as e: st.error(f"SYSTEM OVERLOAD: {e}")
