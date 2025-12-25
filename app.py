import streamlit as st
from groq import Groq

st.title("GOBIDAS 🟠")

# The simple "Vault" check
pw = st.sidebar.text_input("System Key", type="password")
if pw != st.secrets["password"]:
    st.info("Enter the password in the sidebar to start.")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Ask..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)
    
    chat = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=st.session_state.messages)
    ans = chat.choices[0].message.content
    
    with st.chat_message("assistant"): st.markdown(ans)
    st.session_state.messages.append({"role": "assistant", "content": ans})
