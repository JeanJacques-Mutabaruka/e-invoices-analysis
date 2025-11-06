import numpy as np
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from io import BytesIO
from datetime import datetime, timedelta
# NEW:
from utils.file_handler import cls_Customfiles_Filetypehandler as filehandler

# ReportLab for simple PDF export (no wkhtmltopdf)
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from services.report_collector import AnalysisResultsCollector

class cls_Comparison:
    
    @staticmethod
    def fn_init():
        str_Pagetitle = "📈 DATA ANALYSIS BY GROUPS & CATEGORIES "
        st.markdown(f"""
            <h1 style='text-align: center; font-weight: bold; font-family: Cambria; font-size: 40px; padding: 10px; background-color: rgb(220,240,210);color:rgb(0,0,105);
            border-radius: 15px; position: sticky;'>{str_Pagetitle}</h1>
        """, unsafe_allow_html=True)

        if "file_metadata" not in st.session_state:
            str_Warning_message = "No uploaded files found. Please upload data from the main page."
            st.warning(str_Warning_message, icon="⚠️")

    @staticmethod
    def format_numbers(value):
        """Format numbers with commas and red font for negatives."""
        if isinstance(value, (int, float)):
            if pd.isna(value):
                return "-"
            if value < 0:
                return f'({abs(value):,.0f})'
            return f"{value:,.0f}"
        return value

    @staticmethod
    def generate_excel_download(df_summary, file_name="pivot_table.xlsx", str_summary_sheetname="Summary", 
                               df_datadetails=None, str_details_sheetname='Data details'):
        """Generate downloadable Excel file from DataFrame."""
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_summary.to_excel(writer, index=True, sheet_name=str_summary_sheetname)
            if df_datadetails is not None:
                df_datadetails.to_excel(writer, index=False, sheet_name=str_details_sheetname)
        output.seek(0)
        return output

    @staticmethod
    def fn_compare_numeric_fields(df_cat1, df_cat2, field_cat1, field_cat2, agg_func, cat1_name, cat2_name):
        """Compare numeric fields between two categories."""
        try:
            val_cat1 = df_cat1[field_cat1].agg(agg_func)
            val_cat2 = df_cat2[field_cat2].agg(agg_func)
            difference = val_cat1 - val_cat2
            
            return {
                'Field Category 1': field_cat1,
                'Field Category 2': field_cat2,
                'Aggregation Function': agg_func,
                f'Value {cat1_name}': val_cat1,
                f'Value {cat2_name}': val_cat2,
                'Difference': difference
            }
        except Exception as e:
            return None

    @staticmethod
    def fn_compare_non_numeric_fields(df_cat1, df_cat2, field_cat1, field_cat2, cat1_name, cat2_name):
        """Compare non-numeric fields between two categories."""
        try:
            # Get unique values
            set_cat1 = set(df_cat1[field_cat1].dropna().unique())
            set_cat2 = set(df_cat2[field_cat2].dropna().unique())
            
            # Count distinct
            count_cat1 = len(set_cat1)
            count_cat2 = len(set_cat2)
            
            # Find missing values
            missing_in_cat2 = set_cat1 - set_cat2
            missing_in_cat1 = set_cat2 - set_cat1
            
            # For display: show only first 10 items with count
            display_missing_in_cat2 = ', '.join(map(str, sorted(missing_in_cat2)[:10])) + \
                (f'... (+{len(missing_in_cat2)-10} more)' if len(missing_in_cat2) > 10 else '')
            display_missing_in_cat1 = ', '.join(map(str, sorted(missing_in_cat1)[:10])) + \
                (f'... (+{len(missing_in_cat1)-10} more)' if len(missing_in_cat1) > 10 else '')
            
            # For download: full list separated by semicolons
            full_missing_in_cat2 = '; '.join(map(str, sorted(missing_in_cat2)))
            full_missing_in_cat1 = '; '.join(map(str, sorted(missing_in_cat1)))
            
            return {
                'Field Category 1': field_cat1,
                'Field Category 2': field_cat2,
                'Aggregation Function': 'count distinct',
                f'Value {cat1_name}': count_cat1,
                f'Value {cat2_name}': count_cat2,
                'Difference': count_cat1 - count_cat2,
                f'Missing in {cat2_name}': display_missing_in_cat2,
                f'Missing in {cat1_name}': display_missing_in_cat1,
                f'Full_Missing in {cat2_name}': full_missing_in_cat2,  # Full list for download
                f'Full_Missing in {cat1_name}': full_missing_in_cat1   # Full list for download
            }
        except Exception as e:
            return None

    @staticmethod
    def fn_get_month_order():
        """Return month names in chronological order"""
        return ['January', 'February', 'March', 'April', 'May', 'June',
                'July', 'August', 'September', 'October', 'November', 'December']

    @staticmethod
    def fn_sort_by_month(df, month_col='Month_Name'):
        """Sort dataframe by month in chronological order"""
        month_order = cls_Comparison.fn_get_month_order()
        df[month_col] = pd.Categorical(df[month_col], categories=month_order, ordered=True)
        return df.sort_values([month_col])

    @staticmethod
    def fn_create_comparison_interface(categories, group_name, date_from, date_to, selected_duplicates):
        """Create dynamic comparison interface between two categories."""

        category_names = list(categories.keys())

        if len(category_names) < 2:
            st.warning("⚠️ Need at least 2 categories for comparison.")
            return

        # --- Title ---
        st.markdown("""
            <h4 style='text-align: center; background-color: rgb(255,245,220); color: rgb(150,75,0); 
            padding: 10px; border-radius: 8px; border: 2px solid rgb(255,200,100);'>
            🔄 DYNAMIC CATEGORY COMPARISON
            </h4>
        """, unsafe_allow_html=True)

        # --- Category selection ---
        col_cat1, col_cat2 = st.columns(2)
        with col_cat1:
            cat1_name = st.selectbox("📊 Category 1 (Baseline):", category_names, key=f"cat1_{group_name}")
        with col_cat2:
            cat2_name = st.selectbox("📊 Category 2 (Compare To):", [c for c in category_names if c != cat1_name], key=f"cat2_{group_name}")

        if cat1_name == cat2_name:
            st.warning("⚠️ Please select two different categories.")
            return

        # --- Get data ---
        df_cat1 = categories[cat1_name].copy()
        df_cat2 = categories[cat2_name].copy()

        # --- Date filter ---
        if "TRANSACTION DATE" in df_cat1.columns:
            end_time = pd.Timestamp(date_to) + pd.Timedelta(hours=23, minutes=59, seconds=59)
            df_cat1 = df_cat1[(df_cat1["TRANSACTION DATE"] >= pd.Timestamp(date_from)) &
                            (df_cat1["TRANSACTION DATE"] <= end_time)]
        if "TRANSACTION DATE" in df_cat2.columns:
            end_time = pd.Timestamp(date_to) + pd.Timedelta(hours=23, minutes=59, seconds=59)
            df_cat2 = df_cat2[(df_cat2["TRANSACTION DATE"] >= pd.Timestamp(date_from)) &
                            (df_cat2["TRANSACTION DATE"] <= end_time)]

        # --- Duplicate Status filter ---
        if "Duplicate Status" in df_cat1.columns:
            df_cat1 = df_cat1[df_cat1["Duplicate Status"].isin(selected_duplicates)]
        if "Duplicate Status" in df_cat2.columns:
            df_cat2 = df_cat2[df_cat2["Duplicate Status"].isin(selected_duplicates)]

        # --- Info summary ---
        st.markdown(f"""
            <div style='background-color: rgb(240,248,255); padding: 10px; border-radius: 5px; text-align: center; font-weight: bold; font-size: 20px;'>
            📅 <b>Comparison Period:</b> {date_from} → {date_to} |
            🛑 <b>Duplicate status:</b> {', '.join(selected_duplicates)}<br>
            {cat1_name}: {len(df_cat1):,} records --vs-- {cat2_name}: {len(df_cat2):,} records
            </div>
        """, unsafe_allow_html=True)

        # --- Field selection ---
        st.markdown("<b>🔧 COMPARISON CONFIGURATION</b>", unsafe_allow_html=True)

        # --- Numeric fields ---
        st.markdown("##### 🔢 Numeric Fields")
        num_cols1 = df_cat1.select_dtypes(include=[np.number]).columns.tolist()
        num_cols2 = df_cat2.select_dtypes(include=[np.number]).columns.tolist()

        default_num1 = [c for c in num_cols1 if "AMOUNT" in c.upper() or "TOTAL" in c.upper()][:3]
        if not default_num1 and num_cols1:
            default_num1 = num_cols1[:3]

        default_num2 = [c for c in num_cols2 if c in default_num1]
        if not default_num2 and num_cols2:
            default_num2 = num_cols2[:3]

        col1, col2, col3 = st.columns([3, 3, 2])
        with col1:
            fnum1 = st.multiselect(f"Fields in {cat1_name}", num_cols1, default=default_num1, key=f"num1_{group_name}")
        with col2:
            fnum2 = st.multiselect(f"Fields in {cat2_name}", num_cols2, default=default_num2, key=f"num2_{group_name}")
        with col3:
            aggs = st.multiselect("Agg Functions", ["sum", "mean", "min", "max", "count"], default=["sum"], key=f"aggs_{group_name}")

        st.markdown("""<div style="border-top: 1px dotted blue; margin-top: 1px; margin-bottom: 1px;"></div>""", unsafe_allow_html=True)

        # --- Text / Categorical fields ---
        st.markdown("##### 🔤 Text / Categorical Fields")
        text_cols1 = [c for c in df_cat1.select_dtypes(exclude=[np.number]) if "DATE" not in c.upper()]
        text_cols2 = [c for c in df_cat2.select_dtypes(exclude=[np.number]) if "DATE" not in c.upper()]

        default_txt1 = text_cols1[:2] if text_cols1 else []
        default_txt2 = [c for c in text_cols2 if c in default_txt1]
        if not default_txt2 and text_cols2:
            default_txt2 = text_cols2[:2]

        col1, col2 = st.columns(2)
        with col1:
            ftxt1 = st.multiselect(f"Fields in {cat1_name}", text_cols1, default=default_txt1, key=f"txt1_{group_name}")
        with col2:
            ftxt2 = st.multiselect(f"Fields in {cat2_name}", text_cols2, default=default_txt2, key=f"txt2_{group_name}")

        # --- Generate button ---
        if st.button("🔍 GENERATE COMPARISON", use_container_width=True, key=f"btn_run_{group_name}"):

            comp_num, comp_txt = [], []

            # Numeric comparison
            if fnum1 and fnum2:
                for i in range(max(len(fnum1), len(fnum2))):
                    f1 = fnum1[i % len(fnum1)]
                    f2 = fnum2[i % len(fnum2)]
                    for a in aggs:
                        res = cls_Comparison.fn_compare_numeric_fields(df_cat1, df_cat2, f1, f2, a, cat1_name, cat2_name)
                        if res:
                            comp_num.append(res)

            # Text comparison
            if ftxt1 and ftxt2:
                for i in range(max(len(ftxt1), len(ftxt2))):
                    f1 = ftxt1[i % len(ftxt1)]
                    f2 = ftxt2[i % len(ftxt2)]
                    res = cls_Comparison.fn_compare_non_numeric_fields(df_cat1, df_cat2, f1, f2, cat1_name, cat2_name)
                    if res:
                        comp_txt.append(res)

            if not comp_num and not comp_txt:
                st.warning("⚠️ No results generated. Please adjust selections.")
                return

            st.session_state[f'comp_results_{group_name}'] = {
                'comp_num': comp_num,
                'comp_txt': comp_txt,
                'cat1_name': cat1_name,
                'cat2_name': cat2_name,
                'df_cat1': df_cat1,
                'df_cat2': df_cat2
            }
            
            # 🆕 ADD: Store comparison results in collector for AI report
            if 'analysis_collector' in st.session_state:
                st.session_state.analysis_collector.add_comparison_result(
                    group_name, cat1_name, cat2_name, comp_num, comp_txt
                )

        # === Display results if exist ===
        if f'comp_results_{group_name}' not in st.session_state:
            st.info("👆 Click 'GENERATE COMPARISON' button to see results.")
            return

        results = st.session_state[f'comp_results_{group_name}']
        comp_num = results['comp_num']
        comp_txt = results['comp_txt']
        cat1_name = results['cat1_name']
        cat2_name = results['cat2_name']
        df_cat1 = results['df_cat1']
        df_cat2 = results['df_cat2']

        st.success("✅ Comparison completed successfully!")

        # === Tabs ===
        tab1, tab2, tab3, tab4 = st.tabs([
            "🔢 Numeric Fields Comparison Results",
            "🔤 Text/Categorical Fields Comparison Results",
            f"📉 Missing in {cat2_name}",
            f"📈 Missing in {cat1_name}"
        ])

        # === TAB 1: Numeric Fields ===
        with tab1:
            if comp_num:
                df_num = pd.DataFrame(comp_num)
                def highlight_diff(v):
                    if isinstance(v, (int, float)) and not pd.isna(v) and v != 0:
                        return 'background-color: #ffcccc' if v < 0 else 'background-color: #ccffcc'
                    return ''
                st.dataframe(
                    df_num.style.map(highlight_diff, subset=["Difference"]).format({
                        f'Value {cat1_name}': cls_Comparison.format_numbers,
                        f'Value {cat2_name}': cls_Comparison.format_numbers,
                        'Difference': cls_Comparison.format_numbers
                    }),
                    use_container_width=True,
                    height=250
                )
                st.download_button("📥 Download Numeric Comparison", df_num.to_csv(index=False), "numeric_comparison.csv", "text/csv", key=f"download_numeric_{group_name}")
            else:
                st.info("ℹ️ No numeric comparison results found.")

        # === TAB 2: Text/Categorical Fields ===
        with tab2:
            if comp_txt:
                df_txt = pd.DataFrame(comp_txt)

                # 1) Rename the category field columns dynamically if present
                rename_map = {}
                if "Field Category 1" in df_txt.columns:
                    rename_map["Field Category 1"] = f"Field in {cat1_name}"
                if "Field Category 2" in df_txt.columns:
                    rename_map["Field Category 2"] = f"Field in {cat2_name}"
                if rename_map:
                    df_txt = df_txt.rename(columns=rename_map)

                # 2) Build counts from any 'Full_Missing in ...' columns (preferred)
                def _count_from_full_col(x):
                    """Count items from the 'Full_Missing...' source robustly."""
                    if x is None or (isinstance(x, float) and pd.isna(x)):
                        return 0
                    if isinstance(x, (list, tuple, set)):
                        return len([v for v in x if str(v).strip()])
                    try:
                        import numpy as _np
                        import pandas as _pd
                        if isinstance(x, (_pd.Series, _np.ndarray)):
                            lst = list(x)
                            return len([v for v in lst if str(v).strip()])
                    except Exception:
                        pass
                    if isinstance(x, str):
                        if ";" in x:
                            parts = [p.strip() for p in x.split(";") if p.strip()]
                            return len(parts)
                        elif "," in x:
                            parts = [p.strip() for p in x.split(",") if p.strip()]
                            return len(parts)
                        else:
                            return 1 if x.strip() else 0
                    return 0

                # Use 'Full_Missing in ...' columns to create counts
                full_cols = [c for c in df_txt.columns if c.startswith("Full_Missing in ")]
                if full_cols:
                    for full_col in full_cols:
                        short_col = full_col.replace("Full_", "")
                        df_txt[short_col] = df_txt[full_col].apply(_count_from_full_col)
                else:
                    for c in [col for col in df_txt.columns if col.startswith("Missing in ")]:
                        df_txt[c] = df_txt[c].apply(_count_from_full_col)

                # 3) Prepare display
                display_cols = [c for c in df_txt.columns if not c.startswith("Full_")]
                df_display = df_txt[display_cols].copy()

                # 4) Tooltip
                st.markdown("""
                    <div style='font-size: 12px; color: gray; margin-top: -5px;'>
                    ℹ️ The counts in "Missing in ..." columns are derived from the full lists (Full_Missing...). 
                    Full item details are available in the corresponding "Missing in ..." tabs below.
                    </div>
                """, unsafe_allow_html=True)

                # 5) Show the concise table
                st.dataframe(df_display, use_container_width=True, height=250)

                # Download
                df_full_for_download = df_txt.copy()
                rename_full_for_export = {c: c.replace("Full_", "") for c in df_full_for_download.columns if c.startswith("Full_")}
                if rename_full_for_export:
                    df_full_for_download = df_full_for_download.rename(columns=rename_full_for_export)
                st.download_button("📥 Download Categorical Comparison (Full)", df_full_for_download.to_csv(index=False), "text_comparison_full.csv", "text/csv", key=f"download_categorical_{group_name}")
            else:
                st.info("ℹ️ No text/categorical comparison results available.")

        # === TAB 3 & TAB 4: build missing item details ===
        missing_1in2, missing_2in1 = [], []
        if comp_txt:
            for row in comp_txt:
                f1 = row.get("Field Category 1") or row.get("Field in " + cat1_name) or row.get("Field in " + cat1_name, "")
                f2 = row.get("Field Category 2") or row.get("Field in " + cat2_name) or row.get("Field in " + cat2_name, "")

                full_key_in_2 = f"Full_Missing in {cat2_name}"
                full_key_in_1 = f"Full_Missing in {cat1_name}"

                # Missing from cat2
                miss_in_2 = row.get(full_key_in_2, "") or row.get(f"Missing in {cat2_name}", "")
                if miss_in_2 and f1 in df_cat1.columns:
                    vals = []
                    if isinstance(miss_in_2, (list, tuple, set)):
                        vals = [str(v).strip() for v in miss_in_2 if str(v).strip()]
                    elif isinstance(miss_in_2, str):
                        if ";" in miss_in_2:
                            vals = [v.strip() for v in miss_in_2.split(";") if v.strip()]
                        elif "," in miss_in_2:
                            vals = [v.strip() for v in miss_in_2.split(",") if v.strip()]
                        else:
                            if miss_in_2.strip():
                                vals = [miss_in_2.strip()]
                    if vals:
                        sub = df_cat1[df_cat1[f1].astype(str).isin(vals)].copy()
                        if not sub.empty and "TRANSACTION DATE" in sub.columns:
                            sub["Comparison_Field"] = f1
                            sub["Transaction_Date"] = pd.to_datetime(sub["TRANSACTION DATE"], errors="coerce")
                            sub["Year"] = sub["Transaction_Date"].dt.year.astype(str)
                            sub["Month"] = sub["Transaction_Date"].dt.month
                            sub["Month_Name"] = sub["Transaction_Date"].dt.strftime("%B")
                            sub["Missing_From"] = cat2_name
                            sub["Present_In"] = cat1_name
                            missing_1in2.append(sub)

                # Missing from cat1
                miss_in_1 = row.get(full_key_in_1, "") or row.get(f"Missing in {cat1_name}", "")
                if miss_in_1 and f2 in df_cat2.columns:
                    vals = []
                    if isinstance(miss_in_1, (list, tuple, set)):
                        vals = [str(v).strip() for v in miss_in_1 if str(v).strip()]
                    elif isinstance(miss_in_1, str):
                        if ";" in miss_in_1:
                            vals = [v.strip() for v in miss_in_1.split(";") if v.strip()]
                        elif "," in miss_in_1:
                            vals = [v.strip() for v in miss_in_1.split(",") if v.strip()]
                        else:
                            if miss_in_1.strip():
                                vals = [miss_in_1.strip()]
                    if vals:
                        sub = df_cat2[df_cat2[f2].astype(str).isin(vals)].copy()
                        if not sub.empty and "TRANSACTION DATE" in sub.columns:
                            sub["Comparison_Field"] = f2
                            sub["Transaction_Date"] = pd.to_datetime(sub["TRANSACTION DATE"], errors="coerce")
                            sub["Year"] = sub["Transaction_Date"].dt.year.astype(str)
                            sub["Month"] = sub["Transaction_Date"].dt.month
                            sub["Month_Name"] = sub["Transaction_Date"].dt.strftime("%B")
                            sub["Missing_From"] = cat1_name
                            sub["Present_In"] = cat2_name
                            missing_2in1.append(sub)

        # 🆕 ADD: Store missing items summary in collector for AI report
        if (missing_1in2 or missing_2in1) and 'analysis_collector' in st.session_state:
            st.session_state.analysis_collector.add_missing_items_summary(
                group_name, cat1_name, cat2_name, missing_1in2, missing_2in1
            )

        # TAB 3: Category 1 missing in Category 2
        with tab3:
            if missing_1in2:
                df_a = pd.concat(missing_1in2, ignore_index=True)
                try:
                    df_a = cls_Comparison.fn_sort_by_month(df_a)
                except Exception:
                    pass

                unique_fields = df_a["Comparison_Field"].unique()
                fields_str = ", ".join(unique_fields) if len(unique_fields) <= 3 else f"{', '.join(unique_fields[:3])} (+{len(unique_fields)-3} more)"
                st.markdown(f"### 📉 {fields_str} of {cat1_name} Missing in {cat2_name}")

                col1, col2, col3 = st.columns(3)
                years = sorted(df_a["Year"].dropna().unique(), reverse=True)
                month_order = cls_Comparison.fn_get_month_order() if hasattr(cls_Comparison, "fn_get_month_order") else None
                if month_order is not None:
                    available_months = df_a["Month_Name"].dropna().unique().tolist()
                    months = [m for m in month_order if m in available_months]
                else:
                    months = sorted(df_a["Month_Name"].dropna().unique())

                missing_from = df_a["Missing_From"].unique().tolist()

                with col1:
                    year_f = st.multiselect("Filter by Year", years, default=years, key=f"year_filter_{cat1_name}_in_{cat2_name}")
                with col2:
                    month_f = st.multiselect("Filter by Month", months, default=months, key=f"month_filter_{cat1_name}_in_{cat2_name}")
                with col3:
                    miss_f = st.multiselect("Missing From", missing_from, default=missing_from, key=f"miss_filter_{cat1_name}_in_{cat2_name}")

                df_filtered = df_a[df_a["Year"].isin(year_f) & df_a["Month_Name"].isin(month_f) & df_a["Missing_From"].isin(miss_f)]
                try:
                    df_filtered = cls_Comparison.fn_sort_by_month(df_filtered.copy())
                except Exception:
                    pass
                df_filtered = df_filtered.sort_values(['Year', 'Month_Name'], ascending=[False, True])

                numeric_cols = df_filtered.select_dtypes(include=[np.number]).columns.tolist()
                exclude_cols = ['Month', 'Year', 'Comparison_Field', 'Day', 'Days', 'YEAR', 'MONTH', 'DAY']
                numeric_cols = [col for col in numeric_cols if col not in exclude_cols and not col.startswith('Unnamed') and 'year' not in col.lower() and 'month' not in col.lower() and 'day' not in col.lower()]

                if numeric_cols or not df_filtered.empty:
                    st.markdown(f"#### 💰 Summary of Missing {fields_str}")
                    totals_dict = {'Number': len(df_filtered)}
                    for col in numeric_cols:
                        total = df_filtered[col].sum()
                        # Ensure numeric type for proper formatting
                        totals_dict[col] = float(total) if pd.notna(total) else 0

                    total_cols = st.columns(min(len(totals_dict), 7))
                    for idx, (col_name, total_value) in enumerate(totals_dict.items()):
                        with total_cols[idx % len(total_cols)]:
                            if col_name == 'Number':
                                st.markdown(f"""
                                    <div style='background-color: #e3f2fd; padding: 8px; border-radius: 5px; text-align: center;'>
                                        <div style='font-size: 12px; color: #666;'>{col_name}</div>
                                        <div style='font-size: 18px; font-weight: bold; color: #1976d2;'>{total_value:,}</div>
                                    </div>
                                """, unsafe_allow_html=True)
                            else:
                                # Force consistent formatting with 0 decimals for all numeric values
                                try:
                                    numeric_val = float(total_value)
                                    if numeric_val < 0:
                                        formatted_value = f'({abs(numeric_val):,.0f})'
                                    elif numeric_val == 0:
                                        formatted_value = f'-'
                                    else:
                                        formatted_value = f'{numeric_val:,.0f}'
                                except (ValueError, TypeError):
                                    formatted_value = str(total_value)
                                
                                st.markdown(f"""
                                    <div style='background-color: #f5f5f5; padding: 8px; border-radius: 5px; text-align: center;'>
                                        <div style='font-size: 12px; color: #666;'>{col_name}</div>
                                        <div style='font-size: 18px; font-weight: bold; color: #333;'>{formatted_value}</div>
                                    </div>
                                """, unsafe_allow_html=True)
                    st.markdown("""<div style="border-top: 1px dashed #ccc; margin: 10px 0;"></div>""", unsafe_allow_html=True)

                st.dataframe(df_filtered, use_container_width=True, height=400)
                st.download_button("📥 Download Missing Items (Filtered)", df_filtered.to_csv(index=False), f"missing_{cat1_name}_in_{cat2_name}.csv", "text/csv", key=f"download_missing_1in2_{group_name}")
            else:
                st.info(f"✅ No items from {cat1_name} missing in {cat2_name}.")

        # TAB 4: Category 2 missing in Category 1
        with tab4:
            if missing_2in1:
                df_b = pd.concat(missing_2in1, ignore_index=True)
                try:
                    df_b = cls_Comparison.fn_sort_by_month(df_b)
                except Exception:
                    pass

                unique_fields = df_b["Comparison_Field"].unique()
                fields_str = ", ".join(unique_fields) if len(unique_fields) <= 3 else f"{', '.join(unique_fields[:3])} (+{len(unique_fields)-3} more)"
                st.markdown(f"### 📈 {fields_str} of {cat2_name} Missing in {cat1_name}")

                col1, col2, col3 = st.columns(3)
                years = sorted(df_b["Year"].dropna().unique(), reverse=True)
                month_order = cls_Comparison.fn_get_month_order() if hasattr(cls_Comparison, "fn_get_month_order") else None
                if month_order is not None:
                    available_months = df_b["Month_Name"].dropna().unique().tolist()
                    months = [m for m in month_order if m in available_months]
                else:
                    months = sorted(df_b["Month_Name"].dropna().unique())

                missing_from = df_b["Missing_From"].unique().tolist()

                with col1:
                    year_f = st.multiselect("Filter by Year", years, default=years, key=f"year_filter_{cat2_name}_in_{cat1_name}")
                with col2:
                    month_f = st.multiselect("Filter by Month", months, default=months, key=f"month_filter_{cat2_name}_in_{cat1_name}")
                with col3:
                    miss_f = st.multiselect("Missing From", missing_from, default=missing_from, key=f"miss_filter_{cat2_name}_in_{cat1_name}")

                df_filtered = df_b[df_b["Year"].isin(year_f) & df_b["Month_Name"].isin(month_f) & df_b["Missing_From"].isin(miss_f)]
                try:
                    df_filtered = cls_Comparison.fn_sort_by_month(df_filtered.copy())
                except Exception:
                    pass
                df_filtered = df_filtered.sort_values(['Year', 'Month_Name'], ascending=[False, True])

                numeric_cols = df_filtered.select_dtypes(include=[np.number]).columns.tolist()
                exclude_cols = ['Month', 'Year', 'Comparison_Field', 'Day', 'Days', 'YEAR', 'MONTH', 'DAY']
                numeric_cols = [col for col in numeric_cols if col not in exclude_cols and not col.startswith('Unnamed') and 'year' not in col.lower() and 'month' not in col.lower() and 'day' not in col.lower()]

                if numeric_cols or not df_filtered.empty:
                    st.markdown(f"#### 💰 Summary of Missing {fields_str}")
                    totals_dict = {'Number': len(df_filtered)}
                    for col in numeric_cols:
                        total = df_filtered[col].sum()
                        # Ensure numeric type for proper formatting
                        totals_dict[col] = float(total) if pd.notna(total) else 0

                    total_cols = st.columns(min(len(totals_dict), 5))
                    for idx, (col_name, total_value) in enumerate(totals_dict.items()):
                        with total_cols[idx % len(total_cols)]:
                            if col_name == 'Number':
                                st.markdown(f"""
                                    <div style='background-color: #e3f2fd; padding: 8px; border-radius: 5px; text-align: center;'>
                                        <div style='font-size: 12px; color: #666;'>{col_name}</div>
                                        <div style='font-size: 18px; font-weight: bold; color: #1976d2;'>{total_value:,}</div>
                                    </div>
                                """, unsafe_allow_html=True)
                            else:
                                # Force consistent formatting with 0 decimals for all numeric values
                                try:
                                    numeric_val = float(total_value)
                                    if numeric_val < 0:
                                        formatted_value = f'({abs(numeric_val):,.0f})'
                                    else:
                                        formatted_value = f'{numeric_val:,.0f}'
                                except (ValueError, TypeError):
                                    formatted_value = str(total_value)
                                
                                st.markdown(f"""
                                    <div style='background-color: #f5f5f5; padding: 8px; border-radius: 5px; text-align: center;'>
                                        <div style='font-size: 12px; color: #666;'>{col_name}</div>
                                        <div style='font-size: 18px; font-weight: bold; color: #333;'>{formatted_value}</div>
                                    </div>
                                """, unsafe_allow_html=True)
                    st.markdown("""<div style="border-top: 1px dashed #ccc; margin: 10px 0;"></div>""", unsafe_allow_html=True)

                st.dataframe(df_filtered, use_container_width=True, height=400)
                st.download_button("📥 Download Missing Items (Filtered)", df_filtered.to_csv(index=False), f"missing_{cat2_name}_in_{cat1_name}.csv", "text/csv", key=f"download_missing_2in1_{group_name}")
            else:
                st.info(f"✅ No items from {cat2_name} missing in {cat1_name}.")
   
   
    @staticmethod
    def fn_compare_groups():
        """Trigger comparison of categories within the same FINANCIAL STATEMENT GROUP using TABS."""

        cls_Comparison.fn_init()

        # 🆕 Initialize results collector
        if 'analysis_collector' not in st.session_state:
            st.session_state.analysis_collector = AnalysisResultsCollector()
        collector = st.session_state.analysis_collector

        if "comparison_triggered" not in st.session_state:
            st.session_state.comparison_triggered = False
        
        st.markdown("""<div style="border-top: 1px solid blue; margin-top: 1px; margin-bottom: 1px;"></div>""", unsafe_allow_html=True)
        st.markdown("""<div style="border-top: 1px solid blue; margin-top: 1px; margin-bottom: 1px;"></div>""", unsafe_allow_html=True)

        # Add CSS for button and table styling
        st.markdown("""
            <style>
                /* Button Styling */
                div[data-testid="stButton"] > button {
                    background-color: rgb(220,240,210);
                    font-weight: bold;
                    font-style: italic;
                    color: blue;
                    padding: 10px;
                    border-radius: 5px;
                    font-family: Cambria;
                }
                div[data-testid="stButton"] > button:hover {
                    background-color: rgb(200,230,190);
                }

                /* Tab Styling */
                .stTabs [data-baseweb="tab-list"] {
                    gap: 8px;
                }
                .stTabs [data-baseweb="tab"] {
                    background-color: rgb(240,240,240);
                    border-radius: 5px;
                    padding: 10px 20px;
                    font-weight: bold;
                    color: rgb(0,0,100);
                }
                .stTabs [aria-selected="true"] {
                    background-color: rgb(220,240,210);
                    color: rgb(0,0,150);
                }
            </style>
        """, unsafe_allow_html=True)

        obj_mybutton = st.button("GET DATA SUMMARIES COMPARISONS within GROUPS", key="btn_Compare_within_Groups")
        if obj_mybutton:
            st.session_state.comparison_triggered = True

        if st.session_state.comparison_triggered:
            if "file_metadata" not in st.session_state or not st.session_state.file_metadata:
                st.warning("No data available for comparison.")
                return
            # 🆕 Capture metadata
            collector.set_metadata(st.session_state.file_metadata)

            data_groups = {}

            # 🟢 Organize Data by Group & Category
            for file_name, metadata in st.session_state.file_metadata.items():
                for sheet_name, values in metadata.items():
                    category = values[0]
                    df_cleaned = values[5]
                    
                    if "FINANCIAL STATEMENT GROUP" in df_cleaned.columns:
                        unique_groups = df_cleaned["FINANCIAL STATEMENT GROUP"].unique()
                        
                        for group in unique_groups:
                            if group not in data_groups:
                                data_groups[group] = {}
                            
                            df_group = df_cleaned[df_cleaned["FINANCIAL STATEMENT GROUP"] == group].copy()
                            df_group["Source File"] = file_name

                            if "TRANSACTION DATE" in df_group.columns:
                                df_group["YEAR"] = df_group["TRANSACTION DATE"].dt.year
                                df_group["YEAR-MONTH"] = df_group["TRANSACTION DATE"].dt.strftime("%Y-%m")
                            
                            if category not in data_groups[group]:
                                data_groups[group][category] = df_group
                            else:
                                data_groups[group][category] = pd.concat([data_groups[group][category], df_group])

            int_countgroups = 1
            for group, categories in data_groups.items():
                # 🆕 Capture group summary
                collector.add_group_summary(group, categories)        

                st.markdown(f"### 📌 {int_countgroups}- {group} data : {len(categories)} categories")

                # 🟢 Apply "Duplicate Status" Calculation at Group Level BEFORE Filtering
                for category in categories:
                    df_with_dups = filehandler.fn_check_duplicatedrecords(categories[category], category)
                    categories[category] = df_with_dups 

                    # 🆕 Capture duplicate summary
                    collector.add_duplicate_summary(group, category, df_with_dups)

                with st.expander(f"Group: {group}", expanded=True):

                    # 🟢 Styled Filter Box
                    st.markdown("""<div style="border-top: 1px solid blue; margin-top: 10px; margin-bottom: 10px;"></div>""", unsafe_allow_html=True)
                    str_Filters_title = " 🔍 Filters"
                    st.markdown(f"""
                        <h5 style='text-align: center; font-weight: bold; font-family: Cambria; font-size: 25px; padding: 3px; background-color: rgb(220,240,210);color:rgb(0,0,100);
                        border-radius: 5px; position: sticky;'>{str_Filters_title}</h5>
                    """, unsafe_allow_html=True)
                    
                    # 🟢 DATE FILTER
                    if any("TRANSACTION DATE" in df.columns for df in categories.values()):
                        min_date = min(df["TRANSACTION DATE"].min() for df in categories.values() if "TRANSACTION DATE" in df.columns)
                        max_date = max(df["TRANSACTION DATE"].max() for df in categories.values() if "TRANSACTION DATE" in df.columns) + timedelta(days=1)

                        col1, col2, col3 = st.columns([1, 1, 4])
                        with col1:
                            date_from = st.date_input("📅 From Date:", min_value=min_date, max_value=max_date, value=min_date, key=f"from_date_{group}", format="YYYY-MM-DD")
                        with col2:
                            date_to = st.date_input("📅 To Date:", min_value=min_date, max_value=max_date, value=max_date, key=f"to_date_{group}", format="YYYY-MM-DD")

                    # 🟢 DUPLICATE STATUS FILTER
                    if any("Duplicate Status" in df.columns for df in categories.values()):
                        unique_duplicates = set()
                        for df in categories.values():
                            if "Duplicate Status" in df.columns:
                                unique_duplicates.update(df["Duplicate Status"].dropna().unique())

                        with col3:
                            selected_duplicates = st.multiselect(
                                f"🛑 Filter by Duplicate Status for {group}:",
                                sorted(unique_duplicates),
                                default=sorted(unique_duplicates),
                                key=f"dup_status_{group}"
                            )

                    st.markdown("""<div style="border-top: 1px solid blue; margin-top: 1px; margin-bottom: 1px;"></div>""", unsafe_allow_html=True)

                    # ⭐ CREATE TABS FOR CATEGORIES + COMPARISON TAB ⭐
                    category_names = list(categories.keys())
                    
                    # Create tab labels with record counts
                    tab_labels = [f"🎯 {i+1}. {cat} ({len(categories[cat])} records)" 
                                 for i, cat in enumerate(category_names)]
                    
                    # Add comparison tab with special styling indicator
                    tab_labels.append("🔄 COMPARE CATEGORIES")
                    
                    # Create tabs
                    tabs = st.tabs(tab_labels)

                    # 🟢 Process Each Category in its Own Tab
                    for tab_idx, category in enumerate(category_names):
                        with tabs[tab_idx]:
                            df_combined = categories[category]
                            
                            if not df_combined.empty:
                                # 🟢 Apply DATE Filter
                                if "TRANSACTION DATE" in df_combined.columns:
                                    date_to_with_time = pd.Timestamp(date_to) + pd.Timedelta(hours=23, minutes=59, seconds=59)
                                    df_combined = df_combined[
                                        (df_combined["TRANSACTION DATE"] >= pd.Timestamp(date_from)) & 
                                        (df_combined["TRANSACTION DATE"] <= pd.Timestamp(date_to_with_time))
                                    ]

                                # 🟢 Apply DUPLICATE STATUS Filter
                                if "Duplicate Status" in df_combined.columns:
                                    df_combined = df_combined[df_combined["Duplicate Status"].isin(selected_duplicates)]

                                numeric_columns = df_combined.select_dtypes(include="number").columns.tolist()
                                default_amount_fields = [col for col in numeric_columns if ("AMOUNT" in col.upper() or "VAT" in col.upper())][:2]  

                                # Category Title
                                str_Category_title = f"{category} - Filtered Results"
                                st.markdown(f"""
                                    <h5 style='text-align: center; font-weight: bold; font-family: Cambria; font-size: 20px; 
                                    padding: 5px; background-color: rgb(240,248,255);color:rgb(0,0,150);
                                    border-radius: 5px; border: 1px solid rgb(180,200,220);'>{str_Category_title}</h5>
                                """, unsafe_allow_html=True)

                                # 📊 Summary Statistics Section
                                st.markdown("""
                                    <div style='background-color: rgb(240,248,255); padding: 8px; border-radius: 5px; 
                                    border-left: 4px solid rgb(100,149,237); margin: 10px 0;'>
                                    <b>📊 SUMMARY STATISTICS</b>
                                    </div>
                                """, unsafe_allow_html=True)
                                
                                col_01, col_02 = st.columns([3, 2])
                                
                                with col_01:
                                    selected_fields = st.multiselect(
                                        "Select columns to display:",
                                        numeric_columns,
                                        default=default_amount_fields,
                                        key=f"selected_fields_{group}_{category}"
                                    )

                                with col_02:
                                    available_aggs = ["sum", "min", "mean", "max", "count"]
                                    selected_aggs = st.multiselect(
                                        "Select Summary functions:",
                                        available_aggs,
                                        default=["sum"],
                                        key=f"agg_funcs_{group}_{category}"
                                    )

                                st.markdown("""<div style="border-top: 1px dashed #ccc; margin-top: 5px; margin-bottom: 5px;"></div>""", unsafe_allow_html=True)
                                
                                if selected_fields and selected_aggs:
                                    df_aggregated = df_combined[selected_fields].agg(selected_aggs)
                                    obj_table = f"{df_aggregated.style.format(cls_Comparison.format_numbers).to_html()}"
                                    st.markdown(f"""
                                        <div style='text-align: center; padding: 8px; background-color: rgb(248, 252, 248);color:rgb(0,0,250);
                                        border-radius: 8px; border: 1px solid rgb(200,220,200); display: flex; justify-content: center;'>{obj_table}</div>
                                    """, unsafe_allow_html=True)

                                st.markdown("""<div style="border-top: 2px solid blue; margin-top: 15px; margin-bottom: 15px;"></div>""", unsafe_allow_html=True)
                                
                                # 📊 Pivot Table Section
                                st.markdown("""
                                    <div style='background-color: rgb(240,255,240); padding: 8px; border-radius: 5px; 
                                    border-left: 4px solid rgb(34,139,34); margin: 10px 0;'>
                                    <b>📊 PIVOT TABLE ANALYSIS</b>
                                    </div>
                                """, unsafe_allow_html=True)
                                
                                col_01, col_02 = st.columns([3, 7])
                                with col_01:
                                    pivot_columns = st.multiselect(
                                        "Choose Pivot Columns:", 
                                        options=df_combined.columns.tolist(), 
                                        default=["YEAR", "YEAR-MONTH"] if "YEAR" in df_combined.columns else df_combined.columns.tolist()[:1],
                                        key=f"pivot_cols_{group}_{category}"
                                    )

                                with col_02:
                                    pivot_value_options = [(col, agg) for col in selected_fields for agg in selected_aggs]
                                    pivot_value_selections = st.multiselect(
                                        "Choose Values and (summary function):",
                                        options=pivot_value_options,
                                        default=pivot_value_options,
                                        format_func=lambda x: f"{x[0]} ({x[1]})", 
                                        key=f"pivot_vals_{group}_{category}"
                                    )
                                
                                st.markdown("""<div style="border-top: 1px dashed #ccc; margin-top: 5px; margin-bottom: 10px;"></div>""", unsafe_allow_html=True)
                                
                                if pivot_columns and pivot_value_selections:
                                    agg_dict = {col: agg for col, agg in pivot_value_selections}
                                    pivot_df = df_combined.pivot_table(
                                        index=pivot_columns, 
                                        values=list(agg_dict.keys()), 
                                        aggfunc=agg_dict, 
                                        fill_value=0
                                    )
                                else:
                                    # Fallback pivot
                                    pivot_df = df_combined.pivot_table(
                                        index=["YEAR", "YEAR-MONTH"] if "YEAR" in df_combined.columns else df_combined.columns.tolist()[:1], 
                                        values=default_amount_fields if default_amount_fields else numeric_columns[:1], 
                                        aggfunc="sum", 
                                        fill_value=0
                                    )
                                
                                pivot_df_display = pivot_df.map(cls_Comparison.format_numbers)
                                
                                # Configure AG Grid
                                gb = GridOptionsBuilder.from_dataframe(pivot_df.reset_index())
                                gb.configure_default_column(min_column_width=100, groupable=True, enableRowGroup=True)
                                gb.configure_pagination(paginationPageSize=50)
                                grid_options = gb.build()

                                height = min(600, 40 + len(pivot_df) * 35)
                                AgGrid(
                                    pivot_df_display.reset_index(), 
                                    gridOptions=grid_options, 
                                    height=height, 
                                    fit_columns_on_grid_load=True,
                                    key=f"Pivotdisplay_{group}_{category}"
                                )
                                
                                # Download Button
                                excel_data = cls_Comparison.generate_excel_download(
                                    pivot_df,
                                    str_summary_sheetname='Summary',
                                    df_datadetails=df_combined,
                                    str_details_sheetname=category
                                )
                                st.download_button(
                                    "📥 Download Pivot Table & Details", 
                                    data=excel_data, 
                                    file_name=f"pivot_table_{group}_{category}__{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.xlsx", 
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key=f"Pivottable_{group}_{category}"
                                )
                                
                                st.markdown("""<div style="border-top: 1px solid green; margin-top: 10px;"></div>""", unsafe_allow_html=True)

                    # 🔄 COMPARISON TAB (Last Tab)
                    with tabs[-1]:
                        cls_Comparison.fn_create_comparison_interface(
                            categories, group, date_from, date_to, selected_duplicates
                        )

                int_countgroups += 1
                st.markdown("""<div style="border-top: 2px solid blue; margin-top: 20px; margin-bottom: 20px;"></div>""", unsafe_allow_html=True)
