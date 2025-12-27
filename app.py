import smtplib, random
from email.mime.text import MIMEText
from st_gsheets_connection import GSheetsConnection

# --- 2. THE PERMANENT VAULT ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_db_df():
    try:
        return conn.read(ttl=0)
    except:
        # If sheet is empty, create headers
        return pd.DataFrame(columns=["email", "password"])

# --- HELPER: SEND OTP CODE ---
def send_otp(receiver_email):
    otp_code = str(random.randint(111111, 999999))
    sender = "gobidasai@gmail.com"
    # The 'App Password' from Google Secrets
    app_pwd = st.secrets["EMAIL_PASSWORD"] 
    
    msg = MIMEText(f"Your Gobidas Beta Access Code: {otp_code}")
    msg['Subject'] = "GOBIDAS AUTHENTICATION"
    msg['From'] = f"Gobidas AI <{sender}>"
    msg['To'] = receiver_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, app_pwd)
            server.sendmail(sender, receiver_email, msg.as_string())
        return otp_code
    except Exception as e:
        st.error(f"Email Error: {e}")
        return None

# --- 3. LOGIN & VERIFICATION (NO USERNAME) ---
if "user" not in st.session_state:
    st.markdown("<h1 class='main-title'>Gobidas BETA</h1>", unsafe_allow_html=True)
    
    if "step" not in st.session_state: st.session_state.step = "input"

    c1, c2, c3 = st.columns([1, 1.8, 1])
    with c2:
        if st.session_state.step == "input":
            mode = st.radio("ACCESS GATE", ["LOG IN", "SIGN UP"], horizontal=True)
            email_in = st.text_input("EMAIL ADDRESS").lower().strip()
            pass_in = st.text_input("PASSWORD", type="password")
            agree = st.checkbox("I agree to the Legal Articles")

            if st.button("PROCEED", disabled=not agree):
                df = get_db_df()
                if mode == "LOG IN":
                    # Checking Email instead of Username
                    user_match = df[(df['email'] == email_in) & (df['password'] == pass_in)]
                    if not user_match.empty:
                        st.session_state.user = email_in
                        st.rerun()
                    else: st.error("Account not found or password incorrect.")
                else:
                    if "@" in email_in and len(pass_in) > 5:
                        # Send OTP to verify the new user
                        code = send_otp(email_in)
                        if code:
                            st.session_state.temp_email = email_in
                            st.session_state.temp_pass = pass_in
                            st.session_state.sent_otp = code
                            st.session_state.step = "verify"
                            st.rerun()
                    else: st.error("Enter a valid email and 6+ character password.")

        elif st.session_state.step == "verify":
            st.info(f"Verification code sent to {st.session_state.temp_email}")
            user_otp = st.text_input("ENTER 6-DIGIT CODE")
            if st.button("VERIFY & REGISTER"):
                if user_otp == st.session_state.sent_otp:
                    df = get_db_df()
                    if st.session_state.temp_email in df['email'].values:
                        st.error("This email is already registered.")
                    else:
                        # Save to Google Sheet Permanently
                        new_row = pd.DataFrame([{"email": st.session_state.temp_email, "password": st.session_state.temp_pass}])
                        updated_df = pd.concat([df, new_row], ignore_index=True)
                        conn.update(data=updated_df)
                        st.success("Verified! You can now Log In.")
                        st.session_state.step = "input"
                        time.sleep(1.5)
                        st.rerun()
                else: st.error("Invalid Code.")
    st.stop()
