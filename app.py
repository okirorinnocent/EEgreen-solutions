import streamlit as st
from supabase import create_client
import pandas as pd

# --- 1. DATABASE CONNECTION ---
# Paste your actual credentials here
URL = "https://dcpvdapxzkaahyhpflul.supabase.co"
KEY = "sb_publishable_SiQMwIgDgLmckNQHUmO3SA_78UQBLHf"
supabase = create_client(URL, KEY)

# --- 2. THE AGRO-THEME (Visuals) ---
st.set_page_config(page_title="EE Agro-Chemicals", layout="wide")

# Custom CSS to make it look like a Nature/Agro Shop
st.markdown("""
    <style>
    .stApp {
        background-color: #f0f7f4; /* Light Mint Green Background */
    }
    h1, h2, h3 {
        color: #1b5e20; /* Dark Forest Green Text */
    }
    .stButton>button {
        background-color: #2e7d32;
        color: white;
        border-radius: 8px;
        border: none;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🌱 EE GREEN SOLUTIONS: Agro-Chemical Manager")

# --- 3. HELPER FUNCTIONS ---


def fetch_data():
    """Gets data and calculates 'Sold' and 'Value' inside the app"""
    try:
        response = supabase.table("inventory").select("*").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            # THE MATH LOGIC
            # Stock Sold = Input - Remaining
            df["Stock Sold Out"] = df["Total Stock Input"] - df["Stock Remaining"]
            # Total Sales Value = Sold * Price
            df["Total Sales Value"] = df["Stock Sold Out"] * df["Price per Unit"]
        return df
    except:
        return pd.DataFrame()


def update_stock(name, input_qty, remain_qty, price, user):
    """Saves the raw numbers to the cloud"""
    data = {
        "Item Name": name,
        "Total Stock Input": input_qty,
        "Stock Remaining": remain_qty,
        "Price per Unit": price,
        "Updated By": user
    }
    supabase.table("inventory").upsert(data, on_conflict="Item Name").execute()


# --- 4. NAVIGATION ---
user_name = st.sidebar.text_input("Staff Name", "Admin")
menu = ["Inventory Overview", "Log Sales & Stock", "Financial Insights"]
choice = st.sidebar.selectbox("Menu", menu)

df = fetch_data()

# --- 5. PAGES ---

if choice == "Inventory Overview":
    st.subheader("📦 Shop Shelf Status")
    if not df.empty:
        # Displaying the calculated columns nicely
        cols = ["Item Name", "Total Stock Input",
                "Stock Remaining", "Stock Sold Out", "Price per Unit"]
        st.dataframe(df[cols], use_container_width=True)
    else:
        st.info("No items in inventory. Please add stock in the next tab.")

elif choice == "Log Sales & Stock":
    st.subheader(f"Update Stock Levels - Logger: {user_name}")
    with st.form("agro_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Product Name (e.g., NPK Fertilizer)")
            input_qty = st.number_input(
                "Total Stock Input (Bulk Buy)", min_value=0)
        with col2:
            price = st.number_input("Price per Unit ($)", min_value=0.0)
            remain_qty = st.number_input(
                "Current Stock Remaining", min_value=0)

        submit = st.form_submit_button("Save to Cloud")

        if submit:
            if name and (remain_qty <= input_qty):
                update_stock(name, input_qty, remain_qty, price, user_name)
                st.success(f"Updated {name} successfully!")
                st.rerun()
            elif remain_qty > input_qty:
                st.error(
                    "Error: Remaining stock cannot be more than the input stock!")
            else:
                st.warning("Please enter a product name.")

elif choice == "Financial Insights":
    st.subheader("💰 Sales & Revenue Report")
    if not df.empty:
        total_revenue = df["Total Sales Value"].sum()
        total_items_sold = df["Stock Sold Out"].sum()

        # Dashboard Style Metrics
        m1, m2 = st.columns(2)
        m1.metric("Total Items Sold", f"{int(total_items_sold)} units")
        m2.metric("Estimated Sales Revenue", f"${total_revenue:,.2f}")

        st.write("### Product Performance")
        st.table(df[["Item Name", "Stock Sold Out", "Total Sales Value"]])
    else:
        st.error("No sales data to display.")
