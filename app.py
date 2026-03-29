import streamlit as st
import database as db
import ui_admin
import ui_employee

# Configure the main application window
st.set_page_config(page_title="Retail Fraud AI", page_icon="🛡️", layout="wide")

# Initialize session state for memory across reruns
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
    st.session_state['username'] = ''
    st.session_state['role'] = ''

def attempt_login(username, password):
    """Verifies credentials and sets session state."""
    role = db.verify_login(username, password)
    if role:
        st.session_state['logged_in'] = True
        st.session_state['username'] = username
        st.session_state['role'] = role
        st.rerun()
    else:
        st.error("Authentication Failed: Invalid username or password.")

def attempt_logout():
    """Clears the session state and returns to login."""
    st.session_state['logged_in'] = False
    st.session_state['username'] = ''
    st.session_state['role'] = ''
    st.rerun()

# ==========================================
# MASTER ROUTER
# ==========================================

if not st.session_state['logged_in']:
    # --- RENDER LOGIN SCREEN ---
    st.markdown("<h1 style='text-align: center;'>Retail Transaction Anomaly Detection</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Secure Gateway Login</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.form("login_form"):
            user_input = st.text_input("Username")
            pass_input = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Authenticate", use_container_width=True)
            
            if submitted:
                if user_input and pass_input:
                    attempt_login(user_input, pass_input)
                else:
                    st.warning("Please enter both username and password.")
                    
        # Viva Hint: Display credentials for easy testing
        st.info("**System Credentials:**\n* Admin: `admin` | `admin123`\n* Cashier: `C01` | `pass123`")

else:
    # --- RENDER SECURE DASHBOARDS ---
    # Global Sidebar for Logged-In Users
    with st.sidebar:
        st.success(f"Active Session: {st.session_state['role']}")
        st.write(f"**User ID:** {st.session_state['username']}")
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            attempt_logout()

    # RBAC Routing Logic
    if st.session_state['role'] == 'Admin':
        ui_admin.render_admin_dashboard(st.session_state['username'])
    elif st.session_state['role'] == 'Employee':
        ui_employee.render_employee_dashboard(st.session_state['username'])