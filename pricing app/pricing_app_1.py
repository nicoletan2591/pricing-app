import streamlit as st
import pandas as pd
import pdfplumber
from io import BytesIO
import logging

# Silence background noise
logging.getLogger("pdfminer").setLevel(logging.ERROR)

st.set_page_config(page_title="Master Database Consolidator", layout="wide")
st.title("🔬 Master Multi-Database Search")
st.markdown("Upload up to 10+ databases to search, filter, and export into **one unified table**.")

# Initialize the 'basket' (Final Export List)
if 'basket' not in st.session_state:
    st.session_state.basket = pd.DataFrame()

# --- STEP 1: UPLOAD MULTIPLE FILES ---
uploaded_files = st.file_uploader(
    "Drag and drop all your database files here (CSV, Excel, or PDF)", 
    type=None, 
    accept_multiple_files=True
)

all_dataframes = []

if uploaded_files:
    for uploaded_file in uploaded_files:
        try:
            fname = uploaded_file.name.lower()
            with st.spinner(f'Merging {fname}...'):
                # Handle CSV
                if fname.endswith('.csv'):
                    try:
                        temp_df = pd.read_csv(uploaded_file, encoding='utf-8', low_memory=False)
                    except:
                        uploaded_file.seek(0)
                        temp_df = pd.read_csv(uploaded_file, encoding='cp1252', low_memory=False)
                # Handle PDF
                elif fname.endswith('.pdf'):
                    all_rows = []
                    with pdfplumber.open(uploaded_file) as pdf:
                        for page in pdf.pages:
                            table = page.extract_table()
                            if table: all_rows.extend(table)
                    temp_df = pd.DataFrame(all_rows)
                    if not temp_df.empty:
                        temp_df.columns = [str(v).strip() for v in temp_df.iloc[0]]
                        temp_df = temp_df[1:].reset_index(drop=True)
                # Handle Excel
                else:
                    temp_df = pd.read_excel(uploaded_file)
                
                # IMPORTANT: Tag the source so you can filter by database later
                temp_df['Origin_File'] = uploaded_file.name
                all_dataframes.append(temp_df)
        except Exception as e:
            st.error(f"Could not read {uploaded_file.name}: {e}")

    if all_dataframes:
        # --- STEP 2: STACK ALL DATABASES ---
        # axis=0 stacks them vertically. sort=False prevents columns from re-ordering
        master_df = pd.concat(all_dataframes, axis=0, ignore_index=True, sort=False)
        
        # Standardize headers
        master_df.columns = [str(c).strip().replace('\n', ' ') for c in master_df.columns]
        master_df = master_df.dropna(how='all')

        # --- STEP 3: ADVANCED FILTERING ---
        st.divider()
        st.subheader(f"🔍 Searching {len(master_df)} total rows from {len(uploaded_files)} files")
        
        col1, col2, col3, col4 = st.columns([1.5, 1, 1, 1.5])

        with col1:
            # New Feature: Filter by specific Database File
            db_list = ["All Databases"] + sorted(master_df['Origin_File'].unique().tolist())
            selected_db = st.selectbox("📁 Select Database Source:", db_list)

        with col2:
            # Field/Category Detection
            field_keywords = ["field", "primary", "category", "research"]
            field_col = next((c for c in master_df.columns if any(k in c.lower() for k in field_keywords) and "(product)" not in c.lower()), None)
            
            if field_col:
                field_options = ["All Fields"] + sorted([str(x) for x in master_df[field_col].dropna().unique()])
                selected_field = st.selectbox(f"Filter by {field_col}:", field_options)
            else:
                selected_field = "All Fields"

        with col3:
            interest_query = st.text_input("🧬 Research Interest:")

        with col4:
            general_query = st.text_input("⌨️ Keyword Search (Name/DOI):")

        # --- APPLY FILTERS ---
        results = master_df.copy()
        
        if selected_db != "All Databases":
            results = results[results['Origin_File'] == selected_db]
        
        if selected_field != "All Fields":
            results = results[results[field_col].astype(str) == selected_field]
            
        if interest_query:
            # Search everywhere for interest query
            results = results[results.apply(lambda r: r.astype(str).str.contains(interest_query, case=False).any(), axis=1)]
            
        if general_query:
            results = results[results.apply(lambda r: r.astype(str).str.contains(general_query, case=False).any(), axis=1)]

        # --- STEP 4: RESULTS VIEW ---
        if not results.empty:
            st.success(f"Found {len(results)} matching entries.")
            st.dataframe(results, use_container_width=True)
            
            if st.button("➕ Add these results to Final Selection"):
                # Use concat to keep stacking items in the basket
                st.session_state.basket = pd.concat([st.session_state.basket, results], axis=0, sort=False).drop_duplicates()
                st.toast(f"Added {len(results)} rows to export list!")
        else:
            st.warning("No matches found in the combined data.")

# --- STEP 5: THE FINAL CONSOLIDATED TABLE ---
if not st.session_state.basket.empty:
    st.divider()
    st.subheader("📋 Consolidated Export List")
    st.info(f"Currently contains {len(st.session_state.basket)} entries gathered from your searches.")
    st.dataframe(st.session_state.basket, use_container_width=True)
    
    down_col1, down_col2 = st.columns(2)
    with down_col1:
        output = BytesIO()
        # xlsxwriter is used for professional Excel formatting
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            st.session_state.basket.to_excel(writer, index=False)
        st.download_button(
            label="💾 Download All Selected Data as One Excel",
            data=output.getvalue(),
            file_name="consolidated_master_list.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with down_col2:
        if st.button("🗑️ Reset Application"):
            st.session_state.basket = pd.DataFrame()
            st.rerun()
