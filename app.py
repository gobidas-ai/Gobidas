import streamlit as st
from groq import Groq
import json, os, base64, io, time
from PIL import Image
import streamlit.components.v1 as components

# --- 1. CONFIG & TOTAL STEALTH CSS ---
st.set_page_config(page_title="Gobidas Beta", layout="wide", initial_sidebar_state="expanded")

def get_base64(file):
    if os.path.exists(file):
        with open(file, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    return None

bin_str = get_base64('background.jpg')

st.markdown(f"""
<style>
    /* KILL TOP HEADER COMPLETELY */
    [data-testid="stHeader"] {{ display: none !important; }}
    .stDeployButton, footer, [data-testid="stStatusWidget"] {{ display: none !important; }}
    
    /* APP DESIGN */
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
        color: white !important; background: transparent; font-weight: bold;
    }}
    .stButton>button:hover {{
        background: #FF6D00 !important; color: black !important;
    }}
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE & LONG-FORM LEGAL ---
DB_FILE = "gobidas_db.json"
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                now = time.time()
                # 30-day auto-delete
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
    st.markdown("## Terms of Service & Privacy Policy")
    st.warning("### **BETA NOTICE**\nGobidas Artificial Intelligence is currently in beta. You may experience errors, hallucinations, or unexpected behavior. Use at your own risk.")
    st.markdown("### 1. Disclaimer of Liability")
    st.write("""
    The developer of the Gobidas interface acts strictly as a facilitator for third-party AI models. 
    **Under no circumstances shall the developer be held responsible for any output, statements, 
    or actions performed by the AI.** If the AI generates incorrect, harmful, or illegal content, the legal responsibility lies 
    entirely with the creators of the underlying models (Meta/Groq). By using this app, 
    you waive all rights to sue the developer for AI-generated mistakes.
    """)
    st.markdown("### 2. Data & Privacy")
    st.write("""
    * **Local Storage:** Your credentials and chat logs are saved in a local JSON file on the host machine.
    * **30-Day Policy:** All chat data is automatically purged after 30 days to protect your privacy.
    * **AI Processing:** Your inputs are sent to Groq Cloud for processing. We do not sell your data.
    """)

# --- 3. LOGIN SCREEN ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.8, 1])
    with c2:
        mode = st.radio(" ", ["Log In", "Sign Up"], horizontal=True)
        u = st.text_input("Name")
        p = st.text_input("Password", type="password")
        st.caption("By using this AI you accept our terms and privacy.")
        agree = st.checkbox("I agree to the Terms and Privacy Policy")
        
        if st.button("Enter", disabled=not agree):
            if mode == "Log In":
                if u in st.session_state.db["users"] and st.session_state.db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.messages = []
                    st.rerun()
                else: st.error("Invalid Username/Password.")
            else:
                if u and p:
                    st.session_state.db["users"][u] = p
                    st.session_state.db["history"][u] = []
                    save_db(st.session_state.db)
                    st.success("Account created! Now Log In.")
        with st.expander("Read Privacy & Terms"):
            show_legal()
    st.stop()

# --- 4. SIDEBAR (GEAR ICON INSIDE) ---
with st.sidebar:
    st.title(f"Hi, {st.session_state.user}")
    
    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.active_idx = None
        st.rerun()
    
    img_file = st.file_uploader("Upload Image", type=['png', 'jpg', 'jpeg'])
    
    st.divider()
    st.write("### History")
    hist_list = st.session_state.db["history"].get(st.session_state.user, [])
    
    # Reverse history to show newest at top
    for i, chat in enumerate(reversed(hist_list)):
        actual_idx = len(hist_list) - 1 - i
        # Display the prompt as the name, not just "Chat 1"
        display_name = chat.get('name', 'New Chat')
        if st.button(display_name, key=f"hist_btn_{actual_idx}"):
            st.session_state.messages = chat.get("msgs", [])
            st.session_state.active_idx = actual_idx
            st.rerun()

    st.divider()
    # Gear Icon is now here for guaranteed visibility
    if st.button("⚙️ Settings"):
        st.session_state.show_settings = not st.session_state.get("show_settings", False)
    
    if st.session_state.get("show_settings"):
        if st.button("Logout"):
            del st.session_state.user
            st.rerun()
        with st.expander("Privacy & Terms"):
            show_legal()

# --- 5. CHAT LOGIC ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)

# Display Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.markdown(msg["content"])

if prompt := st.chat_input("Message Gobidas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_file: st.image(img_file, width=300)

    with st.chat_message("assistant"):
        try:
            if img_file:
                # FIXED IMAGE ENCODING ERROR
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
            
            # AUTO-SAVE HISTORY IMMEDIATELY
            history = st.session_state.db["history"].get(st.session_state.user, [])
            # Use the first 25 chars of prompt as the title
            chat_title = prompt[:25] + ("..." if len(prompt) > 25 else "")
            chat_entry = {"name": chat_title, "msgs": st.session_state.messages, "ts": time.time()}
            
            if st.session_state.get("active_idx") is None:
                history.append(chat_entry)
                st.session_state.active_idx = len(history) - 1
            else:
                history[st.session_state.active_idx] = chat_entry
            
            st.session_state.db["history"][st.session_state.user] = history
            save_db(st.session_state.db)
            
        except Exception as e:
            st.error(f"Error: {e}")
