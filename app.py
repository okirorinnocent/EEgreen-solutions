import streamlit as st
from supabase import create_client
import pandas as pd

# --- 1. DATABASE CONNECTION ---
# Replace these with your actual Supabase keys if they change
URL = "https://dcpvdapxzkaahyhpflul.supabase.co"
KEY = "sb_publishable_SiQMwIgDgLmckNQHUmO3SA_78UQBLHf"
supabase = create_client(URL, KEY)

# --- 2. THE AGRO-THEME (Visuals & Icon) ---
# Direct link to the Muddo Agro-Chemicals logo
LOGO_URL = "https://www.kcca.go.ug/media/kabd/listings/1614152862.JPG"

st.set_page_config(
    page_title="EE Agro-Chemicals",
    page_icon=LOGO_URL,
    layout="wide"
)

# Custom CSS for the appealing nature background
st.markdown(f"""
    <style>
    .stApp {{
        background: linear-gradient(to bottom, #f0f7f4, #ffffff);
    }}
    h1, h2, h3 {{
        color: #1b5e20;
    }}
    .stButton>button {{
        background-color: #2e7d32;
        color: white;
        border-radius: 8px;
    }}
    </style>
    """, unsafe_allow_html=True)

st.title("🌱 EE GREEN SOLUTIONS: Agro-Chemical Manager")

# --- 3. HELPER FUNCTIONS ---


def fetch_data():
    """Gets data from Supabase and does the math"""
    try:
        response = supabase.table("inventory").select("*").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            # Calculate Sold and Value on the fly
            df["Stock Sold Out"] = df["Total Stock Input"] - df["Stock Remaining"]
            df["Total Sales Value"] = df["Stock Sold Out"] * df["Price per Unit"]
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()


def update_stock(name, input_qty, remain_qty, price, user):
    """Saves the data including the 'Updated By' column"""
    data = {
        "Item Name": name,
        "Total Stock Input": input_qty,
        "Stock Remaining": remain_qty,
        "Price per Unit": price,
        "Updated By": user
    }
    supabase.table("inventory").upsert(data, on_conflict="Item Name").execute()


# --- 4. NAVIGATION ---
st.sidebar.image(LOGO_URL, width=150)
user_name = st.sidebar.text_input("Logged in as:", "Staff Member")
menu = ["Inventory Overview", "Log Sales & Stock", "Financial Insights"]
choice = st.sidebar.selectbox("Menu", menu)

df = fetch_data()

# --- 5. PAGES ---

if choice == "Inventory Overview":
    st.subheader("📦 Shop Shelf Status")
    if not df.empty:
        # Added 'Updated By' to the display table
        cols = ["Item Name", "Total Stock Input", "Stock Remaining",
                "Stock Sold Out", "Price per Unit", "Updated By"]
        st.dataframe(df[cols], use_container_width=True)
    else:
        st.info("No items found. Go to 'Log Sales' to add your first product!")

elif choice == "Log Sales & Stock":
    st.subheader(f"Update Stock - Done by: {user_name}")
    with st.form("agro_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Product Name")
            input_qty = st.number_input("Total Stock Input", min_value=0)
        with col2:
            price = st.number_input("Price per Unit ($)", min_value=0.0)
            remain_qty = st.number_input(
                "Current Stock Remaining", min_value=0)

        submit = st.form_submit_button("Save Changes")

        if submit:
            if name and (remain_qty <= input_qty):
                update_stock(name, input_qty, remain_qty, price, user_name)
                st.success(f"Successfully updated {name}!")
                st.rerun()
            else:
                st.error(
                    "Check your inputs! Name is required and remaining stock can't exceed input.")

elif choice == "Financial Insights":
    st.subheader("💰 Sales & Revenue Report")
    if not df.empty:
        total_rev = df["Total Sales Value"].sum()
        st.metric("Total Estimated Revenue", f"${total_rev:,.2f}")
        st.table(df[["Item Name", "Stock Sold Out",
                 "Total Sales Value", "Updated By"]])
    else:
        st.error("No data available.")
