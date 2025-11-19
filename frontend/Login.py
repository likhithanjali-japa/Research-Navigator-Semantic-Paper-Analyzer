# Login.py
import streamlit as st
import requests
import os

st.set_page_config(page_title="Research Navigator - Login", layout="centered")
BACKEND = st.secrets.get("backend_url", os.environ.get("BACKEND_URL", "http://backend:8000"))

NAVY = "#002B5C"
BG = "#F8F9FB"

st.markdown(f"""
    <style>
    .header {{
        text-align: center;
        margin-top: 20px;
        color: {NAVY};
    }}
    .box {{
        background: white;
        padding: 28px;
        border-radius: 12px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.06);
        width: 420px;
        margin: auto;
    }}
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='header'>🔐 Research Navigator</h1>", unsafe_allow_html=True)
st.write("Sign in or create an account to continue.")

if "login_mode" not in st.session_state:
    st.session_state.login_mode = "signin"

col1, col2 = st.columns(2)
with col1:
    if st.button("Sign In", key="signin_btn", use_container_width=True):
        st.session_state.login_mode = "signin"
with col2:
    if st.button("Create Account", key="signup_btn", use_container_width=True):
        st.session_state.login_mode = "signup"

st.markdown("<hr>", unsafe_allow_html=True)

if st.session_state.login_mode == "signin":
    with st.container():
        st.markdown("<div class='box'>", unsafe_allow_html=True)
        st.subheader("Sign In")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pwd")

        if st.button("Login", key="login_submit", use_container_width=True):
            if email and password:
                try:
                    res = requests.post(f"{BACKEND}/login", json={"email": email, "password": password}, timeout=10)
                    if res.status_code == 200:
                        data = res.json().get("data") or res.json()
                        st.session_state["user"] = data
                        st.success(f"Welcome back, {data.get('name','Researcher')}!")
                        # Redirect to main app page (app.py) in same container: use rerun
                        st.experimental_rerun()
                    else:
                        # try to parse error detail
                        try:
                            err = res.json()
                            st.error(err.get("detail") or err.get("error") or str(err))
                        except:
                            st.error("Invalid credentials. Please try again.")
                except requests.exceptions.RequestException:
                    st.error(f"Cannot connect to backend at {BACKEND}. Is the server running?")
            else:
                st.warning("Please enter email and password.")
        st.markdown("</div>", unsafe_allow_html=True)
else:
    with st.container():
        st.markdown("<div class='box'>", unsafe_allow_html=True)
        st.subheader("Create Account")
        name = st.text_input("Full Name", key="reg_name")
        email = st.text_input("Email Address", key="reg_email")
        password = st.text_input("Password", type="password", key="reg_pwd")
        institution = st.text_input("Institution / University", key="reg_inst")
        research = st.text_input("Research Areas", key="reg_research")

        if st.button("Create Account", key="register_submit", use_container_width=True):
            if name and email and password:
                try:
                    res = requests.post(f"{BACKEND}/register",
                                        json={"name": name, "email": email, "password": password,
                                              "institution": institution, "research": research}, timeout=10)
                    if res.status_code == 200:
                        st.success("Account created successfully! Please sign in.")
                        st.session_state.login_mode = "signin"
                        st.experimental_rerun()
                    else:
                        try:
                            st.error(res.json().get("detail") or res.json().get("error") or "Registration failed.")
                        except:
                            st.error("Registration failed.")
                except requests.exceptions.RequestException:
                    st.error(f"Cannot connect to backend at {BACKEND}. Is the server running?")
            else:
                st.warning("Please fill out all required fields.")
        st.markdown("</div>", unsafe_allow_html=True)
