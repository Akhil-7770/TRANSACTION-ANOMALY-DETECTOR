import streamlit as st
import database as db
import ml_engine as ml
import time
import json
from datetime import datetime

def render_employee_dashboard(username):
    st.title("🛒 Live POS Terminal")
    st.caption(f"Cashier: **{username}** | System: Online")
    
    # 1. Manual Date and Time Override
    with st.expander("⏱️ Manual Date/Time Entry (Optional)", expanded=False):
        c1, c2 = st.columns(2)
        tx_date = c1.date_input("Date")
        tx_time = c2.time_input("Time")
        manual_timestamp = f"{tx_date} {tx_time}"

    # 2. POS Input Form
    st.markdown("### Transaction Details")
    col1, col2, col3 = st.columns(3)
    with col1:
        item_category = st.selectbox("Category", ["Groceries", "Electronics", "Clothing", "Pharmacy", "Hardware"])
    with col2:
        cart_value = st.number_input("Cart Value (₹)", min_value=0.0, format="%.2f")
    with col3:
        discount = st.number_input("Discount (%)", min_value=0.0, max_value=100.0, step=1.0)
    
    voided_items = st.number_input("Number of Voided Items", min_value=0, step=1)
    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("💳 Process Transaction", type="primary", use_container_width=True):
        if cart_value <= 0:
            st.warning("Cart value must be greater than zero.")
            return

        # Load Admin Rules
        try:
            with open("system_config.json", "r") as f:
                config = json.load(f)
        except FileNotFoundError:
            config = {"strict_mode": True, "max_discount": 15.0, "max_voids": 3, "max_cart_value": 50000.0}

        try:
            # Check Machine Learning
            is_anomaly = ml.predict_anomaly(username, item_category, cart_value, discount, voided_items)
            
            # Check Rigid Admin Rules (Override ML if violated)
            if (discount > config.get("max_discount", 15.0) or 
                voided_items > config.get("max_voids", 3) or 
                cart_value > config.get("max_cart_value", 50000.0)):
                is_anomaly = 1

            # Routing Logic
            if is_anomaly == 1:
                if config.get("strict_mode", True):
                    # === STRICT MODE (BUFFER STATE) ===
                    # Log as Pending and lock the terminal
                    tx_id = db.log_transaction(manual_timestamp, username, item_category, cart_value, discount, voided_items, 1, 'Pending_Review')
                    
                    status_container = st.empty()
                    status = 'Pending_Review'
                    
                    # Lock the UI and poll the database every 1 second
                    while status == 'Pending_Review':
                        status_container.warning("🚨 **ANOMALY DETECTED.** Transaction frozen. Waiting for Manager override...")
                        time.sleep(1) 
                        status = db.get_transaction_status(tx_id) 
                    
                    # The loop broke! Admin made a decision.
                    status_container.empty() 
                    if status == 'Admin_Allowed':
                        st.success("✅ **Manager Approved the transaction.**")
                        st.balloons()
                    elif status == 'Purged':
                        st.error("❌ **TRANSACTION REJECTED BY ADMIN.**")
                        st.info("The customer cannot proceed with these items.")
                        if st.button("Enter New Transaction"):
                            st.rerun() 
                else:
                    # === SILENT AUDIT MODE ===
                    # Log ONCE as Approved so the customer leaves, but keep anomaly_flag = 1 for the Analytics board
                    db.log_transaction(manual_timestamp, username, item_category, cart_value, discount, voided_items, 1, 'Approved')
                    st.success("✅ **Transaction Approved.**")
                    # No balloons here; we don't celebrate fraud, even if we are silently tracking it.
            else:
                # === COMPLETELY NORMAL TRANSACTION ===
                db.log_transaction(manual_timestamp, username, item_category, cart_value, discount, voided_items, 0, 'Approved')
                st.success("✅ **Transaction Approved.**")
                st.balloons()
                
        except Exception as e:
            st.error(f"System Error: {e}")