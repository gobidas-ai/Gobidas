import streamlit as st
from groq import Groq
import json, os, base64, io
from PIL import Image
import streamlit.components.v1 as components

# --- 1. UI & AGGRESSIVE STEALTH STYLE ---
st.set_page_config(page_title="Gobidas Beta", layout="wide")

def get_base64(file):
    with open(file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

try:
    bin_str = get_base64('background.jpg')
    # Aggressive CSS to hide everything
    st.markdown(f"""
    <style>
    /* HIDE TOP NAV, MENU, GITHUB, AND DEPLOY BUTTONS */
    header, [data-testid="stHeader"] {{ visibility: hidden !important; display: none !important; }}
    #MainMenu {{ visibility: hidden !important; }}
    .stDeployButton {{ display: none !important; }}
    [data-testid="stToolbar"] {{ display: none !important; }}
    
    /* HIDE BOTTOM "MANAGE APP" AND STATUS BAR */
    footer {{ visibility: hidden !important; display: none !important; }}
    [data-testid="stStatusWidget"] {{ display: none !important; }}
    [data-testid="stManageAppButton"] {{ display: none !important; }}
    
    /* TARGET FLOATING OVERLAYS (MANAGE APP WRAPPERS) */
    .viewerBadge_container__1QS13 {{ display: none !important; }}
    div[class^="viewerBadge"] {{ display: none !important; }}
    
    /* CUSTOM INTERFACE DESIGN */
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.85)), 
                    url("data:image/jpeg;base64,{bin_str}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    [data-testid="stSidebar"] {{
        background: rgba(0, 0, 0, 0.9) !important;
        backdrop-filter: blur(25px);
        border-right: 2px solid #FF6D00;
    }}
    .main-title {{
        font-weight: 900;
        color: #FF6D00;
        text-align: center;
        font-size: 5rem;
        text-shadow: 0px 0px 25px rgba(255, 109, 0, 0.6);
    }}
    .stButton>button {{
        width: 100%;
        border-radius: 12px;
        background: transparent !important;
        color: white !important;
        border: 2px solid #FF6D00 !important;
        font-weight: 600;
        transition: 0.3s all ease-in-out;
    }}
    .stButton>button:hover {{
        background: #FF6D00 !important;
        box-shadow: 0px 0px 30px rgba(255, 109, 0, 0.9);
        color: black !important;
    }}
    .stChatMessage {{
        background: rgba(255, 255, 255, 0.07) !important;
        backdrop-filter: blur(15px);
        border-radius: 20px !important;
        border: 1px solid rgba(255, 109, 0, 0.3) !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    # JavaScript to kill the "Manage App" button if it's in an iframe or shadow root
    components.html("""
        <script>
        const observer = new MutationObserver((mutations) => {
            const buttons = window.parent.document.querySelectorAll('button');
            buttons.forEach(btn => {
                if (btn.innerText.includes('Manage app')) {
                    btn.parentElement.style.display = 'none';
                }
            });
            const toolbars = window.parent.document.querySelectorAll('[data-testid="stToolbar"]');
            toolbars.forEach(t => t.style.display = 'none');
        });
        observer.observe(window.parent.document.body, { childList: true, subtree: true });
        </script>
    """, height=0)
except:
    st.error("Missing background.jpg")

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

# --- 3. LOGIN ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        mode = st.radio(" ", ["Log In", "Sign Up"], horizontal=True)
        u = st.text_input("Name")
        p = st.text_input("Password", type="password")
        if st.button("Enter"):
            if mode == "Log In":
                if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.messages = []
                    st.rerun()
            else:
                if u and p:
                    st.session_state.db["users"][u] = p
                    st.session_state.db["history"][u] = []
                    save_db(st.session_state.db)
                    st.success("Account created! Please Log In.")
    st.stop()

# --- 4. ENGINE ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

with st.sidebar:
    st.markdown(f"### Welcome, {st.session_state.user}")
    if st.button("New Chat"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    
    st.divider()
    img_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
    
    st.divider()
    st.write("History")
    logs = st.session_state.db["history"].get(st.session_state.user, [])
    for i, log in enumerate(logs):
        name = log.get("name", f"Chat {i+1}")
        if st.button(f" {name}", key=f"h_{i}"):
            st.session_state.messages = log.get("msgs", [])
            st.session_state.active_idx = i
            st.rerun()

# --- 5. CHAT ---
st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Ask Gobidas..."):
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
                b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                
                # --- ACTUAL WORKING VISION MODEL (NOT 3.2) ---
                res = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
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
            
            # Save History
            hist = st.session_state.db["history"].get(st.session_state.user, [])
            if st.session_state.get("active_idx") is None:
                summary = (prompt[:30] + '...') if len(prompt) > 30 else prompt
                hist.append({"name": summary, "msgs": st.session_state.messages})
                st.session_state.db["history"][st.session_state.user] = hist
                st.session_state.active_idx = len(hist) - 1
            else:
                idx = st.session_state.active_idx
                st.session_state.db["history"][st.session_state.user][idx]["msgs"] = st.session_state.messages
            save_db(st.session_state.db)
            
        except Exception as e:
            st.error(f"Error: {e}")
            
