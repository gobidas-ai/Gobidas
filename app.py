import streamlit as st
from groq import Groq
import json, os, base64, io, time
from PIL import Image
import streamlit.components.v1 as components

# --- 1. CONFIG & SUPER STEALTH CSS ---
st.set_page_config(page_title="Gobidas Beta", layout="wide", initial_sidebar_state="expanded")

def get_base64(file):
    if os.path.exists(file):
        with open(file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

bin_str = get_base64('background.jpg')

st.markdown(f"""
<style>
    /* 1. HIDE THE HEADER CONTENT (GITHUB, MANAGE APP, ETC) BUT KEEP THE BAR FOR THE BUTTON */
    [data-testid="stHeader"] {{
        background: rgba(0,0,0,0) !important;
        color: rgba(0,0,0,0) !important;
    }}
    /* Hide specific header icons like GitHub and the '...' menu */
    header[data-testid="stHeader"] div:first-child {{
        display: none !important;
    }}
    
    /* 2. FORCE THE SIDEBAR BUTTON TO BE VISIBLE AND ORANGE */
    [data-testid="stSidebarCollapseButton"] {{
        visibility: visible !important;
        display: block !important;
        color: #FF6D00 !important;
        background: rgba(0,0,0,0.5) !important;
        border-radius: 5px !important;
        margin-left: 10px !important;
    }}

    /* 3. APP DESIGN */
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), 
                    url("data:image/jpeg;base64,{bin_str if bin_str else ''}");
        background-size: cover;
    }}
    .main-title {{
        font-weight: 900; color: #FF6D00; text-align: center; font-size: 4.5rem;
        text-shadow: 0px 0px 20px rgba(255, 109, 0, 0.5);
    }}
    [data-testid="stSidebar"] {{
        background-color: rgba(10, 10, 10, 0.98) !important;
        border-right: 2px solid #FF6D00;
    }}
    .stButton>button {{
        width: 100%; border-radius: 10px; border: 1px solid #FF6D00 !important;
        color: white !important; background: transparent;
    }}
    .stButton>button:hover {{
        background: #FF6D00 !important; color: black !important;
    }}
    
    /* Hide 'Deploy' and 'Manage' specifically */
    .stDeployButton, footer, [data-testid="stStatusWidget"] {{
        display: none !important;
    }}
</style>
""", unsafe_allow_html=True)

# Kill "Manage App" via JS as a backup
components.html("<script>setInterval(()=>{window.parent.document.querySelectorAll('button').forEach(b=>{if(b.innerText.includes('Manage app'))b.parentElement.style.display='none'})},500)</script>", height=0)

# --- 2. DATABASE & LEGAL ---
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

def show_legal():
    st.subheader("Terms & Privacy (BETA)")
    st.warning("Gobidas AI is in Beta. You may experience errors.")
    st.write("**Liability:** Developer is NOT responsible for AI output. Responsibility lies with creators (Meta/Groq).")
    st.write("**Privacy:** Data is stored locally for 30 days then deleted.")

# --- 3. THE SIDEBAR (ALWAYS DECLARED) ---
# We define it here so Streamlit allocates space for it immediately.
with st.sidebar:
    if "user" in st.session_state:
        st.title(f"Hi, {st.session_state.user}")
        if st.button("➕ New Chat"):
            st.session_state.messages = []
            st.session_state.active_idx = None
            st.rerun()
        
        st.divider()
        img_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
        
        st.divider()
        st.write("History (30-day limit)")
        user_history = st.session_state.db["history"].get(st.session_state.user, [])
        for i, chat in enumerate(user_history):
            if st.button(f"Chat {i+1}: {chat.get('name', '...')}", key=f"h_{i}"):
                st.session_state.messages = chat.get("msgs", [])
                st.session_state.active_idx = i
                st.rerun()

        st.divider()
        if st.button("⚙️ Settings"):
            st.session_state.show_settings = not st.session_state.get("show_settings", False)
        
        if st.session_state.get("show_settings"):
            if st.button("Logout"):
                del st.session_state.user
                st.rerun()
            with st.expander("Legal Info"):
                show_legal()
    else:
        st.info("Please log in to use chat features.")

# --- 4. LOGIN LOGIC ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.8, 1])
    with c2:
        mode = st.radio(" ", ["Log In", "Sign Up"], horizontal=True)
        u = st.text_input("Name")
        p = st.text_input("Password", type="password")
        st.caption("By using this AI you accept our terms.")
        agree = st.checkbox("I agree to the Terms and Privacy Policy")
        
        if st.button("Enter", disabled=not agree):
            if mode == "Log In":
                if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.messages = []
                    st.rerun()
                else: st.error("Wrong info.")
            else:
                if u and p:
                    st.session_state.db["users"][u] = p
                    st.session_state.db["history"][u] = []
                    save_db(st.session_state.db)
                    st.success("Account made! Switch to Log In.")
        with st.expander("See Terms & Privacy"):
            show_legal()
    st.stop()

# --- 5. CHAT ENGINE ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Ask Gobidas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        # Attempting to access img_file from sidebar scope
        try:
            if img_file: st.image(img_file, width=300)
        except: pass

    with st.chat_message("assistant"):
        try:
            # Check for image presence safely
            try: has_img = img_file is not None
            except: has_img = False

            if has_img:
                img = Image.open(img_file).convert("RGB")
                img.thumbnail((800, 800)); buf = io.BytesIO()
                img.save(buf, format="JPEG"); b64 = base64.encode(buf.getvalue()).decode('utf-8')
                res = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=[{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}]
                )
            else:
                res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=st.session_state.messages)
            
            ans = res.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            # Save History
            hist = st.session_state.db["history"].get(st.session_state.user, [])
            chat_data = {"name": prompt[:15], "msgs": st.session_state.messages, "ts": time.time()}
            if st.session_state.get("active_idx") is None:
                hist.append(chat_data); st.session_state.active_idx = len(hist) - 1
            else:
                hist[st.session_state.active_idx] = chat_data
            st.session_state.db["history"][st.session_state.user] = hist
            save_db(st.session_state.db)
        except Exception as e:
            st.error(f"Error: {e}")
        
