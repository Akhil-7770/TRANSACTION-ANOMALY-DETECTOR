# 🛒 Retail SaaS: ML-Powered POS Anomaly Detection

A real-time, dual-layer Point of Sale (POS) system designed to detect and intercept cashier fraud and billing anomalies using Machine Learning (Isolation Forest) and rigid heuristic thresholds.

## 🚀 System Architecture

This system uses a synchronous, state-managed architecture split into two distinct terminals:
1. **The Employee Terminal:** A live POS interface that evaluates transactions in real-time.
2. **The Admin Control Center:** A centralized dashboard for HR management, rule configuration, and live threat resolution.

### 🛡️ Dual-Layer Security
*   **Layer 1 (Rigid Heuristics):** Hard limits on discounts, cart values, and voided items managed dynamically by the Admin.
*   **Layer 2 (Machine Learning):** An Isolation Forest model that performs context-aware behavioral analysis on the math and the employee's identity to catch subtle, sophisticated fraud.

## ✨ Core Features
*   **Real-Time Buffer State:** Anomalous transactions physically lock the POS terminal and poll the database until a manager approves or rejects the transaction.
*   **Silent Audit Mode:** Option to process transactions normally to avoid alerting the customer, while secretly flagging the employee in the database for review.
*   **Self-Learning ML Loop:** The AI adapts to new employees. Managers can approve "Zero-Trust" transactions and retrain the neural baseline with a single click.
*   **Staff Management (CRUD):** Full HR capabilities to register, terminate, and reset passwords for POS cashiers.
*   **End-of-Day Accounting:** One-click CSV export of the day's transaction ledger.

## 💻 Tech Stack
*   **Frontend & Routing:** Streamlit (Python)
*   **Database:** SQLite (SHA-256 Encrypted Passwords)
*   **Machine Learning:** Scikit-Learn (Isolation Forest), Pandas, Joblib

## ⚙️ Installation & Setup
1. Clone the repository:
   `git clone https://github.com/yourusername/retail-saas-pos.git`
2. Install the required dependencies:
   `pip install streamlit pandas scikit-learn joblib`
3. Run the application:
   `streamlit run app.py`
4. **Default Admin Login:** Username: `admin` | Password: `admin123`


## 👥 Team Members
This project was collaboratively built as part of our Mini Project submission.

AKHIL V - System Architecture, ML Integration, Frontend UI & State Management
ANANYA K - Database Design & Rule Configuration
ADITHYA R - Documentation & QA Testing

