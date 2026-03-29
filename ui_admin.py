import streamlit as st
import pandas as pd
import sqlite3
import database as db
import ml_engine as ml
import json
import time
from datetime import datetime

def update_transaction_status(tx_id, new_status):
    conn = sqlite3.connect(db.DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE transactions SET status = ? WHERE id = ?", (new_status, tx_id))
    conn.commit()
    conn.close()
    st.rerun()

def render_admin_dashboard(username):
    st.title("🛡️ Admin Control Center")
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["⚙️ Settings", "🚨 Live Alerts", "📊 Analytics", "👥 Staff Management"])

    # --- TAB 1: SYSTEM CONFIGURATION ---
    with tab1:
        st.subheader("Data Initialization")
        colA, colB = st.columns(2)
        with colA:
            uploaded_file = st.file_uploader("Upload Legacy POS Data (.csv)", type="csv", label_visibility="collapsed")
            if uploaded_file and st.button("Migrate to SQL", use_container_width=True):
                rows = db.bootstrap_db_from_csv(uploaded_file)
                st.success(f"{rows} rows migrated.")
        with colB:
            st.write("Retrain ML Baseline")
            if st.button("Train Isolation Forest", type="primary", use_container_width=True):
                success, message = ml.retrain_model()
                st.success(message) if success else st.error(message)

        st.markdown("---")
        st.subheader("Rigid Security Thresholds")
        try:
            with open("system_config.json", "r") as f:
                config = json.load(f)
        except FileNotFoundError:
            config = {"strict_mode": True, "max_discount": 15.0, "max_voids": 3, "max_cart_value": 50000.0}

        strict_mode = st.toggle("🚨 Enable Buffer State (Require manual override for anomalies)", value=config.get("strict_mode", True))
        
        c1, c2, c3 = st.columns(3)
        with c1:
            max_discount = st.number_input("Max Discount (%)", 0.0, 100.0, float(config.get("max_discount", 15.0)))
        with c2:
            max_voids = st.number_input("Max Voided Items", 0, 50, int(config.get("max_voids", 3)))
        with c3:
            max_cart_value = st.number_input("Max Cart Value (₹)", 0.0, 1000000.0, float(config.get("max_cart_value", 50000.0)))

        if st.button("💾 Save Global Rules", type="primary"):
            with open("system_config.json", "w") as f:
                json.dump({"strict_mode": strict_mode, "max_discount": max_discount, "max_voids": max_voids, "max_cart_value": max_cart_value}, f)
            st.success("Rules updated instantly across all POS terminals.")

    # --- TAB 2: LIVE ALERTS ---
    with tab2:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("Action Required: Pending Transactions")
        with col2:
            auto_sync = st.toggle("🔄 Live Auto-Sync", value=False)
            
        conn = sqlite3.connect(db.DB_NAME)
        df_pending = pd.read_sql_query("SELECT * FROM transactions WHERE status = 'Pending_Review'", conn)
        conn.close()

        if df_pending.empty:
            st.info("No active alerts. The queue is empty.")
        else:
            for index, row in df_pending.iterrows():
                with st.expander(f"🚨 Cashier {row['cashier_id']} | Cart: ₹{row['cart_value']} | Time: {row['timestamp']}", expanded=True):
                    st.write(f"**Item:** {row['item_category']} | **Discount:** {row['discount']}% | **Voids:** {row['voided_items']}")
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button("✅ Approve Transaction", key=f"allow_{row['id']}", use_container_width=True):
                            update_transaction_status(row['id'], 'Admin_Allowed')
                    with btn_col2:
                        if st.button("❌ Reject Transaction", key=f"deny_{row['id']}", type="primary", use_container_width=True):
                            update_transaction_status(row['id'], 'Purged')

        if auto_sync:
            time.sleep(2)
            st.rerun()

    # --- TAB 3: END-OF-DAY ANALYTICS & EXPORT ---
    with tab3:
        st.subheader("Store Performance & Security Metrics")
        conn = sqlite3.connect(db.DB_NAME)
        df_all = pd.read_sql_query("SELECT * FROM transactions", conn)
        conn.close()
        
        if not df_all.empty:
            total_revenue = df_all[df_all['status'].isin(['Approved', 'Admin_Allowed'])]['cart_value'].sum()
            total_anomalies = len(df_all[df_all['anomaly_flag'] == 1])
            c1, c2 = st.columns(2)
            c1.metric("Net Approved Revenue", f"₹{total_revenue:,.2f}")
            c2.metric("Total Flagged Threats", total_anomalies)
            
            st.markdown("---")
            st.subheader("Suspect Cashier Analysis")
            cashier_stats = df_all.groupby('cashier_id').agg(Total_Transactions=('id', 'count'), Flagged_Anomalies=('anomaly_flag', 'sum')).reset_index()
            cashier_stats['Anomaly_Ratio (%)'] = (cashier_stats['Flagged_Anomalies'] / cashier_stats['Total_Transactions'] * 100).round(2)
            st.dataframe(cashier_stats.style.highlight_max(subset=['Anomaly_Ratio (%)'], color='#ff4b4b'), use_container_width=True)

            # === TRUE END-OF-DAY REPORT EXPORT ===
            st.markdown("---")
            st.subheader("📥 Export Today's End-of-Day Report")
            st.write("Download the transaction ledger specifically for today's date.")
            
            # Get today's date in YYYY-MM-DD format
            today_str = datetime.today().strftime('%Y-%m-%d')
            
            # Filter the dataframe to only include rows where the timestamp starts with today's date
            df_all['timestamp'] = df_all['timestamp'].astype(str)
            df_today = df_all[df_all['timestamp'].str.startswith(today_str)]
            
            if df_today.empty:
                st.info("No transactions have been recorded for today yet.")
            else:
                # Convert only today's data to CSV
                csv_data = df_today.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label=f"Download Today's Ledger ({len(df_today)} Transactions)",
                    data=csv_data,
                    file_name=f"EOD_Audit_Report_{today_str}.csv",
                    mime="text/csv",
                    type="primary",
                    use_container_width=True
                )

    # --- TAB 4: STAFF MANAGEMENT & AUDITING ---
    with tab4:
        st.subheader("👥 Human Resources & Access Control")
        
        emp_list = db.get_all_employees()
        
        colA, colB = st.columns(2)
        
        with colA:
            st.markdown("**Register New Employee**")
            with st.form("add_user_form"):
                new_emp_id = st.text_input("Employee ID (e.g., C02)")
                new_emp_pass = st.text_input("Assign Password", type="password")
                if st.form_submit_button("Create Account", type="primary"):
                    if new_emp_id and new_emp_pass:
                        if db.add_user(new_emp_id, new_emp_pass):
                            st.success(f"✅ Account {new_emp_id} created.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Employee ID already exists.")
                    else:
                        st.warning("Fill all fields.")
                        
        with colB:
            st.markdown("**Manage Existing Access**")
            target_emp = st.selectbox("Select Employee", [""] + emp_list)
            if target_emp:
                new_pass = st.text_input("Reset Password", type="password")
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("Update Password"):
                        db.reset_password(target_emp, new_pass)
                        st.success("Password reset successful.")
                with btn_col2:
                    if st.button("🚨 Terminate Staff", type="primary"):
                        db.delete_user(target_emp)
                        st.warning(f"Access revoked for {target_emp}.")
                        time.sleep(1)
                        st.rerun()

        st.markdown("---")
        
        st.subheader("🔍 Individual Employee Audit Log")
        audit_target = st.selectbox("Select Cashier to View Transaction History", [""] + emp_list, key="audit_dropdown")
        
        if audit_target:
            conn = sqlite3.connect(db.DB_NAME)
            query = """
                SELECT timestamp, item_category, cart_value, discount, voided_items, anomaly_flag, status 
                FROM transactions 
                WHERE cashier_id = ? 
                ORDER BY id DESC
            """
            df_audit = pd.read_sql_query(query, conn, params=(audit_target,))
            conn.close()
            
            if df_audit.empty:
                st.info(f"No transaction history found for {audit_target}.")
            else:
                st.dataframe(
                    df_audit.style.apply(
                        lambda x: ['background: #ffe6e6' if x['anomaly_flag'] == 1 else '' for i in x], axis=1
                    ), 
                    use_container_width=True
                )