import streamlit as st
from supabase import create_client
import pandas as pd

# --- 1. CONFIG & CONNECTIONS ---
URL = "https://dcpvdapxzkaahyhpflul.supabase.co"
KEY = "sb_publishable_SiQMwIgDgLmckNQHUmO3SA_78UQBLHf"
supabase = create_client(URL, KEY)

# EMAILJS CONFIG
EMAILJS_SERVICE_ID = "service_4nf5h0s"
EMAILJS_TEMPLATE_ID = "template_hxqoaek"
EMAILJS_PUBLIC_KEY = "Lb8MwfQXoUKQmNGGh"

st.set_page_config(page_title="EE Agro-Chemicals",
                   page_icon="🌱", layout="wide")

# --- 2. THEME & EMAIL SCRIPT ---
st.markdown(f"""
    <style>
    .stApp {{
        background: url("https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&q=80&w=2000");
        background-size: cover; background-attachment: fixed;
    }}
    .main .block-container {{
        background-color: rgba(255, 255, 255, 0.95);
        padding: 2rem; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }}
    .stButton>button {{ width: 100%; border-radius: 10px; font-weight: bold; }}
    </style>
    
    <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/@emailjs/browser@3/dist/email.min.js"></script>
    <script type="text/javascript">
        (function() {{ emailjs.init("{EMAILJS_PUBLIC_KEY}"); }})();
        function sendEmail(message) {{
            emailjs.send("{EMAILJS_SERVICE_ID}", "{EMAILJS_TEMPLATE_ID}", {{
                message: message, to_name: "Manager"
            }}).then(function() {{ alert("Email Sent!"); }}, function(err) {{ alert("Error!"); }});
        }}
    </script>
    """, unsafe_allow_html=True)

# --- 3. DATABASE FUNCTIONS ---


def fetch_data():
    try:
        response = supabase.table("inventory").select("*").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            # Simple Logic: Sold = Total Input - What is left
            df["Stock Sold Out"] = df["Total Stock Input"] - df["Stock Remaining"]
            df["Total Sales Value"] = df["Stock Sold Out"] * df["Price per Unit"]
        return df
    except:
        return pd.DataFrame()


def update_db(name, input_qty, remain_qty, price, user):
    data = {"Item Name": name, "Total Stock Input": input_qty,
            "Stock Remaining": remain_qty, "Price per Unit": price, "Updated By": user}
    supabase.table("inventory").upsert(data, on_conflict="Item Name").execute()


# --- 4. NAVIGATION ---
st.sidebar.title("🌿 EE AGRO")
user_name = st.sidebar.text_input("Seller Name:", "Staff")
menu = ["🛒 Sell & Manage Stock", "➕ Add New Product", "📈 Sales Reports"]
choice = st.sidebar.selectbox("Menu", menu)
df = fetch_data()

# --- 5. PAGE LOGIC ---

if choice == "🛒 Sell & Manage Stock":
    st.title("Current Shop Inventory")

    if not df.empty:
        # Check for Low Stock
        low_items = df[df["Stock Remaining"] < 5]
        if not low_items.empty:
            st.warning(
                f"📢 Need to restock: {', '.join(low_items['Item Name'].tolist())}")
            if st.button("📧 Send Low Stock Alert to Manager"):
                msg = f"Stock is low for: {', '.join(low_items['Item Name'].tolist())}"
                st.components.v1.html(
                    f"<script>sendEmail('{msg}')</script>", height=0)

        # Show items in a simple list
        for index, row in df.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

                with col1:
                    st.write(f"### {row['Item Name']}")
                    st.caption(f"Price: UGX {row['Price per Unit']:,.0f}")

                with col2:
                    st.write(f"**Stock Left: {row['Stock Remaining']}**")

                with col3:
                    # THE SIMPLIFIED PART: Just enter how many were sold
                    sold_now = st.number_input("Amount Sold", min_value=0, max_value=int(
                        row['Stock Remaining']), key=f"s_{index}")

                with col4:
                    if st.button("Confirm Sale ✅", key=f"btn_{index}"):
                        if sold_now > 0:
                            new_rem = row['Stock Remaining'] - sold_now
                            update_db(row['Item Name'], row['Total Stock Input'],
                                      new_rem, row['Price per Unit'], user_name)
                            st.success(f"Sold {sold_now}!")
                            st.rerun()
                st.divider()

                # Hidden Delete Option
                if st.checkbox(f"Delete {row['Item Name']}?", key=f"del_chk_{index}"):
                    if st.button("Confirm Delete 🗑️", key=f"del_btn_{index}"):
                        supabase.table("inventory").delete().eq(
                            "Item Name", row['Item Name']).execute()
                        st.rerun()

elif choice == "➕ Add New Product":
    st.title("Register New Product")
    with st.form("add_form"):
        name = st.text_input("Chemical Name")
        qty = st.number_input("Initial Stock Quantity", min_value=1)
        price = st.number_input("Price per Unit (UGX)", min_value=0)
        if st.form_submit_button("Add to System"):
            update_db(name, qty, qty, price, user_name)
            st.success(f"{name} added to inventory!")

elif choice == "📈 Sales Reports":
    st.title("Financial Overview")
    if not df.empty:
        total_rev = df['Total Sales Value'].sum()
        st.metric("Total Revenue Collected", f"UGX {total_rev:,.0f}")

        # Simple table for the user
        report_df = df[["Item Name", "Stock Sold Out",
                        "Stock Remaining", "Total Sales Value"]]
        report_df.columns = ["Product", "Units Sold",
                             "In Stock", "Revenue (UGX)"]
        st.table(report_df)
    else:
        st.info("No sales data yet.")
