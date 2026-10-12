import streamlit as st
import mysql.connector
import pandas as pd
from datetime import date, timedelta

st.set_page_config(
    page_title="Sales Management System",
    page_icon="📊",
    layout="wide"
)

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="sales_management_system"
    )
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.title("Sales Management System")
    st.subheader("Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")

    if login_button:
        try:
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT user_id, username, password, branch_id, role
                FROM users
                WHERE username = %s AND password = %s
                """,
                (username, password)
            )
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            if user:
                role = user["role"].strip().lower()

                if role not in ["admin", "super admin"]:
                    st.error("Invalid user role.")
                elif role == "admin" and user["branch_id"] is None:
                    st.error("This admin has no assigned branch.")
                else:
                    st.session_state.logged_in = True
                    st.session_state.username = user["username"]
                    st.session_state.role = role
                    st.session_state.branch_id = user["branch_id"]

                    st.rerun()
            else:
                st.error("Invalid username or password.")
        except mysql.connector.Error as e:
            st.error(f"Database connection error: {e}")

    st.stop()

st.title(" Sales Management Dashboard")

st.write(f"Welcome, **{st.session_state.username}**")

if st.button("Logout"):
    for key in [
        "logged_in", "username", "role", "branch_id"
    ]:
        st.session_state.pop(key, None)
    st.rerun()
try:
    conn = get_connection()

    # Load branches for the Super Admin filter
    branch_df = pd.read_sql(
        "SELECT branch_id, branch_name FROM branches ORDER BY branch_name",
        conn
)

    st.sidebar.header("Report Filters")
    selected_branch = None

    if st.session_state.role == "super admin":
        branch_options = {
            "All branches": None
        }


        for _, row in branch_df.iterrows():
            branch_options[
                f'{row["branch_name"]} (ID: {row["branch_id"]})'
            ] = int(row["branch_id"])
        selected_label = st.sidebar.selectbox(
            "Select Branch",
            list(branch_options.keys())
        )
        selected_branch = branch_options[selected_label]
    else:
        st.sidebar.info("Showing your assigned branch only.")

    start_date = st.sidebar.date_input(
        "Start date",
        value=date(2024, 1, 1)
    )
    end_date = st.sidebar.date_input(
        "End date",
        value=date.today()
)
    customer_search = st.sidebar.text_input(
        "Search customer"
    )
    product_search = st.sidebar.text_input(
        "Search product"
    )
    status_filter = st.sidebar.selectbox(
        "Payment status",
        ["All", "open", "close"]
    )
    if start_date > end_date:
        st.error("Start date cannot be after end date.")
        conn.close()
        st.stop()

    query = """
        SELECT
            s.sales_id,
            s.sales_date,
            s.name AS customer_name,
            s.mobile_number,
            s.product_name,
            b.branch_name,
            s.gross_sales,
            s.received_amount,
            s.pending_amount,
            s.status
        FROM customer_sales_table s
        LEFT JOIN branches b
            ON s.branch_ID = b.branch_id
        WHERE s.sales_date BETWEEN %s AND %s
    """
    params = [start_date, end_date]

    if st.session_state.role == "admin":
        query += " AND s.branch_ID = %s"
        params.append(st.session_state.branch_id)

    elif selected_branch is not None:
        query += " AND s.branch_ID = %s"
        params.append(selected_branch)
    if customer_search:
        query += " AND s.name LIKE %s"
        params.append(f"%{customer_search}%")

    if product_search:
        query += " AND s.product_name LIKE %s"
        params.append(f"%{product_search}%")
    if status_filter != "All":
        query += " AND LOWER(s.status) = %s"
        params.append(status_filter)

    query += " ORDER BY s.sales_date DESC, s.sales_id DESC"

    sales_df = pd.read_sql(
        query, conn, params=params
    )

    conn.close()
    st.subheader("Sales Summary")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Gross Sales",
        f"₹{sales_df['gross_sales'].sum():,.2f}"
    )
    col2.metric(
        "Received Amount",
        f"₹{sales_df['received_amount'].sum():,.2f}"
    )
    col3.metric(
        "Pending Amount",
        f"₹{sales_df['pending_amount'].sum():,.2f}"
    )
    st.subheader("Customer Sales Report")

    st.dataframe(
        sales_df,
        use_container_width=True,
        hide_index=True
    )
    st.caption(f"Total records: {len(sales_df)}")
    csv_data = sales_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Report as CSV",
        data=csv_data,
        file_name="customer_sales_report.csv",
        mime="text/csv"
    )
except mysql.connector.Error as e:
    st.error(f"Database error: {e}")

except Exception as e:
    st.error(f"Application error: {e}")

password="root",
password="mysql123",



role = st.session_state.role
user_branch_id = st.session_state.branch_id

def get_branches(conn):
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT branch_id, branch_name FROM branches ORDER BY branch_name"
    )
    rows = cursor.fetchall()
    cursor.close()
    return rows 


def get_allowed_branch(conn):
    """Super Admin selects a branch; Admin uses assigned branch."""
    branches = get_branches(conn)

    if role == "admin":
        return user_branch_id

    branch_options = {
    f"{b['branch_name']} (ID: {b['branch_id']})": b["branch_id"]
    for b in branches
}

    if not branch_options:
        st.error("No branches found. Add branches in MySQL first.")
        return None

    selected = st.selectbox(
        "Select Branch",
        list(branch_options.keys())
    )
    return branch_options[selected]

role = st.session_state.role.strip().lower()

if role == "super admin":
    page_options = [
        "Customer Sales Report",
        "New Customer Sales Entry",
        "Payment Split Entry",
        "SQL Analysis"
    ]
else:
    page_options = [
        "Customer Sales Report",
        "New Customer Sales Entry",
        "Payment Split Entry"
    ]

page = st.sidebar.selectbox(
    "Select Page",
    page_options,
    key="main_page_navigation"
)


if page == "New Customer Sales Entry":
    st.subheader("➕ New Customer Sales Entry")

    conn = get_connection()

    try:
        branch_id = get_allowed_branch(conn)

        if branch_id is not None:
            with st.form("sales_entry_form"):
                sales_date = st.date_input("Sales Date", value=date.today())
                customer_name = st.text_input("Customer Name")
                mobile_number = st.text_input("Mobile Number")
                product_name = st.text_input("Product Name")
                gross_sales = st.number_input(
                    "Gross Sales (₹)", min_value=0.01, step=100.0
                )

                submitted = st.form_submit_button("Save Sales Entry")

            if submitted:
                if not customer_name.strip() or not product_name.strip():
                    st.error("Enter the customer name and product name.")
                elif not mobile_number.strip():
                    st.error("Enter the mobile number.")
                else:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO customer_sales_table
                        (branch_ID, sales_date, name, mobile_number,
                         product_name, gross_sales, received_amount,
                         pending_amount, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            branch_id,
                            sales_date,
                            customer_name.strip(),
                            mobile_number.strip(),
                            product_name.strip(),
                            gross_sales,
                            0,
                            gross_sales,
                            "open"
                        )
                    )
                    conn.commit()
                    new_sales_id = cursor.lastrowid
                    cursor.close()

                    st.success(
                        f"Sales entry saved successfully! Sales ID: {new_sales_id}"
                    )
                    st.info(
                        "Now use Payment Split Entry to record any payment received."
                    )
    except mysql.connector.Error as e:
        st.error(f"Database error: {e}")
    finally:
        conn.close()

elif page == "Payment Split Entry":
    st.subheader("💳 Payment Split Entry")

    conn = get_connection()

    try:
        cursor = conn.cursor(dictionary=True)

        # Admin sees only sales from their assigned branch.
        if role == "admin":
            cursor.execute(
                """
                SELECT sales_id, name, product_name, gross_sales,
                       received_amount, pending_amount, branch_ID
                FROM customer_sales_table
                WHERE branch_ID = %s AND pending_amount > 0
                ORDER BY sales_id DESC
                """,
                (user_branch_id,)
            )
        else:
            cursor.execute(
                """
                SELECT sales_id, name, product_name, gross_sales,
                       received_amount, pending_amount, branch_ID
                FROM customer_sales_table
                WHERE pending_amount > 0
                ORDER BY sales_id DESC
                """
            )

        sales = cursor.fetchall()
        cursor.close()

        if not sales:
            st.info("No sales with pending payments were found.")
        else:
            sale_options = {
                (
                    f"Sale ID {s['sales_id']} | {s['name']} | "
                    f"{s['product_name']} | Pending ₹{s['pending_amount']:.2f}"
                ): s
                for s in sales
            }

            selected_sale_label = st.selectbox(
                "Select Customer Sale",
                list(sale_options.keys())
            )
            selected_sale = sale_options[selected_sale_label]

            st.write(f"Gross Sales: ₹{selected_sale['gross_sales']:,.2f}")
            st.write(
                f"Already Received: ₹{selected_sale['received_amount']:,.2f}"
            )
            st.write(f"Pending: ₹{selected_sale['pending_amount']:,.2f}")

            with st.form("payment_entry_form"):
                payment_date = st.date_input(
                    "Payment Date", value=date.today()
                )
                amount_paid = st.number_input(
                    "Amount Paid (₹)", min_value=0.01, step=100.0
                )
                payment_method = st.selectbox(
                    "Payment Method",
                    ["Cash", "UPI", "Bank Transfer", "Card", "Cheque", "Other"]
                )

                payment_submitted = st.form_submit_button("Save Payment")

            if payment_submitted:
                if amount_paid > float(selected_sale["pending_amount"]):
                    st.error("Payment cannot be greater than the pending amount.")
                else:
                    try:
                        # Recheck the selected sale before saving.
                        cursor = conn.cursor(dictionary=True)

                        if role == "admin":
                            cursor.execute(
                                """
                                SELECT sales_id, gross_sales, received_amount,
                                       pending_amount
                                FROM customer_sales_table
                                WHERE sales_id = %s AND branch_ID = %s
                                FOR UPDATE
                                """,
                                (selected_sale["sales_id"], user_branch_id)
                            )
                        else:
                            cursor.execute(
                                """
                                SELECT sales_id, gross_sales, received_amount,
                                       pending_amount
                                FROM customer_sales_table
                                WHERE sales_id = %s
                                FOR UPDATE
                                """,
                                (selected_sale["sales_id"],)
                            )

                        current_sale = cursor.fetchone()

                        if not current_sale:
                            conn.rollback()
                            st.error("Sale not found or access denied.")
                        elif amount_paid > float(current_sale["pending_amount"]):
                            conn.rollback()
                            st.error(
                                "The pending amount changed. Refresh and try again."
                            )
                        else:
                            new_received = (
                                float(current_sale["received_amount"])
                                + amount_paid
                            )
                            new_pending = max(
                                0.0,
                                float(current_sale["gross_sales"]) - new_received
                            )
                            new_status = "close" if new_pending <= 0.005 else "open"

                            cursor.execute(
                                """
                                INSERT INTO payment_splits_table
                                (sale_id, payment_date, amount_paid, payment_method)
                                VALUES (%s, %s, %s, %s)
                                """,
                                (
                                    selected_sale["sales_id"],
                                    payment_date,
                                    amount_paid,
                                    payment_method
                                )
                            )

                            cursor.execute(
                                """
                                UPDATE customer_sales_table
                                SET received_amount = %s,
                                    pending_amount = %s,
                                    status = %s
                                WHERE sales_id = %s
                                """,
                                (
                                    new_received,
                                    new_pending,
                                    new_status,
                                    selected_sale["sales_id"]
                                )
                            )

                            conn.commit()
                            st.success("Payment saved successfully!")
                            st.rerun()

                        cursor.close()

                    except mysql.connector.Error as e:
                        conn.rollback()
                        st.error(f"Could not save payment: {e}")

    except mysql.connector.Error as e:
        st.error(f"Database error: {e}")
    finally:
        conn.close()
elif page == "Customer Sales Report":
    st.subheader("📋 Customer Sales Report")

    conn = get_connection()

    try:
        branch_df = pd.read_sql(
            "SELECT branch_id, branch_name FROM branches ORDER BY branch_name",
            conn
        )

        col1, col2 = st.columns(2)

        start_date = col1.date_input(
            "Start Date", value=date(2024, 1, 1)
        )
        end_date = col2.date_input(
            "End Date", value=date.today()
        )

        customer_search = st.text_input("Search Customer")
        product_search = st.text_input("Search Product")
        status_filter = st.selectbox(
            "Payment Status", ["All", "open", "close"]
        )

        selected_branch = None

        if role == "super admin":
            branch_options = {
                "All branches": None
            }

            for _, row in branch_df.iterrows():
                branch_options[
                    f"{row['branch_name']} (ID: {row['branch_id']})"
                ] = int(row["branch_id"])

            selected_label = st.selectbox(
                "Filter by Branch", list(branch_options.keys())
            )
            selected_branch = branch_options[selected_label]
        else:
            st.caption("You can view reports for your assigned branch only.")

        if start_date > end_date:
            st.error("Start Date cannot be after End Date.")
        else:
            query = """
                SELECT s.sales_id, s.sales_date,
                       s.name AS customer_name, s.mobile_number,
                       s.product_name, b.branch_name,
                       s.gross_sales, s.received_amount,
                       s.pending_amount, s.status
                FROM customer_sales_table s
                LEFT JOIN branches b ON s.branch_ID = b.branch_id
                WHERE s.sales_date BETWEEN %s AND %s
            """
            params = [start_date, end_date]

            if role == "admin":
                query += " AND s.branch_ID = %s"
                params.append(user_branch_id)
            elif selected_branch is not None:
                query += " AND s.branch_ID = %s"
                params.append(selected_branch)

            if customer_search.strip():
                query += " AND s.name LIKE %s"
                params.append(f"%{customer_search.strip()}%")

            if product_search.strip():
                query += " AND s.product_name LIKE %s"
                params.append(f"%{product_search.strip()}%")

            if status_filter != "All":
                query += " AND LOWER(s.status) = %s"
                params.append(status_filter)

            query += " ORDER BY s.sales_date DESC, s.sales_id DESC"

            sales_df = pd.read_sql(query, conn, params=params)

            c1, c2, c3 = st.columns(3)
            c1.metric("Gross Sales", f"₹{sales_df['gross_sales'].sum():,.2f}")
            c2.metric(
                "Received Amount",
                f"₹{sales_df['received_amount'].sum():,.2f}"
            )
            c3.metric(
                "Pending Amount",
                f"₹{sales_df['pending_amount'].sum():,.2f}"
            )

            st.dataframe(
                sales_df, use_container_width=True, hide_index=True
            )
            st.caption(f"Total records: {len(sales_df)}")

        
    except mysql.connector.Error as e:
        st.error(f"Database error: {e}")
    finally:
        conn.close()


role = st.session_state.role.strip().lower()

if role == "super admin":
    page_options = [
        "Customer Sales Report",
        "New Customer Sales Entry",
        "Payment Split Entry",
        "SQL Analysis"
    ]
else:
    page_options = [
        "Customer Sales Report",
        "New Customer Sales Entry",
        "Payment Split Entry"
    ]


if page == "SQL Analysis":

    if st.session_state.role.strip().lower() != "super admin":
        st.error("Access denied. Super Admin only.")
        st.stop()

    st.title("SQL Analysis Dashboard")
    st.write("View sales, branch, payment, and financial analysis.")

    queries = {
        "Q1 - All Customer Sales": """
            SELECT * FROM customer_sales_table
        """,

        "Q2 - All Branches": """
            SELECT * FROM branches
        """,

        "Q3 - All Payment Splits": """
            SELECT * FROM payment_splits_table
        """,

        "Q4 - Sales by Branch": """
            SELECT s.*
            FROM customer_sales_table s
            JOIN branches b ON s.branch_ID = b.branch_id
            WHERE UPPER(b.branch_name) = 'CHENNAI'
        """,

        "Q6 - Total Gross Sales": """
            SELECT SUM(gross_sales) AS total_gross_sales
            FROM customer_sales_table
        """,

        "Q7 - Total Received Amount": """
            SELECT SUM(received_amount) AS total_received_amount
            FROM customer_sales_table
        """,

        "Q8 - Total Pending Amount": """
            SELECT SUM(pending_amount) AS total_pending_amount
            FROM customer_sales_table
        """,

        "Q9 - Sales Count by Branch": """
            SELECT b.branch_name, COUNT(s.sales_id) AS total_sales
            FROM branches b
            LEFT JOIN customer_sales_table s
                ON b.branch_id = s.branch_ID
            GROUP BY b.branch_id, b.branch_name
        """,

        "Q11 - Sales with Branch Name": """
            SELECT s.*, b.branch_name
            FROM customer_sales_table s
            JOIN branches b ON s.branch_ID = b.branch_id
        """,

        "Q12 - Total Payment per Sale": """
            SELECT s.sales_id, s.name AS customer_name,
                   s.gross_sales,
                   COALESCE(SUM(p.amount_paid), 0) AS total_payment_received
            FROM customer_sales_table s
            LEFT JOIN payment_splits_table p
                ON s.sales_id = p.sale_id
            GROUP BY s.sales_id, s.name, s.gross_sales
        """,

        "Q13 - Sales with Payment Method": """
            SELECT s.sales_id, s.name AS customer_name,
                   s.product_name, p.payment_date,
                   p.amount_paid, p.payment_method
            FROM customer_sales_table s
            LEFT JOIN payment_splits_table p
                ON s.sales_id = p.sale_id
        """,

        "Q14 - Sales with Branch Admin": """
            SELECT s.sales_id, s.name AS customer_name,
                   s.product_name, s.gross_sales,
                   b.branch_name, b.branch_admin_name
            FROM customer_sales_table s
            JOIN branches b ON s.branch_ID = b.branch_id
        """,

        "Q16 - Pending Greater Than 5000": """
            SELECT *
            FROM customer_sales_table
            WHERE pending_amount > 5000
        """,

        "Q17 - Highest Gross Sales Branch": """
            SELECT b.branch_name,
                   SUM(s.gross_sales) AS total_gross_sales
            FROM branches b
            JOIN customer_sales_table s
                ON b.branch_id = s.branch_ID
            GROUP BY b.branch_id, b.branch_name
            ORDER BY total_gross_sales DESC
            LIMIT 1
        """,

        "Q18 - Monthly Sales Summary": """
            SELECT YEAR(sales_date) AS sales_year,
                   MONTH(sales_date) AS sales_month,
                   COUNT(*) AS total_sales,
                   SUM(gross_sales) AS total_gross_sales,
                   SUM(received_amount) AS total_received,
                   SUM(pending_amount) AS total_pending
            FROM customer_sales_table
            GROUP BY YEAR(sales_date), MONTH(sales_date)
            ORDER BY sales_year, sales_month
        """,

        "Q19 - Collection by Payment Method": """
            SELECT payment_method,
                   SUM(amount_paid) AS total_collection
            FROM payment_splits_table
            GROUP BY payment_method
            ORDER BY total_collection DESC
        """
    }

    selected_query = st.selectbox(
        "Select SQL Query",
        list(queries.keys())
    )

    if st.button("Run Query", key="run_sql_analysis"):
        conn = None
        try:
            conn = get_connection()

            import pandas as pd

            result_df = pd.read_sql(
                queries[selected_query],
                conn
            )

            st.subheader("Query Result")
            st.dataframe(
                result_df,
                use_container_width=True,
                hide_index=True
            )

            st.success(f"Query completed: {selected_query}")

            st.download_button(
                label="Download Result as CSV",
                data=result_df.to_csv(index=False).encode("utf-8"),
                file_name="sql_analysis_result.csv",
                mime="text/csv",
                key="sql_analysis_download"
            )

        except Exception as e:
            st.error(f"Unable to execute query: {e}")

        finally:
            if conn is not None and conn.is_connected():
                conn.close()
