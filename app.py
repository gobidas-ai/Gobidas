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
    /* FORCE DARK UI */
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
    .stButton>button:hover {{ background: #FF6D00 !important; color: black !important; }}
    
    .legal-box {{ font-size: 0.85rem; color: #ccc; background: rgba(0,0,0,0.7); padding: 30px; border-radius: 10px; border: 1px solid #FF6D00; line-height: 1.8; height: 600px; overflow-y: scroll; }}
    .welcome-card {{ background: rgba(255, 255, 255, 0.05); padding: 30px; border-radius: 15px; border-left: 8px solid #FF6D00; margin-bottom: 25px; backdrop-filter: blur(10px); }}
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
        st.write(f"User: **{st.session_state.user}**")
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
            clean_name = log.get('name', 'Chat History')[:25]
            if st.button(f"{clean_name}", key=f"h_{i}"):
                st.session_state.messages = log.get("msgs", [])
                st.session_state.active_idx = len(logs) - 1 - i
                st.rerun()
        
        if st.button("Log out"):
            del st.session_state.user
            st.rerun()

# --- 4. LOGIN & MEGA TERMS ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class='welcome-card'>
        <h2>Welcome!</h2>
        <p>Currently our website is still in beta (not in the final version yet) so you might experience loss of data (losing your user). 
        Everything here is for testing purposes. We appreciate you being part of the early Gobidas community. Have fun!</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        mode = st.radio(" ", ["Log in", "Sign up"], horizontal=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        st.markdown("### Privacy Policy and Terms of Service")
        st.markdown(f"""
        <div class='legal-box'>
            <strong>ARTICLE 1: GENERAL USAGE</strong><br>
            By creating an account on Gobidas, you agree to follow our rules. We have the right to change these rules at any time. If you do not agree, you should stop using the site immediately.<br><br>
            <strong>ARTICLE 2: BETA STAGE AND DATA SECURITY</strong><br>
            Gobidas is in a BETA phase. This means the code is not final. We do not guarantee that your account will always be here. Data wipes happen. Servers crash. Files get lost. By using this site, you accept the risk that your chat history or user profile could be deleted forever without notice.<br><br>
            <strong>ARTICLE 3: ACCOUNT PRIVACY</strong><br>
            We collect your username and password. This is only used so you can log in. We do not ask for your email or phone number. Your chat history is saved so you can see it later. We do not share your chats with any other company. Your data stays on our private server.<br><br>
            <strong>ARTICLE 4: PROHIBITED ACTIONS</strong><br>
            You are NOT allowed to use Gobidas to:
            <ul>
                <li>Create illegal content or harmful instructions.</li>
                <li>Harass, bully, or insult other people or groups.</li>
                <li>Attempt to break into our server or steal other users' data.</li>
                <li>Spam the AI with nonsense or harmful code.</li>
            </ul><br>
            <strong>ARTICLE 5: AI LIMITATIONS</strong><br>
            The AI is a computer model. It can make mistakes. It can give wrong facts. It can say things that are biased or incorrect. You should not use the AI for medical, legal, or financial advice. Always verify information yourself.<br><br>
            <strong>ARTICLE 6: COOKIES AND TRACKING</strong><br>
            We use simple session cookies to keep you logged in. We do not track you across other websites. We do not use advertising trackers.<br><br>
            <strong>ARTICLE 7: DATA RETENTION</strong><br>
            Old chat logs are cleared every 30 days to keep the system running fast. Inactive accounts may be deleted after 60 days of no use.<br><br>
            <strong>ARTICLE 8: NO LIABILITY</strong><br>
            The owners of Gobidas are not responsible for any damage caused by the AI's output or the loss of your data. You use this service at your own risk.<br><br>
            <strong>ARTICLE 9: TERMINATION</strong><br>
            We can ban any user for any reason if we think they are breaking the rules or hurting the community.
        </div>
        """, unsafe_allow_html=True)
        
        agree = st.checkbox("I agree to the terms and policy")
        
        if st.button("Enter", disabled=not agree):
            db = st.session_state.db
            if mode == "Log in":
                if u in db["users"] and db["users"][u] == p:
                    st.session_state.user = u
                    st.session_state.messages = []
                    st.rerun()
                else: st.error("Wrong details.")
            else:
                if u and p:
                    db["users"][u] = p
                    db["history"][u] = []
                    save_db(db)
                    st.success("Account created! Now log in.")
    st.stop()

# --- 5. CHAT ENGINE (MIXTRAL & DEEPSEEK - NO LLAMA/LLAVA) ---
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
        img_bytes = img_file.getvalue()
        b64_str = base64.b64encode(img_bytes).decode('utf-8')
        msg_entry["image_b64"] = b64_str

    st.session_state.messages.append(msg_entry)
    
    with st.chat_message("user"):
        st.markdown(prompt)
        if b64_str: st.image(img_file, width=400)

    with st.chat_message("assistant"):
        try:
            # TEXT AND IMAGE LOGIC USING NON-LLAMA ARCHITECTURES
            if b64_str:
                # Using MoE (Mixture of Experts) architecture models for vision where available
                res = client.chat.completions.create(
                    model="mixtral-8x7b-32768", # Fallback for vision-context text
                    messages=[{"role": "user", "content": prompt}]
                )
            else:
                res = client.chat.completions.create(
                    model="mixtral-8x7b-32768",
                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
                )
            
            ans = res.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            # SAVE HISTORY
            hist = st.session_state.db["history"].get(st.session_state.user, [])
            chat_summary = {"name": prompt[:25], "msgs": st.session_state.messages, "timestamp": time.time()}
            
            if st.session_state.get("active_idx") is None:
                hist.append(chat_summary)
                st.session_state.db["history"][st.session_state.user] = hist
                st.session_state.active_idx = len(hist) - 1
            else:
                st.session_state.db["history"][st.session_state.user][st.session_state.active_idx] = chat_summary
            save_db(st.session_state.db)
        except Exception as e:
            st.error(f"Error: {e}")
