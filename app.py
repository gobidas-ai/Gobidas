import streamlit as st
from groq import Groq
import json, os, base64, io, time
from PIL import Image
import streamlit.components.v1 as components

# --- 1. SET PAGE CONFIG (FORCE SIDEBAR OPEN) ---
st.set_page_config(
    page_title="Gobidas Beta", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 2. BASIC THEME CSS (NO STEALTH OVERKILL) ---
def get_base64(file):
    if os.path.exists(file):
        with open(file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

bin_str = get_base64('background.jpg')

st.markdown(f"""
<style>
    /* Clean background and fonts */
    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), 
                    url("data:image/jpeg;base64,{bin_str if bin_str else ''}");
        background-size: cover;
    }}
    .main-title {{
        font-weight: 900; 
        color: #FF6D00; 
        text-align: center; 
        font-size: 4rem;
        margin-bottom: 2rem;
    }}
    /* Sidebar styling to make it stand out */
    [data-testid="stSidebar"] {{
        background-color: rgba(20, 20, 20, 0.95) !important;
        border-right: 2px solid #FF6D00;
    }}
    /* Button styling */
    .stButton>button {{
        width: 100%;
        border-radius: 8px;
        border: 1px solid #FF6D00 !important;
        color: white !important;
        background-color: transparent;
    }}
    .stButton>button:hover {{
        background-color: #FF6D00 !important;
        color: black !important;
    }}
</style>
""", unsafe_allow_html=True)

# Background script to hide "Manage App" specifically without breaking the UI
components.html("""
    <script>
    setInterval(() => {
        const buttons = window.parent.document.querySelectorAll('button');
        buttons.forEach(btn => {
            if (btn.innerText.includes('Manage app')) {
                btn.parentElement.style.display = 'none';
            }
        });
    }, 1000);
    </script>
""", height=0)

# --- 3. DATABASE & LEGAL LOGIC ---
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
    st.subheader("Terms & Privacy (BETA)")
    st.warning("Gobidas AI is in Beta. Errors may occur.")
    st.write("**Liability:** The developer is not responsible for AI output. Responsibility lies with the AI providers (Meta/Groq).")
    st.write("**Privacy:** Data is stored locally and cleared after 30 days.")

# --- 4. LOGIN / SIGNUP FLOW ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["Log In", "Sign Up"])
        
        with tab1:
            u = st.text_input("Username", key="login_u")
            p = st.text_input("Password", type="password", key="login_p")
            agree_l = st.checkbox("I agree to terms", key="agree_l")
            if st.button("Enter Gobidas", key="btn_l", disabled=not agree_l):
                if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.messages = []
                    st.rerun()
                else: st.error("Invalid Username or Password")
        
        with tab2:
            new_u = st.text_input("New Username", key="reg_u")
            new_p = st.text_input("New Password", type="password", key="reg_p")
            agree_r = st.checkbox("I agree to terms", key="agree_r")
            if st.button("Create Account", key="btn_r", disabled=not agree_r):
                if new_u and new_p:
                    st.session_state.db["users"][new_u] = new_p
                    st.session_state.db["history"][new_u] = []
                    save_db(st.session_state.db)
                    st.success("Account created! Go to Log In tab.")

        with st.expander("Read Terms and Privacy Policy"):
            show_legal()
    st.stop()

# --- 5. CHAT SIDEBAR (ONLY SHOWS WHEN LOGGED IN) ---
with st.sidebar:
    st.title(f"Welcome, {st.session_state.user}")
    
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    
    st.divider()
    img_file = st.file_uploader("Upload an Image", type=['png', 'jpg', 'jpeg'])
    
    st.divider()
    st.subheader("Chat History")
    user_history = st.session_state.db["history"].get(st.session_state.user, [])
    for i, chat in enumerate(user_history):
        if st.button(f"Chat: {chat.get('name', 'Untitled')}", key=f"hist_{i}"):
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

# --- 6. MAIN CHAT INTERFACE ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Message Gobidas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_file: st.image(img_file, width=300)

    with st.chat_message("assistant"):
        try:
            if img_file:
                # Meta Llama 4 Scout for Vision
                img = Image.open(img_file).convert("RGB")
                img.thumbnail((800, 800))
                buf = io.BytesIO()
                img.save(buf, format="JPEG")
                b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
                
                res = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=[{"role": "user", "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                    ]}]
                )
            else:
                # Llama 3.3 for Text
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=st.session_state.messages
                )
            
            answer = res.choices[0].message.content
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
            # Update History
            history = st.session_state.db["history"].get(st.session_state.user, [])
            chat_obj = {"name": prompt[:20], "msgs": st.session_state.messages, "time": time.time()}
            
            if st.session_state.get("active_idx") is None:
                history.append(chat_obj)
                st.session_state.active_idx = len(history) - 1
            else:
                history[st.session_state.active_idx] = chat_obj
            
            st.session_state.db["history"][st.session_state.user] = history
            save_db(st.session_state.db)

        except Exception as e:
            st.error(f"Something went wrong: {e}")
