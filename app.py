import streamlit as st
from supabase import create_client
import pandas as pd

# --- 1. CONFIG & CONNECTIONS ---
URL = "https://dcpvdapxzkaahyhpflul.supabase.co"
KEY = "sb_publishable_SiQMwIgDgLmckNQHUmO3SA_78UQBLHf"
supabase = create_client(URL, KEY)

# --- EMAILJS CONFIG (REPLACE THESE WITH YOUR ACTUAL KEYS) ---
EMAILJS_SERVICE_ID = "service_4nf5h0s"
EMAILJS_TEMPLATE_ID = "template_hxqoaek"
EMAILJS_PUBLIC_KEY = "Lb8MwfQXoUKQmNGGh"

st.set_page_config(page_title="EE Agro-Chemicals",
                   page_icon="🌱", layout="wide")

# --- 2. CUSTOM CSS & BACKGROUND ---
st.markdown(f"""
    <style>
    .stApp {{
        background: url("https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&q=80&w=2000");
        background-size: cover;
        background-attachment: fixed;
    }}
    .main .block-container {{
        background-color: rgba(255, 255, 255, 0.9);
        padding: 2rem; border-radius: 15px; margin-top: 20px;
    }}
    </style>
    
    <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/@emailjs/browser@3/dist/email.min.js"></script>
    <script type="text/javascript">
        (function() {{
            emailjs.init("{EMAILJS_PUBLIC_KEY}");
        }})();
        
        function sendEmail(message) {{
            emailjs.send("{EMAILJS_SERVICE_ID}", "{EMAILJS_TEMPLATE_ID}", {{
                message: message,
                to_name: "Manager"
            }}).then(function() {{
                alert("Email Sent Successfully!");
            }}, function(error) {{
                alert("Failed to send email: " + JSON.stringify(error));
            }});
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


def update_stock(name, input_qty, remain_qty, price, user):
    data = {"Item Name": name, "Total Stock Input": input_qty,
            "Stock Remaining": remain_qty, "Price per Unit": price, "Updated By": user}
    supabase.table("inventory").upsert(data, on_conflict="Item Name").execute()


def delete_item(name):
    supabase.table("inventory").delete().eq("Item Name", name).execute()
    st.rerun()


# --- 4. APP LOGIC ---
user_name = st.sidebar.text_input("👤 User:", "Staff Member")
menu = ["📈 Dashboard & Edit", "➕ Add New Item", "💰 Financials"]
choice = st.sidebar.selectbox("Menu", menu)
df = fetch_data()

if choice == "📈 Dashboard & Edit":
    st.title("📦 Inventory Management")

    if not df.empty:
        low_stock_items = df[df["Stock Remaining"] < 5]
        if not low_stock_items.empty:
            item_list = ", ".join(low_stock_items["Item Name"].tolist())
            st.error(f"⚠️ LOW STOCK: {item_list}")

            # This button triggers the Javascript Email Function
            email_msg = f"Alert! The following items are low in stock: {item_list}. Please restock immediately."
            if st.button("📧 Send Real Email to Manager"):
                st.components.v1.html(
                    f"<script>sendEmail('{email_msg}')</script>", height=0)
                st.success("Email request triggered!")

        for index, row in df.iterrows():
            with st.expander(f"🛠️ {row['Item Name']} (Stock: {row['Stock Remaining']})"):
                c1, c2, c3 = st.columns([2, 1, 1])
                new_rem = c1.number_input("New Stock", value=int(
                    row['Stock Remaining']), key=f"r_{index}")
                if c2.button("Save ✅", key=f"s_{index}"):
                    update_stock(row['Item Name'], row['Total Stock Input'],
                                 new_rem, row['Price per Unit'], user_name)
                    st.rerun()
                if c3.button("Delete 🗑️", key=f"d_{index}"):
                    delete_item(row['Item Name'])

elif choice == "➕ Add New Item":
    with st.form("add"):
        name = st.text_input("Product Name")
        qty = st.number_input("Stock Input", min_value=1)
        pr = st.number_input("Price (UGX)", min_value=0)
        if st.form_submit_button("Add Item") and name:
            update_stock(name, qty, qty, pr, user_name)
            st.success("Added!")

elif choice == "💰 Financials":
    st.metric("Total Revenue", f"UGX {df['Total Sales Value'].sum():,.0f}")
    st.bar_chart(df.set_index("Item Name")["Total Sales Value"])
