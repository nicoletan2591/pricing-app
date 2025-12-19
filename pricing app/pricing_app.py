import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO
import logging

# Silence background noise
logging.getLogger("pdfminer").setLevel(logging.ERROR)

st.set_page_config(page_title="PI Database Targeting", layout="wide")
st.title("🔬 PI Database Targeting & Search")

if 'basket' not in st.session_state:
    st.session_state.basket = pd.DataFrame()

# File Uploader
uploaded_file = st.file_uploader("Upload your Database (CSV, Excel, or PDF)", type=None)

if uploaded_file:
    try:
        fname = uploaded_file.name.lower()
        
        with st.spinner(f'Reading {fname}...'):
            if fname.endswith('.csv'):
                try:
                    df = pd.read_csv(uploaded_file, encoding='utf-8', low_memory=False)
                except:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding='cp1252', low_memory=False)
            elif fname.endswith('.pdf'):
                all_rows = []
                with pdfplumber.open(uploaded_file) as pdf:
                    for page in pdf.pages:
                        table = page.extract_table()
                        if table: all_rows.extend(table)
                df = pd.DataFrame(all_rows)
                if not df.empty:
                    df.columns = [str(v).strip() for v in df.iloc[0]]
                    df = df[1:].reset_index(drop=True)
            else:
                df = pd.read_excel(uploaded_file)

        # --- POWERFUL CLEANING ---
        # Remove empty rows and strip ALL whitespace from column names
        df = df.dropna(how='all')
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]

        # --- SMART COLUMN SEARCH (Case Insensitive) ---
        # We look for "Field" or "Primary" or "Category"
        field_keywords = ["field", "primary", "category", "research"]
        field_col = None
        for col in df.columns:
            if any(key in col.lower() for key in field_keywords) and "(product)" not in col.lower():
                field_col = col
                break
        
        # Look for the "Interest" column
        interest_col = next((c for c in df.columns if "interest" in c.lower() and "(product)" not in c.lower()), None)

        # --- DEBUG SECTION (Optional) ---
        with st.expander("🛠️ Debug: See Detected Columns"):
            st.write("Columns found in your file:", list(df.columns))
            st.write(f"Column chosen for 'Field' filter: **{field_col}**")

        st.subheader("🔍 Search & Filter")
        col1, col2, col3 = st.columns(3)

        with col1:
            # 1. Category Dropdown
            if field_col:
                # Get unique values, remove 'nan', and sort them
                raw_options = df[field_col].dropna().unique().tolist()
                field_options = ["All Categories"] + sorted([str(x) for x in raw_options])
                selected_field = st.selectbox(f"Filter by {field_col}:", field_options)
            else:
                selected_field = "All Categories"
                st.warning("⚠️ No 'Field' column found. Try the General Search.")

        with col2:
            # 2. Detailed Interest Search
            interest_query = st.text_input("Search Specific Interest (e.g. Skin, DNA):")

        with col3:
            # 3. General Search
            general_query = st.text_input("General Search (Name, DOI, SKU):")

        # --- FILTERING ENGINE ---
        results = df.copy()

        # Apply Category
        if selected_field != "All Categories":
            results = results[results[field_col].astype(str) == selected_field]

        # Apply Interest Keyword
        if interest_query:
            search_col = interest_col if interest_col else field_col
            if search_col:
                results = results[results[search_col].astype(str).str.contains(interest_query, case=False, na=False)]
            else:
                results = results[results.apply(lambda r: r.astype(str).str.contains(interest_query, case=False).any(), axis=1)]

        # Apply General Keyword
        if general_query:
            results = results[results.apply(lambda r: r.astype(str).str.contains(general_query, case=False, na=False).any(), axis=1)]

        # --- DISPLAY RESULTS ---
        if not results.empty:
            st.success(f"Matches found: {len(results)}")
            st.dataframe(results, use_container_width=True)
            
            if st.button("➕ Add these results to Export List"):
                st.session_state.basket = pd.concat([st.session_state.basket, results]).drop_duplicates()
                st.toast("Saved!")
        else:
            st.info("No matches found for those criteria.")

        # --- EXPORT BASKET ---
        if not st.session_state.basket.empty:
            st.divider()
            st.subheader("📋 Your Final Export List")
            st.dataframe(st.session_state.basket, use_container_width=True)
            
            ex_col1, ex_col2 = st.columns(2)
            with ex_col1:
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    st.session_state.basket.to_excel(writer, index=False)
                st.download_button("💾 Download Results (Excel)", output.getvalue(), "pi_database_search.xlsx")
            with ex_col2:
                if st.button("🗑️ Clear List"):
                    st.session_state.basket = pd.DataFrame()
                    st.rerun()

    except Exception as e:
        st.error(f"Error: {e}")
