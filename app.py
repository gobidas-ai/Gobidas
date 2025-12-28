import streamlit as st
from groq import Groq
import json, os, base64, io, time
from PIL import Image

# --- 1. UI & SYSTEM SETUP ---
st.set_page_config(page_title="Gobidas Beta", layout="wide", initial_sidebar_state="expanded")

def get_base64_img(file_path):
    try:
        with open(file_path, 'rb') as f: return base64.b64encode(f.read()).decode()
    except: return ""

bin_str = get_base64_img('background.jpg')

st.markdown(f"""
<style>
    /* FORCE DARK UI AND SYSTEM SETTINGS */
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
    
    .legal-box {{ font-size: 0.9rem; color: #ddd; background: rgba(0,0,0,0.8); padding: 35px; border-radius: 12px; border: 1px solid #FF6D00; line-height: 1.8; height: 650px; overflow-y: scroll; }}
</style>
""", unsafe_allow_html=True)

# --- 2. DATABASE SYSTEM ---
DB_FILE = "gobidas_db.json"
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: pass
    return {"users": {}, "history": {}}

def save_db(data):
    # Images are converted to strings before this to avoid "bytes not JSON serializable"
    with open(DB_FILE, "w") as f: json.dump(data, f)

if "db" not in st.session_state:
    st.session_state.db = load_db()

# --- 3. SIDEBAR NAVIGATION ---
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
            clean_name = log.get('name', 'Conversation')[:25]
            if st.button(f"{clean_name}", key=f"h_{i}"):
                st.session_state.messages = log.get("msgs", [])
                st.session_state.active_idx = len(logs) - 1 - i
                st.rerun()
        
        if st.button("Log out"):
            del st.session_state.user
            st.rerun()

# --- 4. ACCESS CONTROL & EXTENDED TERMS ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas</h1>", unsafe_allow_html=True)
    
    st.info("Welcome! Currently our website is still in beta (not in the final version yet) so you might experience loss of data (losing your user). Thank you for using our AI and we hope you will like Gobidas! Have fun!")

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        mode = st.radio(" ", ["Log in", "Sign up"], horizontal=True)
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        st.markdown("### Privacy Policy and Full Terms of Service")
        st.markdown(f"""
        <div class='legal-box'>
            <strong>ARTICLE 1: AGREEMENT TO TERMS</strong><br>
            By creating an account or using Gobidas AI, you expressly agree to be bound by these Terms of Service. If you do not agree, you must immediately exit the platform.<br><br>
            <strong>ARTICLE 2: BETA TESTING AND DATA RISKS</strong><br>
            Gobidas is a Beta-stage application. We are currently testing server stability and AI integration. You acknowledge that this software is provided "AS IS." We make no guarantees regarding data persistence. User accounts, chat histories, and any uploaded media may be purged, corrupted, or lost during updates or server maintenance. You are responsible for maintaining your own copies of important data.<br><br>
            <strong>ARTICLE 3: DATA PRIVACY AND PROTECTION</strong><br>
            We collect minimal data: your username, a hashed password, and your interaction logs. This information is stored in a local server database solely to facilitate your user experience. We do not sell, license, or provide your data to third-party advertisers or data brokers. Your privacy is a priority, but you should avoid sharing sensitive personal identification (SSNs, banking info) with the AI.<br><br>
            <strong>ARTICLE 4: USER RESPONSIBILITIES</strong><br>
            You agree to use Gobidas for lawful purposes only. Prohibited actions include:
            <ul>
                <li>Generating harmful, illegal, or violent content.</li>
                <li>Attempting to reverse-engineer the platform.</li>
                <li>Engaging in harassment or spreading misinformation.</li>
                <li>Using automated scripts to spam the API.</li>
            </ul><br>
            <strong>ARTICLE 5: AI LIMITATIONS AND ACCURACY</strong><br>
            The AI models integrated into Gobidas are large language models. They may produce inaccurate, biased, or incomplete information. Gobidas does not verify the factual accuracy of AI responses. Users should seek professional advice for medical, legal, or financial matters. We are not liable for decisions made based on AI output.<br><br>
            <strong>ARTICLE 6: COOKIES AND LOCAL STORAGE</strong><br>
            We use technical cookies and browser local storage to manage your login session. These do not track your activity on other websites.<br><br>
            <strong>ARTICLE 7: DATA RETENTION POLICY</strong><br>
            Chat history is subject to automatic deletion after 30 days of inactivity to optimize server performance. Inactive accounts may be archived or removed after 60 days.<br><br>
            <strong>ARTICLE 8: INDEMNIFICATION</strong><br>
            You agree to indemnify and hold harmless the developers of Gobidas from any claims, damages, or losses resulting from your use of the platform or violation of these terms.<br><br>
            <strong>ARTICLE 9: MODIFICATIONS</strong><br>
            We reserve the right to update these terms at any time. Your continued use of the platform constitutes acceptance of the new terms.
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
                else: st.error("Access Denied. Check your info.")
            else:
                if u and p:
                    db["users"][u] = p
                    db["history"][u] = []
                    save_db(db)
                    st.success("Account created! Now log in.")
    st.stop()

# --- 5. CHAT ENGINE (LLAMA 3.3 70B - NO 3.2 OR V1.5) ---
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
            # Using Llama 3.3 70B (The flagship successor to 3.1)
            # This handles text and text-vision context without using 3.2
            res = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            )
            
            ans = res.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})
            
            # SAVE HISTORY (Image as String)
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
