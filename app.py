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

st.set_page_config(page_title="EE Agro-Chemicals", page_icon="🌱", layout="wide")

# --- 2. CLEAN READABILITY THEME ---
st.markdown(f"""
    <style>
    /* Clean light gray background */
    .stApp {{
        background-color: #f8f9fa;
    }}
    /* White cards with dark text for high contrast */
    .main .block-container {{
        background-color: #ffffff;
        padding: 2rem; 
        border-radius: 8px; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-top: 20px;
        color: #1a1a1a;
    }}
    /* Dark Green Headers */
    h1, h2, h3 {{
        color: #053e08 !important;
        font-weight: 700 !important;
    }}
    /* Make metrics stand out */
    [data-testid="stMetricValue"] {{
        font-size: 1.8rem !important;
        color: #2e7d32 !important;
    }}
    /* Style buttons for clarity */
    .stButton>button {{
        border-radius: 4px;
        height: 3em;
        width: 100%;
    }}
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
st.sidebar.header("EE AGRO-CHEMICALS")
user_name = st.sidebar.text_input("Seller Name:", "Staff")
menu = ["🛒 Record Sales", "📦 Inventory & Restock", "➕ Add New Product", "📈 Sales Report"]
choice = st.sidebar.selectbox("Go to:", menu)
df = fetch_data()

# --- 5. PAGES ---

if choice == "🛒 Record Sales":
    st.title("Daily Sales Counter")
    if not df.empty:
        # Search Bar
        search = st.text_input("🔍 Search product name...", "")
        filtered_df = df[df["Item Name"].str.contains(search, case=False)]

        for index, row in filtered_df.iterrows():
            if row['Stock Remaining'] > 0:
                with st.container():
                    col1, col2, col3 = st.columns([3, 2, 2])
                    with col1:
                        st.subheader(row['Item Name'])
                        st.write(f"Price: **UGX {row['Price per Unit']:,.0f}**")
                    with col2:
                        st.metric("Units Available", int(row['Stock Remaining']))
                    with col3:
                        qty_sold = st.number_input("Amount Sold", min_value=0, max_value=int(row['Stock Remaining']), key=f"sell_{index}")
                        if st.button("Confirm Sale ✅", key=f"btn_{index}"):
                            if qty_sold > 0:
                                new_rem = row['Stock Remaining'] - qty_sold
                                update_db(row['Item Name'], row['Total Stock Input'], new_rem, row['Price per Unit'], user_name)
                                st.success(f"Sold {qty_sold} units!")
                                st.rerun()
                st.divider()
    else:
        st.info("No items in stock. Please add products first.")

elif choice == "📦 Inventory & Restock":
    st.title("Stock Management")
    if not df.empty:
        # Low Stock Alert
        low = df[df["Stock Remaining"] < 5]
        if not low.empty:
            st.error(f"⚠️ Warning: {', '.join(low['Item Name'].tolist())} are running low!")
            if st.button("📧 Email Manager for Stock"):
                msg = f"Restock needed for: {', '.join(low['Item Name'].tolist())}"
                st.components.v1.html(f"<script>sendEmail('{msg}')</script>", height=0)

        for index, row in df.iterrows():
            with st.expander(f"⚙️ Manage {row['Item Name']}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Current Total Stock:** {row['Total Stock Input']}")
                    st.write(f"**Currently on Shelf:** {row['Stock Remaining']}")
                    add_stock = st.number_input("Add New Shipment Qty", min_value=0, key=f"add_{index}")
                    new_p = st.number_input("Update Price", value=float(row['Price per Unit']), key=f"p_{index}")
                    if st.button("Update Stock 🔄", key=f"up_{index}"):
                        new_input = row['Total Stock Input'] + add_stock
                        new_rem = row['Stock Remaining'] + add_stock
                        update_db(row['Item Name'], new_input, new_rem, new_p, user_name)
                        st.success("Inventory updated!")
                        st.rerun()
                with c2:
                    st.write("---")
                    if st.button("🗑️ Delete Product Forever", key=f"del_{index}"):
                        supabase.table("inventory").delete().eq("Item Name", row['Item Name']).execute()
                        st.rerun()

elif choice == "➕ Add New Product":
    st.title("Add New Chemical")
    with st.form("new_prod"):
        name = st.text_input("Product Name")
        q = st.number_input("Initial Quantity", min_value=1)
        p = st.number_input("Price (UGX)", min_value=0)
        if st.form_submit_button("Save Product"):
            update_db(name, q, q, p, user_name)
            st.success(f"{name} added to inventory!")

elif choice == "📈 Sales Report":
    st.title("Shop Financials")
    if not df.empty:
        st.metric("Total Revenue Collected", f"UGX {df['Total Sales Value'].sum():,.0f}")
        display_df = df[["Item Name", "Stock Sold Out", "Stock Remaining", "Total Sales Value"]]
        display_df.columns = ["Product Name", "Units Sold", "In Stock", "Revenue (UGX)"]
        st.table(display_df)