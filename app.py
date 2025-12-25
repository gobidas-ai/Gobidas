import streamlit as st
from groq import Groq

# --- 1. LUXURY UI CONFIG ---
st.set_page_config(page_title="GOBIDAS", page_icon="🟠", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #000; color: #fff; }
    h1 { color: #FF4B2B; font-weight: 800; text-align: center; }
    .stTextInput>div>div>input { background-color: #111; color: white; border: 1px solid #FF4B2B; }
    .stButton>button { background: #FF4B2B !important; color: white; width: 100%; border-radius: 10px; border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE SIMPLE LOGIN ---
if "logged_in" not in st.session_state:
    st.title("GOBIDAS")
    with st.container():
        col1, col2, col3 = st.columns([1,1.5,1])
        with col2:
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("LOGIN"):
                # Check if user exists in our Secrets list
                if u in st.secrets["passwords"] and p == st.secrets["passwords"][u]:
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
    st.stop()

# --- 3. THE CHAT APP (Once Logged In) ---
st.sidebar.title(f"Welcome, {st.session_state.username}")
if st.sidebar.button("LOGOUT"):
    del st.session_state.logged_in
    st.rerun()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Command Gobidas..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    with st.chat_message("assistant"):
        chat = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        response = chat.choices[0].message.content
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
