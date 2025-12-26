import streamlit as st
from groq import Groq
import json, os, base64, io, time
from PIL import Image
import streamlit.components.v1 as components

# --- 1. UI & REFINED STEALTH STYLE ---
st.set_page_config(page_title="Gobidas Beta", layout="wide")

def get_base64(file):
    with open(file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

try:
    bin_str = get_base64('background.jpg')
    st.markdown(f"""
    <style>
    /* HIDE BRANDING BUT KEEP SIDEBAR TOGGLE */
    [data-testid="stHeader"] {{ background: transparent !important; }}
    .stDeployButton, [data-testid="stToolbar"], footer, 
    [data-testid="stStatusWidget"], [data-testid="stManageAppButton"] {{
        visibility: hidden !important; display: none !important;
    }}
    
    [data-testid="stSidebarCollapseButton"] {{
        visibility: visible !important;
        display: block !important;
        color: #FF6D00 !important;
    }}

    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.85)), 
                    url("data:image/jpeg;base64,{bin_str}");
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    [data-testid="stSidebar"] {{
        background: rgba(0, 0, 0, 0.9) !important;
        backdrop-filter: blur(25px); border-right: 2px solid #FF6D00;
    }}
    .main-title {{
        font-weight: 900; color: #FF6D00; text-align: center; font-size: 5rem;
        text-shadow: 0px 0px 25px rgba(255, 109, 0, 0.6);
    }}
    .stButton>button {{
        width: 100%; border-radius: 12px; background: transparent !important;
        color: white !important; border: 2px solid #FF6D00 !important;
        font-weight: 600; transition: 0.3s all ease-in-out;
    }}
    .stButton>button:hover:not(:disabled) {{
        background: #FF6D00 !important; box-shadow: 0px 0px 30px rgba(255, 109, 0, 0.9);
        color: black !important;
    }}
    .stChatMessage {{
        background: rgba(255, 255, 255, 0.07) !important; backdrop-filter: blur(15px);
        border-radius: 20px !important; border: 1px solid rgba(255, 109, 0, 0.3) !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    components.html("""
        <script>
        const observer = new MutationObserver(() => {
            window.parent.document.querySelectorAll('button').forEach(btn => {
                if (btn.innerText.includes('Manage app')) btn.parentElement.style.display = 'none';
            });
        });
        observer.observe(window.parent.document.body, { childList: true, subtree: true });
        </script>
    """, height=0)
except:
    st.error("Missing background.jpg")

# --- 2. STORAGE & AUTO-DELETE ---
DB_FILE = "gobidas_db.json"
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: 
                data = json.load(f)
                now = time.time()
                cutoff = 30 * 24 * 60 * 60
                for user in data.get("history", {}):
                    data["history"][user] = [c for c in data["history"][user] if (now - c.get("timestamp", now)) < cutoff]
                return data
        except: pass
    return {"users": {}, "history": {}}

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

if "db" not in st.session_state:
    st.session_state.db = load_db()

def show_legal_content():
    st.markdown("## Terms of Service & Privacy Policy")
    st.warning("**BETA NOTICE:** Gobidas AI is in beta. Errors may occur.")
    st.markdown("### Liability")
    st.write("Developer not responsible for AI output. Responsibility lies with Meta/Groq.")
    st.markdown("### Privacy")
    st.write("Data stored for 30 days locally then deleted.")

# --- 3. LOGIN LOGIC ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        mode = st.radio(" ", ["Log In", "Sign Up"], horizontal=True)
        u = st.text_input("Name")
        p = st.text_input("Password", type="password")
        st.markdown("<p style='text-align: center; font-size: 0.8rem; color: #bbb;'>By using our AI you accept our terms</p>", unsafe_allow_html=True)
        agree = st.checkbox("I agree to the Terms and Privacy Policy")
        
        if st.button("Enter", disabled=not agree):
            if mode == "Log In":
                if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.messages = []
                    st.rerun()
                else: st.error("Invalid credentials")
            else:
                if u and p:
                    st.session_state.db["users"][u] = p
                    st.session_state.db["history"][u] = []
                    save_db(st.session_state.db)
                    st.success("Account created!")
        with st.expander("See our terms and privacy"):
            show_legal_content()
    st.stop()

# --- 4. SIDEBAR (POST-LOGIN) ---
if "show_settings" not in st.session_state: st.session_state.show_settings = False

with st.sidebar:
    st.markdown(f"### {st.session_state.user}")
    
    if st.button("New Chat"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    
    img_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
    
    st.divider()
    st.write("History (30-day limit)")
    logs = st.session_state.db["history"].get(st.session_state.user, [])
    for i, log in enumerate(logs):
        if st.button(f" {log.get('name', 'Chat')}", key=f"h_{i}"):
            st.session_state.messages = log.get("msgs", [])
            st.session_state.active_idx = i
            st.rerun()
            
    st.divider()
    if st.button("⚙️ Settings"):
        st.session_state.show_settings = not st.session_state.show_settings
    
    if st.session_state.show_settings:
        with st.expander("Privacy and Terms"):
            show_legal_content()
        if st.button("Logout"):
            del st.session_state.user
            st.rerun()

# --- 5. CHAT INTERFACE ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
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
            chat_data = {"name": prompt[:20], "msgs": st.session_state.messages, "timestamp": time.time()}
            if st.session_state.get("active_idx") is None:
                hist.append(chat_data)
                st.session_state.db["history"][st.session_state.user] = hist
                st.session_state.active_idx = len(hist) - 1
            else:
                st.session_state.db["history"][st.session_state.user][st.session_state.active_idx] = chat_data
            save_db(st.session_state.db)
        except Exception as e:
            st.error(f"Error: {e}")
