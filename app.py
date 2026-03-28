import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px

# --- 1. DATABASE CONNECTION ---
# Fill these in with your actual Supabase credentials
URL = "https://dcpvdapxzkaahyhpflul.supabase.co"
KEY = "sb_publishable_SiQMwIgDgLmckNQHUmO3SA_78UQBLHf"
supabase = create_client(URL, KEY)

st.set_page_config(page_title="EE GREEN SOLUTIONS", layout="wide")
st.title("🌿 EE GREEN SOLUTIONS: Cloud Stock Manager")

# --- 2. THE USER ---
user_name = st.sidebar.text_input("Enter Your Name (Staff/Owner)", "Admin")

# --- 3. HELPER FUNCTIONS ---


def fetch_data():
    """Gets all stock from the cloud"""
    try:
        response = supabase.table("inventory").select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        return pd.DataFrame()  # Returns empty if table isn't ready yet


def update_stock(name, qty, price, user):
    """Saves or Updates stock in the cloud using EXACT screen names"""
    total = qty * price
    # These labels MUST match the SQL table columns exactly (including spaces)
    data = {
        "Item Name": name,
        "Quantity in Stock": qty,
        "Price per Unit": price,
        "Total Value": total,
        "Updated By": user
    }
    # We use "Item Name" as the conflict check so it updates existing items
    supabase.table("inventory").upsert(data, on_conflict="Item Name").execute()


# --- 4. APP INTERFACE ---
menu = ["View Stock", "Add/Update Item", "Business Insights"]
choice = st.sidebar.selectbox("Navigation", menu)

# Load current data
df = fetch_data()

if choice == "View Stock":
    st.subheader("Live Inventory (Cloud Sync)")
    if not df.empty:
        st.dataframe(df)
    else:
        st.info("No stock found. Go to 'Add/Update Item' to begin.")

elif choice == "Add/Update Item":
    st.subheader(f"Editing as: {user_name}")
    with st.form("edit_form"):
        name = st.text_input("Item Name (e.g., Solar Panel)")
        qty = st.number_input("Quantity in Stock", min_value=0, step=1)
        price = st.number_input("Price per Unit", min_value=0.0)
        submit = st.form_submit_button("Push to Cloud")

        if submit:
            if name:
                update_stock(name, qty, price, user_name)
                st.success(f"Successfully pushed '{name}' to the cloud!")
                st.rerun()
            else:
                st.error("Please enter an Item Name.")

elif choice == "Business Insights":
    st.subheader("Performance Analysis")
    if not df.empty:
        total_val = df["Total Value"].sum()
        st.metric("Total Business Value", f"${total_val:,.2f}")

        # Graph - using the exact column names from the table
        fig = px.bar(df, x="Item Name", y="Quantity in Stock",
                     title="Current Stock Levels")
        st.plotly_chart(fig)
    else:
        st.error("No data to analyze.")
