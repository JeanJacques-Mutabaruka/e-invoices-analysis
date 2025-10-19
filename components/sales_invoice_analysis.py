# Detailed Sales Invoice Analysis Module
# Handles invoice data import, validation, and comprehensive sales reporting
# Features: Sales summaries by item/price, missing invoice detection, filters

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import re
from utils.file_handler import cls_Customfiles_Filetypehandler as filehandler

class cls_InvoiceSalesAnalysis:
    """Detailed Sales Invoices Analysis Component - Manages invoice data and sales reporting"""

    # Expected columns from invoice file
    EXPECTED_COLUMNS = [
        'Invoice number', 'SDC ID', 'Buyer TIN', 'Buyer Name', 'Sale date',
        'Receipt type', 'Item code', 'Item name', 'Quantity', 'Unit price',
        'Tax type', 'Taxable Supply Price', 'Discount Amount', 'VAT', 'Summary Amount'
    ]

    # ---------- Column Mappings for V20 ----------
    COL_MAPPING_V20 = {
        "Invoice No": "MRC NO",
        "SDC No": "SDC NO",
        "Buyer Tin": "BUYER TIN",
        "Buyer Name": "BUYER NAME",
        "User Name": "USER NAME",
        "Remark": "REMARK",
        "Date": "TRANSACTION DATE",
        "Type": "TYPE",
        "Item Code": "ITEM CODE",
        "Item Name": "ITEM NAME",
        "Quantity": "QUANTITY",
        "Unit Price": "UNIT PRICE",
        "Taxable Amount": "TAXABLE AMOUNT",
        "Discount Amount": "DISCOUNT AMOUNT",
        "VAT": "VAT AMOUNT",
        "Summary Amount": "SUMMARY AMOUNT",
        "Ref.Number": "REFUNDED-NUMBER",
        "Ref.SDC Num": "REFUNDED-SDC NUM",
        "Ref.Date": "REFUNDED-DATE",
        "Refund Reason": "REFUND REASON",
    }

    DATA_TYPES_V20 = {
        "MRC NO": "INTEGER",
        "SDC NO": "TEXT",
        "BUYER TIN": "TEXT",
        "BUYER NAME": "TEXT",
        "USER NAME": "TEXT",
        "REMARK": "TEXT",
        "TRANSACTION DATE": "DATE",
        "TYPE": "TEXT",
        "ITEM CODE": "TEXT",
        "ITEM NAME": "TEXT",
        "QUANTITY": "FLOAT",
        "UNIT PRICE": "FLOAT",
        "TAXABLE AMOUNT": "FLOAT",
        "DISCOUNT AMOUNT": "FLOAT",
        "VAT AMOUNT": "FLOAT",
        "SUMMARY AMOUNT": "FLOAT",
        "REFUNDED-NUMBER": "INTEGER",
        "REFUNDED-SDC NUM": "INTEGER",
        "REFUNDED-DATE": "DATE",
        "REFUND REASON": "TEXT"
    }

    @staticmethod
    def fn_standardize_v20_data(df_raw):
        """Standardize EBM BO SALES DETAILS V20 data to match V21 structure"""
        df = df_raw.rename(columns=cls_InvoiceSalesAnalysis.COL_MAPPING_V20)

        # Type conversions
        for col, dtype in cls_InvoiceSalesAnalysis.DATA_TYPES_V20.items():
            if col not in df.columns:
                continue
            if dtype == "FLOAT":
                df[col] = df[col].apply(cls_InvoiceSalesAnalysis.fn_clean_numeric)
            elif dtype == "INTEGER":
                df[col] = df[col].apply(lambda x: int(cls_InvoiceSalesAnalysis.fn_clean_numeric(x)))
            elif dtype == "DATE":
                df[col] = df[col].apply(cls_InvoiceSalesAnalysis.fn_clean_date)
            else:
                df[col] = df[col].astype(str).str.strip()

        # Now rename columns to match V21-style names
        rename_to_v21 = {
            "MRC NO": "Invoice number",
            "SDC NO": "SDC ID",
            "BUYER TIN": "Buyer TIN",
            "BUYER NAME": "Buyer Name",
            "TRANSACTION DATE": "Sale date",
            "TYPE": "Receipt type",
            "ITEM CODE": "Item code",
            "ITEM NAME": "Item name",
            "QUANTITY": "Quantity",
            "UNIT PRICE": "Unit price",
            "TAXABLE AMOUNT": "Taxable Supply Price",
            "DISCOUNT AMOUNT": "Discount Amount",
            "VAT AMOUNT": "VAT",
            "SUMMARY AMOUNT": "Summary Amount"
        }

        df.rename(columns=rename_to_v21, inplace=True)

        return df

    NUMERIC_COLUMNS = [
        'Quantity', 'Unit price', 'Taxable Supply Price', 
        'Discount Amount', 'VAT', 'Summary Amount'
    ]

    DATE_COLUMNS = ['Sale date']

    TEXT_COLUMNS = ['Invoice number', 'SDC ID', 'Buyer TIN']

    # ---------- Format helper ----------
    @staticmethod
    def fn_format_numbers(value, int_nbdigits=2):
        """Format numbers with commas and parentheses for negatives"""
        if isinstance(value, (int, float)):
            if pd.isna(value):
                return "-"
            value = round(value, int_nbdigits)
            return f"({abs(value):,.{int_nbdigits}f})" if value < 0 else f"{value:,.{int_nbdigits}f}"
        elif isinstance(value, (datetime, date, pd.Timestamp)):
            return value.strftime("%d-%b-%Y")
        return value

    # ---------- Month ordering helper ----------
    @staticmethod
    def fn_get_month_sort_order():
        """Return month names in chronological order"""
        return ['January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December']

    # ---------- Initialization ----------
    @staticmethod
    def fn_initialize_invoice_data():
        """Initialize invoice data structures if not exists"""
        if 'invoice_sales_data' not in st.session_state or st.session_state.invoice_sales_data is None:
            st.session_state.invoice_sales_data = pd.DataFrame(columns=cls_InvoiceSalesAnalysis.EXPECTED_COLUMNS)

    # ---------- Data validation and cleaning ----------
    @staticmethod
    def fn_clean_numeric(value):
        """Convert text to numeric, handling various formats"""
        if pd.isna(value):
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        
        # Remove commas and spaces, convert to float
        try:
            cleaned = str(value).replace(',', '').replace(' ', '').strip()
            return float(cleaned) if cleaned else 0.0
        except:
            return 0.0

    @staticmethod
    def fn_clean_date(value):
        """Convert various date formats to datetime"""
        if pd.isna(value):
            return None
        if isinstance(value, (datetime, pd.Timestamp)):
            return value
        
        try:
            # Try parsing common date formats
            return pd.to_datetime(value, errors='coerce', dayfirst=True)
        except:
            return None

    @staticmethod
    def fn_extract_sdc_and_serial(sdc_id):
        """Extract SDC number and serial from SDC ID like 'SDC010037083/1761'"""
        if pd.isna(sdc_id) or not sdc_id:
            return None, None
        
        parts = str(sdc_id).split('/')
        if len(parts) == 2:
            try:
                return parts[0].strip(), int(parts[1].strip())
            except:
                return parts[0].strip(), None
        return str(sdc_id).strip(), None

    @staticmethod
    def fn_process_uploaded_data(df):
        """Process and validate uploaded invoice data"""
        df = df.copy()

        # --- Detect Version ---
        v20_cols = set(cls_InvoiceSalesAnalysis.COL_MAPPING_V20.keys())
        v21_cols = set(cls_InvoiceSalesAnalysis.EXPECTED_COLUMNS)

        if len(v20_cols.intersection(df.columns)) >= 5:
            st.info("Detected: EBM BO SALES DETAILS V20 format")
            df = cls_InvoiceSalesAnalysis.fn_standardize_v20_data(df)
        else:
            st.info("Detected: EBM BO SALES DETAILS V21 format")

        # continue with rest of existing fn_process_uploaded_data() logic

        # Check for required columns
        missing_cols = [col for col in cls_InvoiceSalesAnalysis.EXPECTED_COLUMNS if col not in df.columns]
        if missing_cols:
            st.warning(f"Missing columns: {', '.join(missing_cols)}")
        
        # Convert numeric columns
        for col in cls_InvoiceSalesAnalysis.NUMERIC_COLUMNS:
            if col in df.columns:
                df[col] = df[col].apply(cls_InvoiceSalesAnalysis.fn_clean_numeric)
        
        # Convert date columns
        for col in cls_InvoiceSalesAnalysis.DATE_COLUMNS:
            if col in df.columns:
                df[col] = df[col].apply(cls_InvoiceSalesAnalysis.fn_clean_date)
        
        # Ensure text columns remain as text
        for col in cls_InvoiceSalesAnalysis.TEXT_COLUMNS:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        # Handle refunds: make quantities and amounts negative, keep unit price positive
        if 'Receipt type' in df.columns:
            refund_mask = df['Receipt type'].str.contains('Refund', case=False, na=False)
            
            for col in ['Quantity', 'Taxable Supply Price', 'Summary Amount', 'VAT', 'Discount Amount']:
                if col in df.columns:
                    # Make negative if not already
                    df.loc[refund_mask & (df[col] > 0), col] = -df.loc[refund_mask & (df[col] > 0), col]
            
            # Keep unit price positive
            if 'Unit price' in df.columns:
                df.loc[refund_mask & (df['Unit price'] < 0), 'Unit price'] = df.loc[refund_mask & (df['Unit price'] < 0), 'Unit price'].abs()
        
        # Calculate Amount without VAT
        if 'Summary Amount' in df.columns and 'VAT' in df.columns:
            df['Amount without VAT'] = df['Summary Amount'] - df['VAT']
        
        # Extract SDC and Serial Number
        if 'SDC ID' in df.columns:
            df[['SDC', 'Serial Number']] = df['SDC ID'].apply(
                lambda x: pd.Series(cls_InvoiceSalesAnalysis.fn_extract_sdc_and_serial(x))
            )
        
        # Add Year and Month columns from Sale date
        if 'Sale date' in df.columns:
            df['Year'] = pd.to_datetime(df['Sale date']).dt.year
            df['Month'] = pd.to_datetime(df['Sale date']).dt.month
            df['Month Name'] = pd.to_datetime(df['Sale date']).dt.strftime('%B')
        
        return df

    # ---------- Data Upload UI ----------
    @staticmethod
    def fn_render_data_upload():
        """Render data upload section"""
        st.markdown("""
            <h4 style='background-color: #607D8B; color: white; padding: 8px; border-radius: 5px; 
            text-align: center;'>📂 INVOICE DATA UPLOAD</h4>
        """, unsafe_allow_html=True)

        col_upload, col_download = st.columns([2, 1])

        # Upload section
        with col_upload:
            st.markdown("**Upload detailed Sales Invoices File (Excel)**")
            uploaded_file = st.file_uploader(
                "📤 Upload Sales Data",
                type=['xlsx', 'xls', 'xlsb', 'xlsm'],
                key='upload_invoice_data'
            )

            if uploaded_file is not None:
                try:
                    df_raw = pd.read_excel(uploaded_file)
                    df_processed = cls_InvoiceSalesAnalysis.fn_process_uploaded_data(df_raw)
                    
                    st.session_state.invoice_sales_data = df_processed
                    st.success(f"✅ Invoice data loaded successfully! {len(df_processed)} records processed.")
                    
                    # Show preview
                    with st.expander("📋 Preview uploaded data (first 10 rows)"):
                        st.dataframe(df_processed.head(10), use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Error reading uploaded file: {e}")

        # Download section
        with col_download:
            st.markdown("**Download Current Data:**")
            if not st.session_state.invoice_sales_data.empty:
                excel_data = filehandler.fn_to_excel_multiple_sheets({
                    'Invoice_Data': st.session_state.invoice_sales_data
                })
                filename = datetime.now().strftime("invoice_data_%Y-%m-%d_%H%M.xlsx")
                filehandler.fn_create_download_button(
                    label=f"📥 {filename}",
                    data=excel_data,
                    filename=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    # ---------- Sales Summary by Item & Price ----------
    @staticmethod
    def fn_render_sales_summary():
        """Render enhanced sales summary grouped by item and price, with multi-level sorting, subtotals, and global total at the top."""
        
        st.markdown("""
            <h4 style='background-color: #2196F3; color: white; padding: 8px; border-radius: 5px; 
            text-align: center;'>📊 SALES SUMMARY BY ITEM & PRICE</h4>
        """, unsafe_allow_html=True)

        # --- basic validation ---
        if "invoice_sales_data" not in st.session_state or st.session_state.invoice_sales_data.empty:
            st.info("No invoice data available. Please upload a file.")
            return

        df = st.session_state.invoice_sales_data.copy()

        # ---------- FILTERS & OPTIONS ----------
        with st.expander("🔍 FILTERS & OPTIONS", expanded=False):
            col1, col2, col3 = st.columns([1.2, 1.2, 1.0])

            with col1:
                sort_choice = st.selectbox(
                    "📊 Sort by",
                    ["Sales VAT Inc (Revenue)", "Quantity", "Invoices", "Percent of Total", "Unit Price"],
                    help="Choose sorting order for both items and details."
                )
            with col2:
                order_choice = st.radio("Order", ["Descending", "Ascending"], horizontal=True, label_visibility='collapsed')
            with col3:
                show_subtotals = st.checkbox("🧮 Show Subtotals", value=True)

            col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)

            with col_f1:
                item_options = ['All'] + sorted(df['Item name'].dropna().unique().tolist())
                selected_item = st.selectbox('Item Name', item_options)
            with col_f2:
                price_options = ['All'] + sorted(df['Unit price'].dropna().unique().tolist())
                selected_price = st.selectbox('Unit Price', price_options)
            with col_f3:
                if 'Year' in df.columns:
                    year_options = ['All'] + sorted(df['Year'].dropna().unique().tolist())
                    selected_year = st.multiselect('Year', year_options, default=['All'])
                else:
                    selected_year = ['All']
            with col_f4:
                if 'Month Name' in df.columns:
                    # Sort months chronologically instead of alphabetically
                    month_order = cls_InvoiceSalesAnalysis.fn_get_month_sort_order()
                    available_months = df['Month Name'].dropna().unique().tolist()
                    month_options = ['All'] + [m for m in month_order if m in available_months]
                    selected_month = st.multiselect('Month', month_options, default=['All'])
                else:
                    selected_month = ['All']
            with col_f5:
                if 'Sale date' in df.columns:
                    min_date = df['Sale date'].min()
                    max_date = df['Sale date'].max()
                    date_range = st.date_input(
                        "Date Range",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date
                    )
                else:
                    date_range = None

            # Apply filters
            df_filtered = df.copy()
            if selected_item != 'All':
                df_filtered = df_filtered[df_filtered['Item name'] == selected_item]
            if selected_price != 'All':
                df_filtered = df_filtered[df_filtered['Unit price'] == selected_price]
            if 'All' not in selected_year and selected_year:
                df_filtered = df_filtered[df_filtered['Year'].isin(selected_year)]
            if 'All' not in selected_month and selected_month:
                df_filtered = df_filtered[df_filtered['Month Name'].isin(selected_month)]
            if date_range and len(date_range) == 2:
                df_filtered = df_filtered[
                    (df_filtered['Sale date'] >= pd.Timestamp(date_range[0])) &
                    (df_filtered['Sale date'] <= pd.Timestamp(date_range[1]))
                ]

            if df_filtered.empty:
                st.warning("No records found for the selected filters.")
                return

            # ---------- AGGREGATION ----------
            pivot_df = df_filtered.groupby(['Item name', 'Unit price'], dropna=False).agg({
                'Invoice number': 'nunique',
                'Quantity': 'sum',
                'Summary Amount': 'sum',
                'VAT': 'sum',
                'Amount without VAT': 'sum'
            }).reset_index()

            pivot_df.rename(columns={
                'Invoice number': 'Invoices',
                'Summary Amount': 'Sales VAT Inc',
                'Amount without VAT': 'Sales VAT Excl'
            }, inplace=True)

            total_sales = pivot_df['Sales VAT Inc'].sum()
            pivot_df['Percent of Total'] = (
                (pivot_df['Sales VAT Inc'] / total_sales * 100).round(2) if total_sales > 0 else 0
            )

            # ---------- ITEM-LEVEL AGGREGATION ----------
            item_agg = pivot_df.groupby('Item name', as_index=True).agg({
                'Invoices': 'sum',
                'Quantity': 'sum',
                'Sales VAT Inc': 'sum',
                'VAT': 'sum',
                'Sales VAT Excl': 'sum'
            })
            item_agg['Percent of Total'] = (
                (item_agg['Sales VAT Inc'] / total_sales * 100).round(2) if total_sales > 0 else 0
            )

            # ---------- Sorting ----------
            sort_col_map = {
                "Sales VAT Inc (Revenue)": "Sales VAT Inc",
                "Quantity": "Quantity",
                "Invoices": "Invoices",
                "Percent of Total": "Percent of Total",
                "Unit Price": "Unit price"
            }
            sort_col = sort_col_map.get(sort_choice, "Sales VAT Inc")
            ascending = order_choice == "Ascending"

            # Item-level ordering
            item_sort_col = sort_col if sort_col in item_agg.columns else "Sales VAT Inc"
            ordered_items = item_agg.sort_values(by=item_sort_col, ascending=ascending).index.tolist()

            # ---------- Build combined display ----------
            rows = []
            for item in ordered_items:
                item_df = pivot_df[pivot_df['Item name'] == item].copy()
                detail_sort_col = sort_col if sort_col in item_df.columns else 'Sales VAT Inc'
                item_df.sort_values(by=detail_sort_col, ascending=ascending, inplace=True)

                subtotal = item_agg.loc[item]

                # Subtotal row
                if show_subtotals:
                    rows.append({
                        "ITEM": f"📊 {item}",
                        "Unit price": "Subtotal",
                        "Invoices": int(subtotal['Invoices']),
                        "Quantity": subtotal['Quantity'],
                        "Sales VAT Inc": subtotal['Sales VAT Inc'],
                        "VAT": subtotal['VAT'],
                        "Sales VAT Excl": subtotal['Sales VAT Excl'],
                        "Percent of Total": subtotal['Percent of Total']
                    })
                else:
                    rows.append({
                        "ITEM": f"📊 {item}",
                        "Unit price": "",
                        "Invoices": "",
                        "Quantity": "",
                        "Sales VAT Inc": "",
                        "VAT": "",
                        "Sales VAT Excl": "",
                        "Percent of Total": ""
                    })

                # Detail rows
                for _, r in item_df.iterrows():
                    rows.append({
                        "ITEM": "",
                        "Unit price": r['Unit price'],
                        "Invoices": r['Invoices'],
                        "Quantity": r['Quantity'],
                        "Sales VAT Inc": r['Sales VAT Inc'],
                        "VAT": r['VAT'],
                        "Sales VAT Excl": r['Sales VAT Excl'],
                        "Percent of Total": r['Percent of Total']
                    })

            # ---------- GLOBAL TOTAL ----------
            global_totals = {
                "ITEM": "🌍 TOTAL (ALL ITEMS)",
                "Unit price": "",
                "Invoices": int(item_agg['Invoices'].sum()),
                "Quantity": item_agg['Quantity'].sum(),
                "Sales VAT Inc": item_agg['Sales VAT Inc'].sum(),
                "VAT": item_agg['VAT'].sum(),
                "Sales VAT Excl": item_agg['Sales VAT Excl'].sum(),
                "Percent of Total": 100.0
            }

            # Prepend total at the top
            rows = [global_totals] + rows

            df_display = pd.DataFrame(rows)

            # ---------- Display inside expander ----------
            st.markdown(
                f"##### Sorted by **{sort_choice}** at both Item and Unit-Price levels "
                f"({'Ascending' if ascending else 'Descending'})"
            )

            def fmt(x, ndigits=0):
                if isinstance(x, (int, float)):
                    return f"{x:,.{ndigits}f}"
                return x

            styled_df = (
                df_display.style
                .hide(axis="index")
                .apply(
                    lambda row: [
                        "font-weight: bold; background-color: #e6f7e6;"  # Subtotals
                        if str(row["Unit price"]).lower() == "subtotal"
                        else (
                            "font-weight: bold; background-color: #b9e6b9;font-size:20px"  # Global total
                            if str(row["ITEM"]).startswith("🌍")
                            else ""
                        )
                        for _ in row
                    ],
                    axis=1
                )
                .format({
                    "Unit price": lambda x: fmt(x, 0) if str(x).replace('.', '', 1).isdigit() else x,
                    "Invoices": lambda x: fmt(x, 0),
                    "Quantity": lambda x: fmt(x, 0),
                    "Sales VAT Inc": lambda x: fmt(x, 0),
                    "VAT": lambda x: fmt(x, 0),
                    "Sales VAT Excl": lambda x: fmt(x, 0),
                    "Percent of Total": lambda x: f"{x:.1f}%" if isinstance(x, (int, float)) else x
                })
            )

            st.dataframe(styled_df, use_container_width=True, height=750)

            # ---------- DOWNLOAD ----------
            st.markdown("##### 📥 Download Summary Data")

            excel_data = filehandler.fn_to_excel_multiple_sheets({
                'Sales_Summary': df_display
            })
            filename = datetime.now().strftime("sales_summary_%Y-%m-%d_%H%M.xlsx")

            filehandler.fn_create_download_button(
                label="📥 Download Summary",
                data=excel_data,
                filename=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
    
    # ---------- Missing Invoice Detection with Enhanced Data ----------
    @staticmethod
    def fn_detect_missing_invoices():
        """Detect missing invoice serial numbers by SDC with date information"""
        df = st.session_state.invoice_sales_data.copy()

        if 'SDC' not in df.columns or 'Serial Number' not in df.columns:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        # Filter out rows with missing SDC or Serial Number
        df_valid = df[df['SDC'].notna() & df['Serial Number'].notna()].copy()

        if df_valid.empty:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

        missing_invoices = []
        sdc_summary_list = []
        invoices_without_serial = []

        # Group by SDC
        for sdc, group in df_valid.groupby('SDC'):
            group_sorted = group.sort_values('Serial Number')
            serials = sorted(group_sorted['Serial Number'].dropna().astype(int).unique())

            if len(serials) < 1:
                continue

            min_serial = min(serials)
            max_serial = max(serials)

            # Get first and last invoice dates for this SDC
            first_invoice_date = group_sorted.iloc[0]['Sale date']
            last_invoice_date = group_sorted.iloc[-1]['Sale date']

            # Add SDC summary
            sdc_summary_list.append({
                'SDC ID': sdc,
                'First Invoice': f"{sdc}/{min_serial}",
                'Last Invoice': f"{sdc}/{max_serial}",
                'First Invoice Date': first_invoice_date,
                'Last Invoice Date': last_invoice_date,
                'Number of Missing Invoices': 0  # Will be updated
            })

            # Find missing serials in range
            expected_serials = set(range(min_serial, max_serial + 1))
            actual_serials = set(serials)
            missing_serials = sorted(expected_serials - actual_serials)

            if not missing_serials:
                continue

            # Update SDC summary with missing count
            sdc_summary_list[-1]['Number of Missing Invoices'] = len(missing_serials)

            # Create mapping of serial -> date for this SDC
            serial_date_map = dict(zip(group_sorted['Serial Number'].astype(int), group_sorted['Sale date']))

            for missing in missing_serials:
                # Find preceding and following invoices
                preceding_serials = [s for s in actual_serials if s < missing]
                following_serials = [s for s in actual_serials if s > missing]

                preceding_serial = max(preceding_serials) if preceding_serials else None
                following_serial = min(following_serials) if following_serials else None

                preceding_date = serial_date_map.get(preceding_serial) if preceding_serial else None
                following_date = serial_date_map.get(following_serial) if following_serial else None

                # Calculate invoice period (YYYY-MM) - estimate based on surrounding dates
                if preceding_date and following_date:
                    mid_date = preceding_date + (following_date - preceding_date) / 2
                    invoice_period = pd.Timestamp(mid_date).strftime('%Y-%m')
                    between_dates = f"{preceding_date.strftime('%Y-%m-%d')} - {following_date.strftime('%Y-%m-%d')}"
                elif preceding_date:
                    invoice_period = pd.Timestamp(preceding_date).strftime('%Y-%m')
                    between_dates = f"{preceding_date.strftime('%Y-%m-%d')} - ?"
                elif following_date:
                    invoice_period = pd.Timestamp(following_date).strftime('%Y-%m')
                    between_dates = f"? - {following_date.strftime('%Y-%m-%d')}"
                else:
                    invoice_period = "Unknown"
                    between_dates = "N/A"

                missing_invoices.append({
                    'SDC ID': sdc,
                    'Missing Serial Number': missing,
                    'Missing Invoice ID': f"{sdc}/{missing}",
                    'Invoice Period': invoice_period,
                    'Between Dates': between_dates
                })

        # Find invoices without serial numbers
        df_no_serial = df[df['SDC'].notna() & (df['Serial Number'].isna() | (df['Serial Number'] == 0))].copy()
        
        if not df_no_serial.empty:
            for _, row in df_no_serial.iterrows():
                sdc = row['SDC']
                invoice_date = row['Sale date']
                
                # Get all missing invoices for this SDC with their date ranges
                sdc_missing = [m for m in missing_invoices if m['SDC ID'] == sdc]
                
                # Filter probable serials based on invoice date falling within "Between Dates"
                probable_serials = []
                for missing_inv in sdc_missing:
                    between_dates_str = missing_inv['Between Dates']
                    
                    # Parse the date range
                    if ' - ' in between_dates_str and between_dates_str != "N/A":
                        try:
                            dates_parts = between_dates_str.split(' - ')
                            if len(dates_parts) == 2:
                                start_date_str = dates_parts[0].strip()
                                end_date_str = dates_parts[1].strip()
                                
                                # Handle missing dates (indicated by '?')
                                if start_date_str != '?':
                                    start_date = pd.to_datetime(start_date_str)
                                else:
                                    start_date = pd.Timestamp.min
                                
                                if end_date_str != '?':
                                    end_date = pd.to_datetime(end_date_str)
                                else:
                                    end_date = pd.Timestamp.max
                                
                                # Check if invoice date falls within this range
                                if pd.notna(invoice_date) and start_date <= invoice_date <= end_date:
                                    probable_serials.append(missing_inv['Missing Serial Number'])
                        except:
                            pass
                
                # If no probable serials found based on date range, show all
                if not probable_serials:
                    probable_serials = [m['Missing Serial Number'] for m in sdc_missing]
                
                comment = f"Probable serial: {', '.join([str(s) for s in probable_serials])}" if probable_serials else "No probable serials found"
                
                invoices_without_serial.append({
                    'SDC ID': sdc,
                    'Serial Number': 'missing',
                    'MRC Number': row['Invoice number'],
                    'Invoice Date': invoice_date,
                    'Comment': comment
                })

        df_missing = pd.DataFrame(missing_invoices)
        df_sdc_summary = pd.DataFrame(sdc_summary_list)
        df_no_serial_invoices = pd.DataFrame(invoices_without_serial)

        return df_missing, df_sdc_summary, df_no_serial_invoices

    @staticmethod
    def fn_render_missing_invoices():
        """Render missing invoices report with enhanced data"""
        st.markdown("""
            <h4 style='background-color: #FF5722; color: white; padding: 8px; border-radius: 5px; 
            text-align: center;'>⚠️ MISSING INVOICES BY SDC</h4>
        """, unsafe_allow_html=True)

        if st.session_state.invoice_sales_data.empty:
            st.info("No invoice data available. Please upload a file.")
            return

        with st.expander("🔍 MISSING INVOICES REPORT", expanded=False):
            df_missing, df_sdc_summary, df_no_serial_invoices = cls_InvoiceSalesAnalysis.fn_detect_missing_invoices()

            if df_missing.empty and df_no_serial_invoices.empty:
                st.success("✅ No missing invoices detected! All serial numbers are consecutive and all invoices have serial numbers.")
            else:
                # Summary by SDC
                st.markdown("##### 📋 Summary by SDC")
                
                # Format dates for display
                df_sdc_display = df_sdc_summary.copy()
                df_sdc_display['First Invoice Date'] = df_sdc_display['First Invoice Date'].apply(
                    lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else 'N/A'
                )
                df_sdc_display['Last Invoice Date'] = df_sdc_display['Last Invoice Date'].apply(
                    lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else 'N/A'
                )
                
                st.dataframe(
                    df_sdc_display[['SDC ID', 'First Invoice', 'Last Invoice', 
                                   'First Invoice Date', 'Last Invoice Date', 'Number of Missing Invoices']],
                    use_container_width=True, 
                    hide_index=True
                )

                # Detailed Missing Invoices
                if not df_missing.empty:
                    st.warning(f"⚠️ Found {len(df_missing)} missing invoice(s)")
                    st.markdown("##### 📄 Detailed Missing Invoices")
                    st.dataframe(
                        df_missing[['SDC ID', 'Missing Serial Number', 'Missing Invoice ID', 
                                   'Invoice Period', 'Between Dates']],
                        use_container_width=True, 
                        hide_index=True
                    )

                # Invoices without serial numbers
                if not df_no_serial_invoices.empty:
                    st.error(f"❌ Found {len(df_no_serial_invoices)} invoice(s) without serial number(s)")
                    st.markdown("##### 📄 Invoices Without Serial Numbers")
                    
                    # Format dates for display
                    df_no_serial_display = df_no_serial_invoices.copy()
                    df_no_serial_display['Invoice Date'] = df_no_serial_display['Invoice Date'].apply(
                        lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) else 'N/A'
                    )
                    
                    st.dataframe(
                        df_no_serial_display[['SDC ID', 'Serial Number', 'MRC Number', 'Invoice Date', 'Comment']],
                        use_container_width=True, 
                        hide_index=True
                    )

                # Download option
                col_dl1, col_dl2 = st.columns([3, 1])
                with col_dl2:
                    excel_data = filehandler.fn_to_excel_multiple_sheets({
                        'Missing_Invoices': df_missing,
                        'Invoices_Without_Serial': df_no_serial_invoices,
                        'SDC_Summary': df_sdc_summary
                    })
                    filename = datetime.now().strftime("missing_invoices_%Y-%m-%d_%H%M.xlsx")
                    filehandler.fn_create_download_button(
                        label="📥 Download Report",
                        data=excel_data,
                        filename=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    # ---------- Main render ----------
    @staticmethod
    def fn_render():
        """Main render function for detailed Sales Invoices Analysis"""
        st.header("📊 Detailed Sales Invoices Analysis")

        # Initialize data
        cls_InvoiceSalesAnalysis.fn_initialize_invoice_data()

        # Data Upload
        cls_InvoiceSalesAnalysis.fn_render_data_upload()
        st.markdown("""<div style="border-top: 2px solid blue; margin: 10px 0;"></div>""", unsafe_allow_html=True)

        # Sales Summary
        cls_InvoiceSalesAnalysis.fn_render_sales_summary()
        st.markdown("""<div style="border-top: 2px solid blue; margin: 10px 0;"></div>""", unsafe_allow_html=True)

        # Missing Invoices
        cls_InvoiceSalesAnalysis.fn_render_missing_invoices()