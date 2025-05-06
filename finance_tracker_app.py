import streamlit as st
import pymysql
from datetime import date
import smtplib
import random

# Set Streamlit page configuration
st.set_page_config(page_title="💰 Personal Finance Tracker", layout="wide")

# DB connection using pymysql
conn = pymysql.connect(
    host="localhost",
    user="root",
    password="Root",
    database="finance_tracker"
)
cursor = conn.cursor()

# Email configuration
def send_email(email, otp):
    sender_email = "newiconsz@gmail.com"
    sender_password = "balpqmghtxbzwctp"
    receiver_email = email

    message = f"Subject: Your OTP\n\nYour OTP is: {otp}. Valid for 5 minutes!"

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message)
        return True
    except Exception as e:
        st.error(f"Error sending email: {e}")
        return False

# Database functions
def add_user(username, email, password):
    query = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
    cursor.execute(query, (username, email, password))
    conn.commit()

def get_user_id(username, password):
    query = "SELECT user_id FROM users WHERE username = %s AND password = %s"
    cursor.execute(query, (username, password))
    result = cursor.fetchone()
    return result[0] if result else None

def get_username(user_id):
    query = "SELECT username FROM users WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    result = cursor.fetchone()
    return result[0] if result else None

def add_transaction(user_id, amount, category, t_type, t_date, description):
    query = "INSERT INTO transactions (user_id, amount, category, type, date, description) VALUES (%s, %s, %s, %s, %s, %s)"
    cursor.execute(query, (user_id, amount, category, t_type, t_date, description))
    conn.commit()

def get_transactions_by_date(user_id):
    query = "SELECT date, category, amount, description, type FROM transactions WHERE user_id = %s ORDER BY date DESC"
    cursor.execute(query, (user_id,))
    return cursor.fetchall()

# Main App
def main():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.show_register = False
        st.session_state.reg_data = None
        st.session_state.reg_otp = None

    st.sidebar.title("User Authentication")

    # Displaying the app name with the money bag emoji 💰
    st.markdown("<h1 style='text-align: center; color: green;'>💰 Personal Finance Tracker</h1>", unsafe_allow_html=True)

    if not st.session_state.logged_in:
        if not st.session_state.show_register:
            st.sidebar.subheader("Login")
            username = st.sidebar.text_input("Username", placeholder="Enter username")
            password = st.sidebar.text_input("Password", type="password", placeholder="Enter password")
            
            if st.sidebar.button("Login"):
                uid = get_user_id(username, password)
                if uid:
                    st.session_state.logged_in = True
                    st.session_state.user_id = uid
                    st.experimental_rerun()
                else:
                    st.sidebar.error("Invalid credentials")
            
            if st.sidebar.button("Switch to Registration"):
                st.session_state.show_register = True
                st.experimental_rerun()
        
        else:
            st.sidebar.subheader("Registration")
            new_username = st.sidebar.text_input("New Username", placeholder="Choose username")
            new_email = st.sidebar.text_input("Email", placeholder="Enter email")
            new_password = st.sidebar.text_input("New Password", type="password", placeholder="Choose password")
            
            if st.sidebar.button("Send OTP"):
                if new_username and new_email and new_password:
                    otp = str(random.randint(100000, 999999))
                    st.session_state.reg_otp = otp
                    st.session_state.reg_data = (new_username, new_email, new_password)
                    
                    if send_email(new_email, otp):
                        st.sidebar.success(f"OTP sent to {new_email}")
                    else:
                        st.sidebar.error("Failed to send OTP")
                else:
                    st.sidebar.warning("Please fill all fields")

            if "reg_otp" in st.session_state:
                entered_otp = st.sidebar.text_input("Enter OTP", placeholder="6-digit OTP")
                if st.sidebar.button("Verify OTP & Register"):
                    if entered_otp == st.session_state.reg_otp:
                        username, email, password = st.session_state.reg_data
                        add_user(username, email, password)
                        st.session_state.registration_success = True
                        st.session_state.show_register = False
                        del st.session_state.reg_otp
                        del st.session_state.reg_data
                        st.experimental_rerun()
                    else:
                        st.sidebar.error("Invalid OTP")
            
            if st.sidebar.button("Back to Login"):
                st.session_state.show_register = False
                st.experimental_rerun()

    if st.session_state.logged_in:
        user_name = get_username(st.session_state.user_id)
        st.title(f"💰 Welcome, {user_name}!")

        # Add Transaction
        st.header("➕ Add Transaction")
        amount = st.number_input("Amount", min_value=0.0, format="%.2f")
        
        # Select Type of Transaction (Income or Expense)
        t_type = st.radio("Transaction Type", ['income', 'expense'])
        
        # Categories specific to Income or Expense
        if t_type == 'income':
            income_categories = ["Salary", "Freelance", "Investments", "Gifts", "Others"]
            category = st.selectbox("Select Income Category", income_categories)
        else:
            expense_categories = ["Food", "Transport", "Entertainment", "Utilities", "Family Expenditure", "Healthcare", "Miscellaneous"]
            category = st.selectbox("Select Expense Category", expense_categories)
        
        description = st.text_input("Description", placeholder="Describe transaction")
        
        if st.button("Add Transaction"):
            if amount > 0 and category:
                add_transaction(st.session_state.user_id, amount, category, t_type, date.today(), description)
                st.success("Transaction added!")
                st.experimental_rerun()
            else:
                st.error("Please fill all fields")

        # Display Transactions
        st.header("📖 Transaction Diary")
        
        # Income Transactions
        with st.expander("Income Transactions"):
            income_data = [t for t in get_transactions_by_date(st.session_state.user_id) if t[4] == 'income']
            if income_data:
                total_income = sum(t[2] for t in income_data)
                for t in income_data:
                    st.write(f"📅 {t[0].strftime('%Y-%m-%d')} | {t[1]} | ₹{t[2]:.2f} - {t[3]}")
                st.subheader(f"Total Income: ₹{total_income:.2f}")
            else:
                st.info("No income transactions")

        # Expense Transactions
        with st.expander("Expense Transactions"):
            expense_data = [t for t in get_transactions_by_date(st.session_state.user_id) if t[4] == 'expense']
            if expense_data:
                total_expense = sum(t[2] for t in expense_data)
                for t in expense_data:
                    st.write(f"📅 {t[0].strftime('%Y-%m-%d')} | {t[1]} | ₹{t[2]:.2f} - {t[3]}")
                st.subheader(f"Total Expenses: ₹{total_expense:.2f}")
            else:
                st.info("No expense transactions")

        # Logout Button
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.experimental_rerun()

    else:
        if st.session_state.show_register:
            st.title("Registration with OTP")
            st.info("Please complete registration in the sidebar")
        else:
            st.title("Login")
            if st.session_state.get("registration_success"):
                st.success("🎉 Registration successful! Please login.")
                del st.session_state.registration_success
            st.info("Please login using the sidebar")

if __name__ == "__main__":
    main()
