import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime
import pandas as pd

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

# MongoDB connection
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

books_col = db["books"]
lenders_col = db["lenders"]
issued_col = db["issued_books"]

st.set_page_config(page_title="Book Lending Admin", layout="wide")
st.title("📚 Book Lending Admin Panel")

# Utility functions
def get_books():
    return [b['title'] for b in books_col.find()]

def get_lenders():
    return [l['name'] for l in lenders_col.find()]

# Tabs: Issue + View
tab1, tab2 = st.tabs(["➕ Issue Book", "📖 View Issued Books"])

# ========== TAB 1: ISSUE BOOK ==========
with tab1:
    st.subheader("Issue a Book")

    # -- Add New Book Section --
    with st.expander("➕ Add New Book"):
        new_book_title = st.text_input("Book Title", key="new_book_title")
        if st.button("Add Book"):
            if new_book_title:
                if books_col.find_one({"title": new_book_title}):
                    st.warning("Book already exists.")
                else:
                    books_col.insert_one({"title": new_book_title})
                    st.success("Book added successfully.")
                    st.rerun()  # Re-run the app to update the book list
            else:
                st.error("Please enter a book title.")

    # -- Issue Form --
    books = get_books()
    lenders = get_lenders()

    book_title = st.selectbox("Select Book", options=books)
    lender_name = st.selectbox("Select Lender", options=lenders + ["➕ Add New Lender"])

    if lender_name == "➕ Add New Lender":
        st.markdown("### Add Lender Details")
        new_name = st.text_input("Full Name", key="new_lender_name")
        new_id = st.text_input("Student/Employee ID", key="new_lender_id")

        if st.button("Save Lender"):
            if new_name and new_id:
                if lenders_col.find_one({"id": new_id}):
                    st.warning("Lender with this ID already exists.")
                else:
                    lenders_col.insert_one({"name": new_name, "id": new_id})
                    st.success("Lender added successfully.")
                    st.rerun()  # Re-run to refresh the lender list
            else:
                st.error("Please fill all fields.")
    else:
        lender_doc = lenders_col.find_one({"name": lender_name})
        issue_date = st.date_input("Issue Date", datetime.today())

        if st.button("Issue Book"):
            if lender_doc:
                issued_col.insert_one({
                    "book_title": book_title,
                    "borrower": lender_name,
                    "borrower_id": lender_doc['id'],
                    "issue_date": issue_date.strftime("%Y-%m-%d"),
                    "returned": False
                })
                st.success("Book issued successfully.")

# ========== TAB 2: VIEW ISSUED BOOKS ==========
with tab2:
    st.subheader("Issued Books")

    search = st.text_input("🔍 Search by Book or Borrower")
    query = {}

    if search:
        query = {
            "$or": [
                {"book_title": {"$regex": search, "$options": "i"}},
                {"borrower": {"$regex": search, "$options": "i"}}
            ]
        }

    records = list(issued_col.find(query))
    if records:
        for record in records:
            record["_id"] = str(record["_id"])

        df = pd.DataFrame(records)
        df = df.rename(columns={
            "book_title": "Book",
            "borrower": "Borrower",
            "borrower_id": "ID",
            "issue_date": "Issued On",
            "returned": "Returned"
        })

        st.dataframe(df[["Book", "Borrower", "ID", "Issued On", "Returned"]], use_container_width=True)
    else:
        st.info("No issued books found.")
