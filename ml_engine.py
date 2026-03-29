import pandas as pd
import joblib
import sqlite3
import os
from sklearn.ensemble import IsolationForest

MODEL_FILE = 'trained_model.pkl'
COLUMNS_FILE = 'expected_columns.pkl'
DB_NAME = 'retail_saas.db'

def load_model_assets():
    """Loads the trained Isolation Forest and expected column structure."""
    if not os.path.exists(MODEL_FILE) or not os.path.exists(COLUMNS_FILE):
        return None, None
    return joblib.load(MODEL_FILE), joblib.load(COLUMNS_FILE)

def predict_anomaly(cashier_id, item_category, cart_value, discount, voided_items):
    """
    Evaluates the transaction including Employee Identity and Item Context.
    """
    model, expected_columns = load_model_assets()
    if model is None:
        raise FileNotFoundError("ML Model files missing. Please bootstrap and retrain the system.")

    input_data = pd.DataFrame({
        'Cashier_ID': [cashier_id],
        'Item_Category': [item_category],
        'Cart_Value': [cart_value],
        'Discount_Percent': [discount],
        'Voided_Items': [voided_items]
    })

    # One-Hot Encode to create the identity/category columns
    input_encoded = pd.get_dummies(input_data)
    
    # The Dimensionality Defense: Align with the exact columns the AI trained on
    input_aligned = input_encoded.reindex(columns=expected_columns, fill_value=0)

    # Predict: -1 for anomaly, 1 for normal.
    prediction = model.predict(input_aligned)[0]
    
    return 1 if prediction == -1 else 0

def retrain_model():
    """
    Fetches clean data AND Admin-Approved exceptions to build a growing baseline.
    """
    conn = sqlite3.connect(DB_NAME)
    
    # THE UPGRADE: Learn from historically clean data AND new Admin_Allowed transactions
    query = """
        SELECT cashier_id as Cashier_ID, item_category as Item_Category, 
               cart_value as Cart_Value, discount as Discount_Percent, 
               voided_items as Voided_Items 
        FROM transactions 
        WHERE status IN ('Approved', 'Admin_Allowed')
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()

    if len(df) < 50:
        return False, "Not enough clean data to retrain. Need at least 50 standard transactions."

    # One-hot encode the full dataset
    df_encoded = pd.get_dummies(df)
    expected_columns = df_encoded.columns

    # Train the Isolation Forest with the new Context
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(df_encoded)

    # Serialize and save to hard drive
    joblib.dump(model, MODEL_FILE)
    joblib.dump(expected_columns, COLUMNS_FILE)

    return True, f"Model retrained on {len(df)} transactions. Identity and Context profiling restored."