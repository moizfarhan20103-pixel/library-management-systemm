import streamlit as st
import sqlite3
import re
from datetime import datetime, timedelta

# Page setup
st.set_page_config(page_title="Library Management System - AGC", layout="wide")

DB_NAME = "library_administration.db"

# ----------------- DATABASE SETUP -----------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        password TEXT NOT NULL,
        secQuestion TEXT NOT NULL,
        secAnswer TEXT NOT NULL,
        Phone INTEGER NOT NULL,
        City TEXT NOT NULL
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS books (
        Book_Id INTEGER PRIMARY KEY,
        Book_name TEXT NOT NULL,
        Author TEXT NOT NULL,
        Availiability BOOLEAN NOT NULL DEFAULT 1
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS students (
        Roll_no INTEGER NOT NULL,
        name TEXT NOT NULL,
        Student_Id INTEGER PRIMARY KEY,
        class TEXT NOT NULL,
        Phone_number INTEGER NOT NULL,
        Books_Issued INTEGER NOT NULL DEFAULT 0,
        Fine INTEGER NOT NULL DEFAULT 0
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS issue (
        BID INTEGER NOT NULL,
        SID INTEGER NOT NULL,
        Issue_date TEXT NOT NULL,
        Return_date TEXT NOT NULL,
        PRIMARY KEY(BID, SID),
        FOREIGN KEY(BID) REFERENCES books(Book_Id),
        FOREIGN KEY(SID) REFERENCES students(Student_Id)
    )""")
    conn.commit()
    conn.close()

init_db()

def get_connection():
    return sqlite3.connect(DB_NAME)

# ----------------- SESSION STATE -----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.admin_user = ""

# ----------------- AUTHENTICATION MODULE -----------------
if not st.session_state.logged_in:
    st.title("Library Management System")
    st.caption("Asansol Girls' College | BCA Minor Project 2026")

    auth_tab = st.sidebar.radio("Navigation", ["Login", "Register Admin", "Forgot Password"])

    if auth_tab == "Login":
        st.subheader("Admin Login")
        with st.form("login_form"):
            uid = st.text_input("User ID")
            pwd = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")

            if submit:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT * FROM admin WHERE id = ? AND password = ?", (uid, pwd))
                user = cur.fetchone()
                conn.close()
                if user:
                    st.session_state.logged_in = True
                    st.session_state.admin_user = user[1]
                    st.rerun()
                else:
                    st.error("Invalid User ID or Password.")

    elif auth_tab == "Register Admin":
        st.subheader("Register Admin Account")
        with st.form("reg_form"):
            uid = st.text_input("User ID (min 5 characters)")
            name = st.text_input("Full Name")
            pwd = st.text_input("Password", type="password")
            sec_q = st.selectbox("Security Question", [
                "What is your school name?",
                "What is your home name?",
                "What is your Father name?",
                "What is your pet name?"
            ])
            sec_a = st.text_input("Security Answer")
            phone = st.text_input("Phone Number (10 digits)")
            city = st.text_input("City")
            submit_reg = st.form_submit_button("Register")

            if submit_reg:
                if len(uid) < 5:
                    st.error("User ID must be at least 5 characters.")
                elif len(name) < 3:
                    st.error("Please enter a valid full name.")
                elif (len(pwd) < 8 or not re.search(r"[a-z]", pwd) or not re.search(r"[A-Z]", pwd)
                      or not re.search(r"[0-9]", pwd) or not re.search(r"[_@$]", pwd)):
                    st.error("Password must be 8+ chars with uppercase, lowercase, digit, and [_@$].")
                elif not re.fullmatch(r"[6-9]\d{9}", phone):
                    st.error("Phone must be 10 digits starting with 6-9.")
                else:
                    conn = get_connection()
                    cur = conn.cursor()
                    try:
                        cur.execute("INSERT INTO admin VALUES (?, ?, ?, ?, ?, ?, ?)",
                                    (uid, name, pwd, sec_q, sec_a, int(phone), city))
                        conn.commit()
                        st.success("Admin registered successfully! You can now log in.")
                    except sqlite3.IntegrityError:
                        st.error("Admin User ID already exists.")
                    finally:
                        conn.close()

    elif auth_tab == "Forgot Password":
        st.subheader("Reset Password")
        f_uid = st.text_input("Enter User ID")
        f_q = st.selectbox("Select Security Question", [
            "What is your school name?",
            "What is your home name?",
            "What is your Father name?",
            "What is your pet name?"
        ])
        f_a = st.text_input("Enter Security Answer", type="password")
        new_pwd = st.text_input("New Password", type="password")
        confirm_pwd = st.text_input("Confirm New Password", type="password")

        if st.button("Reset Password"):
            if new_pwd != confirm_pwd:
                st.error("Passwords do not match.")
            else:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT * FROM admin WHERE id = ? AND secQuestion = ? AND secAnswer = ?",
                            (f_uid, f_q, f_a))
                record = cur.fetchone()
                if record:
                    cur.execute("UPDATE admin SET password = ? WHERE id = ?", (new_pwd, f_uid))
                    conn.commit()
                    st.success("Password reset successfully! Return to Login.")
                else:
                    st.error("Verification failed. Check your ID and security answer.")
                conn.close()

# ----------------- MAIN APPLICATION (LOGGED IN) -----------------
else:
    st.sidebar.markdown(f"**Logged in as:** {st.session_state.admin_user}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

    menu = st.sidebar.selectbox("Navigation Menu", [
        "Dashboard (Issued Books)",
        "Book Circulation (Issue/Return/Renew)",
        "Add Books / Students",
        "Search Records",
        "Admin Tools"
    ])

    # 1. DASHBOARD
    if menu == "Dashboard (Issued Books)":
        st.header("Welcome To AGC Library Dashboard")
        search_col1, search_col2 = st.columns([1, 2])
        search_by = search_col1.selectbox("Filter By", ["All", "Student ID", "Book ID"])
        filter_val = search_col2.text_input("Enter ID (leave empty to view all)")

        conn = get_connection()
        cur = conn.cursor()
        query = """
            SELECT issue.BID as 'Book ID', issue.SID as 'Student ID', students.name as 'Student Name',
                   students.Fine as 'Fine (Rs)', books.Book_name as 'Book Name',
                   issue.Issue_date as 'Issue Date', issue.Return_date as 'Return Date'
            FROM books, students, issue
            WHERE issue.BID = books.Book_Id AND issue.SID = students.Student_Id
        """
        params = []
        if search_by == "Student ID" and filter_val:
            query += " AND issue.SID = ?"
            params.append(filter_val)
        elif search_by == "Book ID" and filter_val:
            query += " AND issue.BID = ?"
            params.append(filter_val)

        cur.execute(query, params)
        records = cur.fetchall()
        conn.close()

        if records:
            st.dataframe(records, use_container_width=True)
        else:
            st.info("No active issued books found matching criteria.")

    # 2. CIRCULATION (ISSUE, RENEW, RETURN)
    elif menu == "Book Circulation (Issue/Return/Renew)":
        st.header("Circulation Desk")
        circ_action = st.radio("Choose Action", ["Issue Book", "Renew Book", "Return Book"], horizontal=True)
        
        c_bid = st.number_input("Book ID", min_value=1, step=1)
        c_sid = st.number_input("Student ID", min_value=1, step=1)

        conn = get_connection()
        cur = conn.cursor()

        if circ_action == "Issue Book":
            if st.button("Issue Book"):
                cur.execute("SELECT Availiability FROM books WHERE Book_Id = ?", (c_bid,))
                book = cur.fetchone()
                cur.execute("SELECT Fine, Books_Issued FROM students WHERE Student_Id = ?", (c_sid,))
                student = cur.fetchone()

                if not book:
                    st.error("Book ID not found.")
                elif not student:
                    st.error("Student ID not found.")
                elif book[0] == 0:
                    st.warning("Book is currently unavailable (already issued).")
                elif student[0] > 100:
                    st.error("Cannot issue. Student fine exceeds Rs 100.")
                elif student[1] >= 3:
                    st.error("Limit reached: Student has already issued 3 books.")
                else:
                    today = datetime.now().strftime("%Y-%m-%d")
                    due = (datetime.now() + timedelta(days=15)).strftime("%Y-%m-%d")
                    cur.execute("INSERT INTO issue VALUES (?, ?, ?, ?)", (c_bid, c_sid, today, due))
                    cur.execute("UPDATE books SET Availiability = 0 WHERE Book_Id = ?", (c_bid,))
                    cur.execute("UPDATE students SET Books_Issued = Books_Issued + 1 WHERE Student_Id = ?", (c_sid,))
                    conn.commit()
                    st.success(f"Book {c_bid} issued to Student {c_sid} until {due}.")

        elif circ_action == "Renew Book":
            if st.button("Renew Book"):
                cur.execute("SELECT Return_date FROM issue WHERE BID = ? AND SID = ?", (c_bid, c_sid))
                row = cur.fetchone()
                if not row:
                    st.error("No active issue record for this Book and Student.")
                else:
                    due_date = datetime.strptime(row[0], "%Y-%m-%d")
                    today = datetime.now()
                    if today > due_date:
                        overdue = (today - due_date).days
                        cur.execute("UPDATE students SET Fine = Fine + ? WHERE Student_Id = ?", (overdue, c_sid))
                        st.warning(f"Overdue by {overdue} days. Fine added.")

                    new_issue = today.strftime("%Y-%m-%d")
                    new_due = (today + timedelta(days=15)).strftime("%Y-%m-%d")
                    cur.execute("UPDATE issue SET Issue_date = ?, Return_date = ? WHERE BID = ?", (new_issue, new_due, c_bid))
                    conn.commit()
                    st.success(f"Book renewed. New return date is {new_due}.")

        elif circ_action == "Return Book":
            if st.button("Return Book"):
                cur.execute("SELECT Return_date FROM issue WHERE BID = ? AND SID = ?", (c_bid, c_sid))
                row = cur.fetchone()
                if not row:
                    st.error("No record found matching this Book ID and Student ID.")
                else:
                    due_date = datetime.strptime(row[0], "%Y-%m-%d")
                    today = datetime.now()
                    if today > due_date:
                        fine_amt = (today - due_date).days
                        cur.execute("UPDATE students SET Fine = Fine + ? WHERE Student_Id = ?", (fine_amt, c_sid))
                        st.warning(f"Late return! Penalty fine of Rs {fine_amt} applied.")
                    else:
                        st.success("Book returned on time.")

                    cur.execute("DELETE FROM issue WHERE BID = ? AND SID = ?", (c_bid, c_sid))
                    cur.execute("UPDATE books SET Availiability = 1 WHERE Book_Id = ?", (c_bid,))
                    cur.execute("UPDATE students SET Books_Issued = MAX(0, Books_Issued - 1) WHERE Student_Id = ?", (c_sid,))
                    conn.commit()
        conn.close()

    # 3. ADD BOOKS / STUDENTS
    elif menu == "Add Books / Students":
        tab1, tab2 = st.tabs(["Add Book", "Add Student"])

        with tab1:
            st.subheader("Add New Book")
            b_id = st.number_input("Book ID", min_value=1, step=1, key="add_bid")
            b_name = st.text_input("Book Name")
            b_author = st.text_input("Book Author")
            if st.button("Save Book"):
                if b_name and b_author:
                    conn = get_connection()
                    cur = conn.cursor()
                    try:
                        cur.execute("INSERT INTO books VALUES (?, ?, ?, 1)", (b_id, b_name, b_author))
                        conn.commit()
                        st.success("Book added successfully!")
                    except sqlite3.IntegrityError:
                        st.error("Book ID already exists.")
                    finally:
                        conn.close()
                else:
                    st.error("All fields are required.")

        with tab2:
            st.subheader("Add New Student")
            s_roll = st.number_input("Class Roll Number", min_value=1, step=1)
            s_name = st.text_input("Student Name")
            s_id = st.number_input("Student ID", min_value=1, step=1)
            s_class = st.text_input("Student Class/Department")
            s_phone = st.text_input("Phone Number (10 digits)")
            if st.button("Save Student"):
                if s_name and s_class and len(s_phone) == 10 and s_phone.isdigit():
                    conn = get_connection()
                    cur = conn.cursor()
                    try:
                        cur.execute("""
                            INSERT INTO students (Roll_no, name, Student_Id, class, Phone_number, Books_Issued, Fine)
                            VALUES (?, ?, ?, ?, ?, 0, 0)
                        """, (s_roll, s_name, s_id, s_class, int(s_phone)))
                        conn.commit()
                        st.success("Student added successfully!")
                    except sqlite3.IntegrityError:
                        st.error("Student ID or Roll No already registered.")
                    finally:
                        conn.close()
                else:
                    st.error("Please enter valid student details and a 10-digit phone number.")

    # 4. SEARCH RECORDS
    elif menu == "Search Records":
        st.header("Search Database")
        search_target = st.radio("Search Target", ["Books", "Students"], horizontal=True)
        search_term = st.text_input("Enter search keywords")

        conn = get_connection()
        cur = conn.cursor()

        if search_target == "Books":
            cur.execute("""
                SELECT Book_Id, Book_name, Author,
                       CASE WHEN Availiability = 1 THEN 'Available' ELSE 'Issued' END as Status
                FROM books
                WHERE Book_name LIKE ? OR Author LIKE ? OR Book_Id LIKE ?
            """, (f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"))
            results = cur.fetchall()
            st.dataframe(results, use_container_width=True)

        elif search_target == "Students":
            cur.execute("""
                SELECT Student_Id, Roll_no, name, class, Phone_number, Books_Issued, Fine
                FROM students
                WHERE name LIKE ? OR Student_Id LIKE ?
            """, (f"%{search_term}%", f"%{search_term}%"))
            results = cur.fetchall()
            st.dataframe(results, use_container_width=True)

        conn.close()

    # 5. ADMIN TOOLS
    elif menu == "Admin Tools":
        st.header("Admin Operations")
        sub_tool = st.selectbox("Select Action", ["Clear Fine", "Delete Entry"])

        conn = get_connection()
        cur = conn.cursor()

        if sub_tool == "Clear Fine":
            st.subheader("Clear Outstanding Student Fine")
            target_sid = st.number_input("Enter Student ID to Clear Fine", min_value=1, step=1)
            if st.button("Clear Dues"):
                cur.execute("SELECT Fine FROM students WHERE Student_Id = ?", (target_sid,))
                row = cur.fetchone()
                if row:
                    cur.execute("UPDATE students SET Fine = 0 WHERE Student_Id = ?", (target_sid,))
                    conn.commit()
                    st.success(f"Fine cleared for Student {target_sid}.")
                else:
                    st.error("Student not found.")

        elif sub_tool == "Delete Entry":
            st.subheader("Remove Book or Student")
            del_type = st.radio("Target Type", ["Book", "Student"], horizontal=True)
            del_id = st.number_input("Enter ID", min_value=1, step=1)
            if st.button("Delete"):
                if del_type == "Book":
                    cur.execute("DELETE FROM books WHERE Book_Id = ?", (del_id,))
                    st.success(f"Book {del_id} removed from database.")
                else:
                    cur.execute("DELETE FROM students WHERE Student_Id = ?", (del_id,))
                    st.success(f"Student {del_id} removed from database.")
                conn.commit()

        conn.close()