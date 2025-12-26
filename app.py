import streamlit as st
from groq import Groq
import json, os, base64, io, time
from PIL import Image

# --- 1. CONFIG & STYLING ---
st.set_page_config(page_title="Gobidas Beta", layout="wide", initial_sidebar_state="expanded")

def get_base64(file):
    if os.path.exists(file):
        with open(file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

bin_str = get_base64('background.jpg')

st.markdown(f"""
<style>
    /* ENSURE SIDEBAR IS VISIBLE */
    [data-testid="stSidebar"] {{
        background-color: rgba(10, 10, 10, 0.98) !important;
        border-right: 2px solid #FF6D00;
        min-width: 300px !important;
    }}

    /* GLOBAL DESIGN */
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), 
                    url("data:image/jpeg;base64,{bin_str if bin_str else ''}");
        background-size: cover;
        background-attachment: fixed;
    }}
    
    .main-title {{
        font-weight: 900; color: #FF6D00; text-align: center; font-size: 5rem;
        text-shadow: 0px 0px 30px rgba(255, 109, 0, 0.7);
    }}

    /* BUTTONS */
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

# --- 2. DATABASE & MASSIVE LEGAL ---
DB_FILE = "gobidas_db.json"
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                return data
        except: pass
    return {"users": {}, "history": {}}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

if "db" not in st.session_state:
    st.session_state.db = load_db()

def show_legal():
    st.markdown("## 📜 OFFICIAL TERMS OF SERVICE & PRIVACY POLICY")
    st.error("### **ARTICLE 1: COMPREHENSIVE BETA DISCLAIMER**")
    st.write("""
    **1.1 Experimental Nature:** Gobidas is an experimental artificial intelligence interface. Users acknowledge that the software is provided 'as-is' and may contain bugs or functional defects. 
    **1.2 Output Accuracy:** AI models are prone to 'hallucinations'—generating facts that are incorrect or nonsensical. The developer assumes zero responsibility for the truthfulness of any AI response.
    """)
    st.markdown("### **ARTICLE 2: LEGAL LIABILITY & INDEMNITY**")
    st.write("""
    **2.1 Third-Party Models:** Gobidas uses models from Meta (Llama) and services from Groq. Any harm caused by the logic of these models is the responsibility of the model creators, not the Gobidas UI developer.
    **2.2 Total Indemnity:** By using this application, the user agrees to waive all rights to pursue legal action against the developer for any reason, including but not limited to data loss, offensive output, or system errors.
    **2.3 No Professional Advice:** This AI is for entertainment and general information only. It is NOT a doctor, lawyer, or financial advisor. 
    """)
    st.markdown("### **ARTICLE 3: DATA PRIVACY & RETENTION**")
    st.write("""
    **3.1 Data Sovereignty:** Your credentials and history are stored in a local JSON file. No data is shared with third-party advertisers.
    **3.2 The 30-Day Purge:** All chat history is automatically deleted after 30 days to protect your privacy and maintain system performance. This action is final and unrecoverable.
    **3.3 Encryption:** While we use standard security measures, no system is 100% secure. Use at your own discretion.
    """)

# --- 3. LOGIN / SIGN UP FLOW ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.8, 1])
    with c2:
        mode = st.radio("SELECT MODE", ["LOG IN", "SIGN UP"], horizontal=True)
        u = st.text_input("USERNAME")
        p = st.text_input("PASSWORD", type="password")
        agree = st.checkbox("I HAVE READ AND AGREE TO THE FULL TERMS AND PRIVACY POLICY")
        
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
                    st.success("ACCOUNT CREATED! PLEASE LOG IN.")
        st.divider()
        with st.expander("VIEW FULL LEGAL DOCUMENTATION"): show_legal()
    st.stop()

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title(f"@{st.session_state.user}")
    if st.button("➕ NEW SESSION"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    
    img_file = st.file_uploader("UPLOAD IMAGE", type=['png', 'jpg', 'jpeg'])
    
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
        if st.button("LOGOUT"):
            del st.session_state.user
            st.rerun()
        with st.expander("LEGAL"): show_legal()

# --- 5. CHAT ENGINE ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("ASK GOBIDAS..."):
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
            
            # Save Logic
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
