import streamlit as st           # For building the website interface
from supabase import create_client  # For talking to your cloud database
import pandas as pd              # For organizing data into tables
import plotly.express as px      # For creating the charts/graphs

# --- 1. DATABASE CONNECTION ---
# These are your "keys" to enter the database. Keep them secret!
URL = "https://dcpvdapxzkaahyhpflul.supabase.co"
KEY = "sb_publishable_SiQMwIgDgLmckNQHUmO3SA_78UQBLHf"
# This line actually connects the app to the internet database
supabase = create_client(URL, KEY)

# Configure the browser tab title and make the layout wide
st.set_page_config(page_title="EE GREEN SOLUTIONS", layout="wide")
st.title("🌿 EE GREEN SOLUTIONS: Cloud Stock Manager")

# --- 2. THE SIDEBAR ---
# Creates a text box on the left so we know who is logging the data
user_name = st.sidebar.text_input("Enter Your Name (Staff/Owner)", "Admin")

# --- 3. HELPER FUNCTIONS (The "Brains") ---


def fetch_data():
    """This function pulls the latest stock list from the cloud"""
    # Ask Supabase to select everything (*) from the 'inventory' table
    response = supabase.table("inventory").select("*").execute()
    # Turn that data into a clean table (DataFrame) using Pandas
    return pd.DataFrame(response.data)


def update_stock(name, qty, price, user):
    """This function sends new or updated info to the cloud"""
    total = qty * price  # Calculate the math automatically
    # Prepare the 'package' of data to send
    data = {
        "item_name": name,
        "quantity": qty,
        "price": price,
        "total_value": total,
        "updated_by": user
    }
    # 'Upsert' means: Update if the name exists, Insert if it's new
    supabase.table("inventory").upsert(data, on_conflict="item_name").execute()


# --- 4. APP NAVIGATION ---
# Create a menu on the left side
menu = ["View Stock", "Add/Update Item", "Business Insights"]
choice = st.sidebar.selectbox("Navigation", menu)

# Immediately pull the latest data so the app is always up to date
df = fetch_data()

# --- 5. PAGE LOGIC ---

if choice == "View Stock":
    st.subheader("Live Inventory (Cloud Sync)")
    if not df.empty:
        # Show the table but only specific columns to keep it neat
        st.dataframe(
            df[["item_name", "quantity", "price", "total_value", "updated_by"]])
    else:
        st.write("No stock found in the database.")

elif choice == "Add/Update Item":
    st.subheader(f"Editing as: {user_name}")
    # 'st.form' makes sure the app doesn't refresh until you click 'Submit'
    with st.form("edit_form"):
        name = st.text_input("Item Name (e.g., Solar Panel)")
        qty = st.number_input("Quantity in Stock", min_value=0)
        price = st.number_input("Price per Unit", min_value=0.0)
        submit = st.form_submit_button("Push to Cloud")

        if submit:
            # When clicked, run our 'Brains' function from above
            update_stock(name, qty, price, user_name)
            st.success(f"Stock Updated successfully!")
            st.rerun()  # Refresh the app to show new data

elif choice == "Business Insights":
    st.subheader("Performance Analysis")
    if not df.empty:
        # Sum up the 'total_value' column for a grand total
        total_val = df["total_value"].sum()
        st.metric("Total Business Value", f"${total_val:,.2f}")

        # Create a bar chart: X-axis is the name, Y-axis is the quantity
        fig = px.bar(df, x="item_name", y="quantity", title="Stock Levels")
        st.plotly_chart(fig)  # Display the chart on the screen
    else:
        st.error("No data available to analyze yet.")
