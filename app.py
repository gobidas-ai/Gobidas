import streamlit as st
from groq import Groq
import json, os, base64, io, time
from PIL import Image

# --- 1. UI SETUP & STYLE ---
st.set_page_config(page_title="Gobidas Beta", layout="wide", initial_sidebar_state="expanded")

def get_base64(file):
    try:
        with open(file, 'rb') as f: return base64.b64encode(f.read()).decode()
    except: return ""

bin_str = get_base64('background.jpg')

st.markdown(f"""
<style>
    header[data-testid="stHeader"] {{ visibility: visible !important; background: rgba(0,0,0,0.5) !important; }}
    .stApp a[href*="github.com"], .stApp [data-testid="stHeader"] svg[viewBox*="github"] {{ display: none !important; }}
    footer, [data-testid="stStatusWidget"], [data-testid="stManageAppButton"] {{ display: none !important; }}

    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.65), rgba(0,0,0,0.85)), 
                    url("data:image/jpeg;base64,{bin_str}");
        background-size: cover; background-position: center; background-attachment: fixed;
    }}
    
    [data-testid="stSidebar"] {{ background: rgba(0, 0, 0, 0.95) !important; border-right: 2px solid #FF6D00; }}
    .main-title {{ font-weight: 900; color: #FF6D00; text-align: center; font-size: 5rem; }}
    
    .stButton>button {{ width: 100%; border-radius: 12px; border: 2px solid #FF6D00 !important; color: white !important; background: transparent !important; }}
    .legal-box {{ font-size: 0.85rem; color: #ccc; background: rgba(255,109,0,0.1); padding: 20px; border-radius: 10px; border: 1px solid #FF6D00; line-height: 1.6; }}
    .welcome-card {{ background: rgba(255, 255, 255, 0.1); padding: 25px; border-radius: 15px; border-left: 5px solid #FF6D00; margin-bottom: 20px; }}
</style>
""", unsafe_allow_html=True)

# --- 2. DATA STORAGE ---
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
        st.write(f"Logged in as: **{st.session_state.user}**")
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
            if st.button(f"Chat: {log.get('name', 'Conversation')[:15]}...", key=f"h_{i}"):
                st.session_state.messages = log.get("msgs", [])
                st.session_state.active_idx = len(logs) - 1 - i
                st.rerun()
        
        if st.button("Log out"):
            del st.session_state.user
            st.rerun()

# --- 4. LOGIN & TERMS ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='welcome-card'>
        <h3>Welcome!</h3>
        <p>Currently our website is still in beta (not in the final version yet) so you might experience loss of data (losing your user). 
        Thank you for using our AI and we hope you will like Gobidas! Have fun!</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        tab1, tab2 = st.tabs(["Log in", "Sign up"])
        
        with tab1:
            u_in = st.text_input("Username", key="li_u")
            p_in = st.text_input("Password", type="password", key="li_p")
            
        with tab2:
            u_up = st.text_input("Choose Username", key="su_u")
            p_up = st.text_input("Choose Password", type="password", key="su_p")

        st.markdown("### Terms and Policy")
        st.markdown(f"""
        <div class='legal-box'>
            <strong>1. Beta Agreement:</strong> Gobidas is in a testing phase. We do not guarantee that your account or chats will be saved forever. 
            Data wipes may happen at any time.<br><br>
            <strong>2. Privacy:</strong> We store your username and a hashed version of your password. Your chat history is saved locally on our server 
            so you can see it later. We do not sell your data to third parties.<br><br>
            <strong>3. Usage:</strong> You agree not to use this AI for illegal activities, generating hate speech, or harmful content. 
            The AI can make mistakes; always double-check important info.<br><br>
            <strong>4. Cookies:</strong> We use basic session tools to keep you logged in. By entering, you agree to these simple rules.
        </div>
        """, unsafe_allow_html=True)
        
        agree = st.checkbox("I agree to the terms and policy")
        
        if st.button("Enter", disabled=not agree):
            db = st.session_state.db
            if u_in and p_in: # Log in logic
                if u_in in db["users"] and db["users"][u_in] == p_in:
                    st.session_state.user = u_in
                    st.session_state.messages = []
                    st.rerun()
                else: st.error("Wrong info.")
            elif u_up and p_up: # Sign up logic
                db["users"][u_up] = p_up
                db["history"][u_up] = []
                save_db(db)
                st.success("Account made! Now log in above.")
    st.stop()

# --- 5. CHAT ENGINE (NEW LLAMA 4 MODEL) ---
client = Groq(api_key=st.secrets["GROQ_API_KEY"])
st.markdown("<h1 class='main-title'>Gobidas AI</h1>", unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "image" in msg: st.image(msg["image"], width=400)

if prompt := st.chat_input("Message Gobidas..."):
    msg_entry = {"role": "user", "content": prompt}
    if img_file: msg_entry["image"] = img_file.getvalue()
    st.session_state.messages.append(msg_entry)
    
    with st.chat_message("user"):
        st.markdown(prompt)
        if img_file: st.image(img_file, width=400)

    with st.chat_message("assistant"):
        try:
            if img_file:
                # USING LLAMA 4 SCOUT (NOT 3.2)
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
                res = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                )
            
            ans = res.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            # Save to Database
            hist = st.session_state.db["history"].get(st.session_state.user, [])
            chat_summary = {"name": prompt[:20], "msgs": st.session_state.messages, "timestamp": time.time()}
            
            if st.session_state.get("active_idx") is None:
                hist.append(chat_summary)
                st.session_state.db["history"][st.session_state.user] = hist
                st.session_state.active_idx = len(hist) - 1
            else:
                st.session_state.db["history"][st.session_state.user][st.session_state.active_idx] = chat_summary
            save_db(st.session_state.db)
        except Exception as e:
            st.error(f"Error: {e}")
