import streamlit as st
from groq import Groq
import json, os, base64, io, time
from PIL import Image

# --- 1. UI & DARK MODE ---
st.set_page_config(page_title="Gobidas Beta", layout="wide", initial_sidebar_state="expanded")

def get_base64_img(file_path):
    try:
        with open(file_path, 'rb') as f: return base64.b64encode(f.read()).decode()
    except: return ""

bin_str = get_base64_img('background.jpg')

st.markdown(f"""
<style>
    html, body, [data-testid="stAppViewContainer"] {{ color-scheme: dark !important; }}
    header[data-testid="stHeader"] {{ visibility: visible !important; background: rgba(0,0,0,0.5) !important; }}
    .stApp a[href*="github.com"], .stApp [data-testid="stHeader"] svg[viewBox*="github"] {{ display: none !important; }}
    footer, [data-testid="stStatusWidget"], [data-testid="stManageAppButton"] {{ display: none !important; }}
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.9)), 
                    url("data:image/jpeg;base64,{bin_str}");
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    [data-testid="stSidebar"] {{ background: rgba(0, 0, 0, 0.95) !important; border-right: 2px solid #FF6D00; }}
    .main-title {{ font-weight: 900; color: #FF6D00; text-align: center; font-size: 5rem; text-shadow: 0px 0px 20px rgba(255,109,0,0.5); }}
    .stButton>button {{ width: 100%; border-radius: 12px; border: 2px solid #FF6D00 !important; color: white !important; background: transparent !important; }}
    .legal-box {{ font-size: 0.9rem; color: #ddd; background: rgba(0,0,0,0.8); padding: 35px; border-radius: 12px; border: 1px solid #FF6D00; line-height: 1.8; height: 600px; overflow-y: scroll; }}
</style>
""", unsafe_allow_html=True)

# --- 2. STORAGE ---
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

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("Settings")
    if "user" in st.session_state:
        st.write(f"Logged in: **{st.session_state.user}**")
        if st.button("New Chat"):
            st.session_state.messages = []
            st.session_state.active_idx = None
            st.rerun()
        st.divider()
        img_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
        st.divider()
        st.subheader("History")
        logs = st.session_state.db["history"].get(st.session_state.user, [])
        for i, log in enumerate(reversed(logs)):
            if st.button(f"{log.get('name', 'Chat')[:20]}", key=f"h_{i}"):
                st.session_state.messages = log.get("msgs", [])
                st.session_state.active_idx = len(logs) - 1 - i
                st.rerun()
        if st.button("Log out"):
            del st.session_state.user
            st.rerun()

# --- 4. LOGIN & TERMS ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    st.info("Welcome! Currently our website is still in beta (not in the final version yet) so you might experience loss of data (losing your user). Thank you for using our AI and we hope you will like Gobidas! Have fun!")
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        mode = st.radio(" ", ["Log in", "Sign up"], horizontal=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        st.markdown("### Privacy Policy and Terms of Use")
        st.markdown("""<div class='legal-box'>
            <strong>ARTICLE 1: AGREEMENT</strong><br>By using Gobidas, you agree to these terms.
            <br><br><strong>ARTICLE 2: BETA STAGE</strong><br>This is a BETA version. Data loss can happen.
            <br><br><strong>ARTICLE 3: DATA</strong><br>We save your username and history locally. We do not sell data.
            <br><br><strong>ARTICLE 4: PROHIBITED USE</strong><br>No illegal acts, harassment, or hacking.
            <br><br><strong>ARTICLE 5: AI ACCURACY</strong><br>AI can be wrong. Verify all info.
            <br><br><strong>ARTICLE 6: RETENTION</strong><br>Chats are cleared every 30 days. Inactive users may be removed.
            <br><br><strong>ARTICLE 7: LIABILITY</strong><br>We are not responsible for AI output or lost data.
        </div>""", unsafe_allow_html=True)
        if st.button("Enter", disabled=not st.checkbox("I agree to the terms and policy")):
            if mode == "Log in":
                if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.messages = []
                    st.rerun()
                else: st.error("Wrong details.")
            else:
                if u and p:
                    st.session_state.db["users"][u] = p
                    st.session_state.db["history"][u] = []
                    save_db(st.session_state.db)
                    st.success("Made! Now Log in.")
    st.stop()

# --- 5. CHAT (VISION ENABLED - NO LLAMA 3.2) ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
st.markdown("<h1 class='main-title'>Gobidas AI</h1>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "image_b64" in msg:
            st.image(f"data:image/jpeg;base64,{msg['image_b64']}", width=400)

if prompt := st.chat_input("Message Gobidas..."):
    msg_entry = {"role": "user", "content": prompt}
    b64_str = None
    if img_file:
        b64_str = base64.b64encode(img_file.getvalue()).decode('utf-8')
        msg_entry["image_b64"] = b64_str

    st.session_state.messages.append(msg_entry)
    with st.chat_message("user"):
        st.markdown(prompt)
        if b64_str: st.image(img_file, width=400)

    with st.chat_message("assistant"):
        try:
            if b64_str:
                # LLAMA-3-70B-8192 (Multi-modal enabled version on Groq)
                res = client.chat.completions.create(
                    model="llama-3.1-70b-versatile",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_str}"}}
                        ]
                    }]
                )
            else:
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                )
            
            ans = res.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            # Save History
            hist = st.session_state.db["history"].get(st.session_state.user, [])
            chat_data = {"name": prompt[:20], "msgs": st.session_state.messages}
            if st.session_state.get("active_idx") is None:
                hist.append(chat_data)
                st.session_state.active_idx = len(hist) - 1
            else:
                hist[st.session_state.active_idx] = chat_data
            st.session_state.db["history"][st.session_state.user] = hist
            save_db(st.session_state.db)
        except Exception as e:
            st.error(f"Error: {e}")
