# pages/05_📈_Reports.py - OPTION 1 VERSION
"""
Reports Page - OPTION 1: Retrieves stored dataframes from analysis results
Cleaner and more efficient - no need to re-run duplicate detection
"""

import streamlit as st
import pandas as pd
import sys
import os
from datetime import datetime
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.global_analysis_orchestrator import GlobalAnalysisOrchestrator
from services.ai_report_generator import AIReportGenerator


def format_number(value):
    """Format numbers with commas"""
    if isinstance(value, (int, float)):
        if pd.isna(value):
            return "-"
        if value < 0:
            return f'({abs(value):,.0f})'
        return f"{value:,.0f}"
    return value


def format_year(value):
    """Format YEAR as text (yyyy)"""
    if pd.isna(value):
        return "-"
    return str(int(value))


def display_file_summary_table():
    """Display uploaded files in a professional table"""
    
    st.markdown("""
        <div style='background-color: rgb(240,255,240); padding: 10px; border-radius: 8px; 
        border-left: 5px solid rgb(76,175,80); margin: 10px 0; text-align: center;'>
        <h4 style='margin: 0; color: rgb(0,0,105);'>📊 Summary of Uploaded Data</h4>
        </div>
    """, unsafe_allow_html=True)
    
    file_info = []
    
    for file_name, sheets in st.session_state.file_metadata.items():
        for sheet_name, sheet_data in sheets.items():
            category = sheet_data[0]
            df = sheet_data[5]
            
            min_date = "N/A"
            max_date = "N/A"
            if 'TRANSACTION DATE' in df.columns:
                dates = df['TRANSACTION DATE'].dropna()
                if len(dates) > 0:
                    min_date = dates.min().strftime('%Y-%m-%d %H:%M:%S')
                    max_date = dates.max().strftime('%Y-%m-%d %H:%M:%S')
            
            group = "N/A"
            if 'FINANCIAL STATEMENT GROUP' in df.columns:
                groups = df['FINANCIAL STATEMENT GROUP'].unique()
                if len(groups) > 0:
                    group = groups[0]
            
            file_info.append({
                'File Name': file_name,
                'Worksheet': sheet_name,
                'Group': group,
                'Category': category,
                'MIN Date': min_date,
                'MAX Date': max_date,
                'Nb Records': len(df)
            })
    
    df_summary = pd.DataFrame(file_info)
    
    if 'Group' in df_summary.columns and df_summary['Group'].notna().any():
        df_summary = df_summary.sort_values(['Group', 'Category', 'File Name'])
    else:
        df_summary = df_summary.sort_values(['Category', 'File Name'])
    
    st.dataframe(
        df_summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            'File Name': st.column_config.TextColumn('File Name', width='medium'),
            'Worksheet': st.column_config.TextColumn('Worksheet', width='small'),
            'Group': st.column_config.TextColumn('Group', width='medium'),
            'Category': st.column_config.TextColumn('Category', width='medium'),
            'MIN Date': st.column_config.TextColumn('MIN Date', width='medium'),
            'MAX Date': st.column_config.TextColumn('MAX Date', width='medium'),
            'Nb Records': st.column_config.NumberColumn('Nb Records', format='%d')
        }
    )


def aggregate_dataframe_by_year(df: pd.DataFrame, exclude_patterns: list) -> pd.DataFrame:
    """Aggregate dataframe by year"""
    from utils.file_handler import get_numeric_columns, get_date_range
    
    if 'YEAR' not in df.columns or df.empty:
        return pd.DataFrame()
    
    numeric_cols = get_numeric_columns(df, exclude_patterns)
    
    if not numeric_cols:
        return pd.DataFrame()
    
    try:
        yearly_data = df.groupby('YEAR')[numeric_cols].sum().reset_index()
        yearly_data = yearly_data.sort_values('YEAR')
        
        date_ranges = []
        for year in yearly_data['YEAR']:
            year_df = df[df['YEAR'] == year]
            start, end = get_date_range(year_df)
            date_ranges.append(f"{start} to {end}")
        
        yearly_data['Date Range'] = date_ranges
        
        cols = ['YEAR', 'Date Range'] + numeric_cols
        yearly_data = yearly_data[cols]
        
        return yearly_data
    except Exception as e:
        print(f"Error aggregating: {e}")
        return pd.DataFrame()


def display_category_analysis(category: str, analysis: dict, group_name: str, 
                              original_df: pd.DataFrame, exclude_patterns: list):
    """Display analysis with separate aggregations for clean and duplicate data"""
    
    # 🆕 OPTION 1: DataFrame already has "Duplicate Status" column!
    print(f"\n🔍 OPTION 1 - Retrieved dataframe for {category}:")
    print(f"   Columns: {original_df.columns.tolist()}")
    print(f"   Has 'Duplicate Status': {'Duplicate Status' in original_df.columns}")
    if 'Duplicate Status' in original_df.columns:
        print(f"   Value counts: {original_df['Duplicate Status'].value_counts().to_dict()}")
    
    # Category title
    st.markdown(f"""
        <div style='background-color: rgb(240,248,255); padding: 8px; border-radius: 5px; 
        border-left: 4px solid rgb(100,149,237); margin: 10px 0;'>
        <b>📊 {category}</b>
        </div>
    """, unsafe_allow_html=True)
    
    # Basic stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
            <div style='background-color: #e3f2fd; padding: 8px; border-radius: 5px; text-align: center;'>
                <div style='font-size: 12px; color: #666;'>Total Records</div>
                <div style='font-size: 18px; font-weight: bold; color: #1976d2;'>{analysis['total_records']:,}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        date_range = analysis['date_range']
        st.markdown(f"""
            <div style='background-color: #f5f5f5; padding: 8px; border-radius: 5px; text-align: center;'>
                <div style='font-size: 12px; color: #666;'>Date Range</div>
                <div style='font-size: 14px; font-weight: bold; color: #333;'>{date_range['from']}</div>
                <div style='font-size: 14px; font-weight: bold; color: #333;'>to {date_range['to']}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        dup_summary = analysis['duplicate_summary']
        if dup_summary['status'] == 'checked':
            total_dups = dup_summary['is_duplicate']
            color = '#f44336' if total_dups > 0 else '#4caf50'
            st.markdown(f"""
                <div style='background-color: #fff3e0; padding: 8px; border-radius: 5px; text-align: center;'>
                    <div style='font-size: 12px; color: #666;'>Duplicates Found</div>
                    <div style='font-size: 18px; font-weight: bold; color: {color};'>{total_dups:,}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div style='background-color: #fafafa; padding: 8px; border-radius: 5px; text-align: center;'>
                    <div style='font-size: 12px; color: #666;'>Duplicates</div>
                    <div style='font-size: 14px; font-weight: bold; color: #999;'>Not checked</div>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown("""<div style="border-top: 1px dashed #ccc; margin: 10px 0;"></div>""", unsafe_allow_html=True)
    
    # Duplicate Status Breakdown
    if dup_summary['status'] == 'checked':
        st.markdown("""
            <div style='background-color: rgb(255,250,240); padding: 8px; border-radius: 5px; 
            border-left: 4px solid rgb(255,165,0); margin: 10px 0;'>
            <b>🔍 Duplicate Status Breakdown</b>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            clean_total = dup_summary['no_duplicates'] + dup_summary['has_duplicates']
            st.markdown(f"""
                <div style='background-color: #e8f5e9; padding: 8px; border-radius: 5px; text-align: center;'>
                    <div style='font-size: 11px; color: #666;'>Clean Records</div>
                    <div style='font-size: 10px; color: #888;'>(NO + HAS duplicates)</div>
                    <div style='font-size: 16px; font-weight: bold; color: #2e7d32;'>{clean_total:,}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div style='background-color: #ffebee; padding: 8px; border-radius: 5px; text-align: center;'>
                    <div style='font-size: 11px; color: #666;'>IS DUPLICATE</div>
                    <div style='font-size: 10px; color: #888;'>(Records to exclude)</div>
                    <div style='font-size: 16px; font-weight: bold; color: #c62828;'>{dup_summary['is_duplicate']:,}</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col3:
            dup_pct = (dup_summary['is_duplicate'] / analysis['total_records'] * 100) if analysis['total_records'] > 0 else 0
            st.markdown(f"""
                <div style='background-color: #f3e5f5; padding: 8px; border-radius: 5px; text-align: center;'>
                    <div style='font-size: 11px; color: #666;'>Duplicate Rate</div>
                    <div style='font-size: 10px; color: #888;'>(IS DUPLICATE %)</div>
                    <div style='font-size: 16px; font-weight: bold; color: #6a1b9a;'>{dup_pct:.2f}%</div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("""<div style="border-top: 1px dashed #ccc; margin: 10px 0;"></div>""", unsafe_allow_html=True)
        
        # SEPARATE AGGREGATIONS
        if dup_summary['is_duplicate'] > 0:
            # Find Duplicate Status column
            dup_col = None
            for col in original_df.columns:
                if col.upper().strip() == 'DUPLICATE STATUS':
                    dup_col = col
                    break
            
            if dup_col:
                print(f"   ✅ Duplicate column found: '{dup_col}'")
                
                # Split dataframes
                clean_mask = original_df[dup_col].str.upper().isin(['NO DUPLICATES', 'HAS DUPLICATES'])
                duplicate_mask = original_df[dup_col].str.upper() == 'IS DUPLICATE'
                
                df_clean = original_df[clean_mask].copy()
                df_duplicates = original_df[duplicate_mask].copy()
                
                print(f"   ✅ Split successful:")
                print(f"      Clean records: {len(df_clean)}")
                print(f"      Duplicate records: {len(df_duplicates)}")
                
                # === CLEAN DATA ANALYSIS ===
                st.markdown("""
                    <div style='background-color: rgb(240,255,240); padding: 8px; border-radius: 5px; 
                    border-left: 4px solid rgb(76,175,80); margin: 10px 0;'>
                    <b>✅ Clean Records Analysis (NO + HAS Duplicates)</b>
                    </div>
                """, unsafe_allow_html=True)
                
                yearly_clean = aggregate_dataframe_by_year(df_clean, exclude_patterns)
                
                if not yearly_clean.empty:
                    df_display = yearly_clean.copy()
                    if 'YEAR' in df_display.columns:
                        df_display['YEAR'] = df_display['YEAR'].apply(format_year)
                    
                    for col in df_display.columns:
                        if col not in ['YEAR', 'Date Range']:
                            df_display[col] = df_display[col].apply(format_number)
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                else:
                    st.info("No clean data to aggregate")
                
                st.markdown("""<div style="border-top: 1px dashed #ccc; margin: 10px 0;"></div>""", unsafe_allow_html=True)
                
                # === DUPLICATE DATA ANALYSIS ===
                with st.expander(f"🔴 IS DUPLICATE Records Analysis ({len(df_duplicates):,} records)", expanded=False):
                    st.markdown("""
                        <div style='background-color: #ffebee; padding: 12px; border-radius: 5px; 
                        border-left: 4px solid #c62828; margin: 10px 0;'>
                        <b>⚠️ These are duplicate records that should be excluded from main totals</b>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    yearly_duplicates = aggregate_dataframe_by_year(df_duplicates, exclude_patterns)
                    
                    if not yearly_duplicates.empty:
                        df_dup_display = yearly_duplicates.copy()
                        if 'YEAR' in df_dup_display.columns:
                            df_dup_display['YEAR'] = df_dup_display['YEAR'].apply(format_year)
                        
                        for col in df_dup_display.columns:
                            if col not in ['YEAR', 'Date Range']:
                                df_dup_display[col] = df_dup_display[col].apply(format_number)
                        
                        st.dataframe(df_dup_display, use_container_width=True, hide_index=True)
                    else:
                        st.info("No duplicate data to aggregate")
            else:
                st.error("❌ Duplicate Status column not found in stored dataframe!")
        else:
            # No duplicates
            st.markdown("""
                <div style='background-color: rgb(240,255,240); padding: 8px; border-radius: 5px; 
                border-left: 4px solid rgb(76,175,80); margin: 10px 0;'>
                <b>📅 Summary by Year (All Records - No Duplicates)</b>
                </div>
            """, unsafe_allow_html=True)
            
            if analysis['yearly_summary'] is not None and not analysis['yearly_summary'].empty:
                df_display = analysis['yearly_summary'].copy()
                
                if 'YEAR' in df_display.columns:
                    df_display['YEAR'] = df_display['YEAR'].apply(format_year)
                
                for col in df_display.columns:
                    if col not in ['YEAR', 'Date Range']:
                        df_display[col] = df_display[col].apply(format_number)
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        # Duplicates not checked
        if analysis['yearly_summary'] is not None and not analysis['yearly_summary'].empty:
            st.markdown("""
                <div style='background-color: rgb(240,255,240); padding: 8px; border-radius: 5px; 
                border-left: 4px solid rgb(76,175,80); margin: 10px 0;'>
                <b>📅 Summary by Year</b>
                </div>
            """, unsafe_allow_html=True)
            
            df_display = analysis['yearly_summary'].copy()
            
            if 'YEAR' in df_display.columns:
                df_display['YEAR'] = df_display['YEAR'].apply(format_year)
            
            for col in df_display.columns:
                if col not in ['YEAR', 'Date Range']:
                    df_display[col] = df_display[col].apply(format_number)
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    st.markdown("""<div style="border-top: 1px dashed #ccc; margin: 10px 0;"></div>""", unsafe_allow_html=True)
    
    # 🆕 ENHANCED Top Analysis with proper naming
    if 'top_analysis' in analysis and analysis['top_analysis']:
        if 'top_analysis_table' in analysis['top_analysis']:
            # 🆕 Get the analysis title (Top Clients, Top Suppliers, or Top Partners)
            analysis_title = analysis['top_analysis'].get('analysis_title', 'Top Partners')
            
            st.markdown(f"""
                <div style='background-color: rgb(255,248,240); padding: 8px; border-radius: 5px; 
                border-left: 4px solid rgb(255,152,0); margin: 10px 0;'>
                <b>🎯 {analysis_title} Analysis (Clean Records Only)</b>
                </div>
            """, unsafe_allow_html=True)
            
            df_top = analysis['top_analysis']['top_analysis_table'].copy()
            
            if 'YEAR' in df_top.columns:
                df_top['YEAR'] = df_top['YEAR'].apply(format_year)
            
            df_top['Total Amount'] = df_top['Total Amount'].apply(format_number)
            
            st.dataframe(df_top, use_container_width=True, hide_index=True)
    
    st.markdown("""<div style="border-top: 1px solid blue; margin: 10px: 10px; margin-bottom: 10px;"></div>""", unsafe_allow_html=True)

def enhance_ai_report_formatting(report_text: str) -> str:
    """
    🆕 ENHANCED: Enhance AI report with color highlighting for:
    - Duplicate-related content (red)
    - CRITICAL priority recommendations (red)
    - HIGH priority recommendations (light red/pink)
    - Bold text (blue)
    """
    
    enhanced = report_text
    
    # ========================================
    # 1. HIGHLIGHT DUPLICATES (RED)
    # ========================================
    
    # Pattern 1: "X duplicates" or "X Duplicates" where X is not 0
    def highlight_duplicates_count(match):
        number = match.group(1).replace(',', '')
        text = match.group(0)
        
        # Skip if number is 0
        if number == '0':
            return text
        
        # Highlight in red
        return f"<span style='color: red; font-weight: bold; background-color: #ffebee; padding: 2px 4px; border-radius: 3px;'>{text}</span>"
    
    # Match patterns like: "123 duplicates", "1,234 Duplicates", "456 duplicate records"
    enhanced = re.sub(
        r'(\d{1,3}(?:,\d{3})*)\s+duplicates?(?:\s+records?)?',
        highlight_duplicates_count,
        enhanced,
        flags=re.IGNORECASE
    )
    
    # Pattern 2: "Duplicate Rate: X%" or "Duplicate Percentage: X%" where X > 0
    def highlight_duplicate_rate(match):
        prefix = match.group(1)
        rate = match.group(2)
        
        try:
            rate_value = float(rate)
            if rate_value == 0:
                return match.group(0)
        except:
            pass
        
        return f"<span style='color: red; font-weight: bold; background-color: #ffebee; padding: 2px 4px; border-radius: 3px;'>{prefix}{rate}%</span>"
    
    enhanced = re.sub(
        r'(Duplicate\s+(?:Rate|Percentage|%)[:\s]*)([\d.]+)%',
        highlight_duplicate_rate,
        enhanced,
        flags=re.IGNORECASE
    )
    
    # Pattern 3: "IS DUPLICATE: X" where X is not 0
    def highlight_is_duplicate(match):
        prefix = match.group(1)
        number = match.group(2).replace(',', '')
        full_text = match.group(0)
        
        if number == '0':
            return full_text
        
        return f"<span style='color: red; font-weight: bold; background-color: #ffebee; padding: 2px 4px; border-radius: 3px;'>{full_text}</span>"
    
    enhanced = re.sub(
        r'(IS\s+DUPLICATE[:\s]*)(\d{1,3}(?:,\d{3})*)',
        highlight_is_duplicate,
        enhanced,
        flags=re.IGNORECASE
    )
    
    # Pattern 4: Highlight rows in tables with non-zero duplicates
    # Match table rows with duplicate data
    def highlight_table_row_with_duplicates(match):
        row = match.group(0)
        
        # Check if row contains non-zero duplicate numbers
        # Pattern: look for numbers followed by words like "duplicate", "duplicates"
        if re.search(r'[1-9]\d*(?:,\d{3})*\s*\|.*?duplicate', row, re.IGNORECASE):
            # Don't double-highlight already highlighted spans
            if '<span style=' in row:
                return row
            return f"<span style='background-color: #ffebee;'>{row}</span>"
        
        return row
    
    # Apply to table rows (lines starting with |)
    lines = enhanced.split('\n')
    highlighted_lines = []
    for line in lines:
        if line.strip().startswith('|') and '|' in line[1:]:
            # Check if line has duplicate-related non-zero values
            if re.search(r'\|\s*[1-9]\d*(?:,\d{3})*\s*\|', line) and 'duplicate' in line.lower():
                # Add background color to the entire row
                if '<span style=' not in line:
                    line = f"<span style='background-color: #ffebee;'>{line}</span>"
        highlighted_lines.append(line)
    
    enhanced = '\n'.join(highlighted_lines)
    
    # ========================================
    # 2. HIGHLIGHT CRITICAL PRIORITY (RED)
    # ========================================
    
    # Pattern: Lines or sections with "CRITICAL" priority
    def highlight_critical_priority(match):
        text = match.group(0)
        
        # Don't double-highlight
        if '<span style=' in text:
            return text
        
        return f"<span style='color: red; font-weight: bold; background-color: #ffcdd2; padding: 2px 6px; border-radius: 3px; border-left: 3px solid red;'>{text}</span>"
    
    # Match CRITICAL in various contexts
    enhanced = re.sub(
        r'(?:Priority[:\s]*)?CRITICAL(?:\s*Priority)?(?:[:\s]*[^\n]*)?',
        highlight_critical_priority,
        enhanced,
        flags=re.IGNORECASE
    )
    
    # Highlight table rows with CRITICAL
    lines = enhanced.split('\n')
    highlighted_lines = []
    for line in lines:
        if 'CRITICAL' in line.upper() and line.strip().startswith('|'):
            if '<span style=' not in line:
                line = f"<span style='background-color: #ffcdd2; font-weight: bold;'>{line}</span>"
        highlighted_lines.append(line)
    
    enhanced = '\n'.join(highlighted_lines)
    
    # ========================================
    # 3. HIGHLIGHT HIGH PRIORITY (LIGHT RED/PINK)
    # ========================================
    
    def highlight_high_priority(match):
        text = match.group(0)
        
        # Don't double-highlight (skip if already highlighted as CRITICAL)
        if '<span style=' in text:
            return text
        
        # Don't highlight if it's "HIGH" in other contexts (like "HIGH quality")
        if 'priority' not in text.lower():
            return text
        
        return f"<span style='color: #d32f2f; font-weight: bold; background-color: #ffe0e0; padding: 2px 6px; border-radius: 3px; border-left: 3px solid #ff8a80;'>{text}</span>"
    
    # Match HIGH priority in various contexts
    enhanced = re.sub(
        r'(?:Priority[:\s]*)?HIGH(?:\s*Priority)?(?:[:\s]*[^\n]*)?',
        highlight_high_priority,
        enhanced,
        flags=re.IGNORECASE
    )
    
    # Highlight table rows with HIGH priority
    lines = enhanced.split('\n')
    highlighted_lines = []
    for line in lines:
        if 'HIGH' in line.upper() and 'priority' in line.lower() and line.strip().startswith('|'):
            if '<span style=' not in line or 'CRITICAL' not in line.upper():
                if '<span style=' not in line:
                    line = f"<span style='background-color: #ffe0e0; font-weight: bold;'>{line}</span>"
        highlighted_lines.append(line)
    
    enhanced = '\n'.join(highlighted_lines)
    
    # ========================================
    # 4. HIGHLIGHT BOLD TEXT (BLUE) - Original functionality
    # ========================================
    
    def replace_bold(match):
        text = match.group(1)
        
        # Don't re-highlight already colored text
        if '<span style=' in text:
            return f"**{text}**"
        
        return f"<span style='color: rgb(0,0,255); font-weight: bold;'>{text}</span>"
    
    enhanced = re.sub(r'\*\*([^*]+)\*\*', replace_bold, enhanced)
    
    return enhanced


def main():
    str_Pagetitle = "📈 FINANCIAL ANALYSIS REPORTS"
    st.markdown(f"""
        <h1 style='text-align: center; font-weight: bold; font-family: Cambria; font-size: 40px; padding: 10px; background-color: rgb(220,240,210);color:rgb(0,0,105);
        border-radius: 15px; position: sticky;'>{str_Pagetitle}</h1>
    """, unsafe_allow_html=True)
    
    st.markdown("""
        <style>
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
            .stTabs [data-baseweb="tab-list"] {
                gap: 10px;
            }
            .stTabs [data-baseweb="tab"] {
                background-color: rgb(240,240,240);
                border-radius: 8px;
                padding: 12px 24px;
                font-weight: bold;
                font-size: 16px;
                color: rgb(0,0,100);
            }
            .stTabs [aria-selected="true"] {
                background-color: rgb(220,240,210);
                color: rgb(0,0,150);
            }
            .stTabs .stTabs [data-baseweb="tab"] {
                background-color: rgb(250,250,250);
                padding: 8px 16px;
                font-size: 14px;
                color: rgb(0,0,120);
                border-radius: 5px;
            }
            .stTabs .stTabs [aria-selected="true"] {
                background-color: rgb(200,220,240);
                color: rgb(0,0,150);
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""<div style="border-top: 1px solid blue; margin-top: 1px; margin-bottom: 1px;"></div>""", unsafe_allow_html=True)
    st.markdown("""<div style="border-top: 1px solid blue; margin-top: 1px; margin-bottom: 1px;"></div>""", unsafe_allow_html=True)
    
    if 'file_metadata' not in st.session_state or not st.session_state.file_metadata:
        st.warning("⚠️ No data uploaded yet.")
        st.info("👉 Go to the **📤 Upload Data** page.")
        
        col1, col2, col3 = st.columns(3)
        with col2:
            if st.button("📤 Go to Upload Page", use_container_width=True):
                st.switch_page("pages/02_📤_Upload_Data.py")
        
        return
    
    st.success("✅ Data loaded successfully!")
    
    with st.expander("📋 Summary of Uploaded Data", expanded=False):
        display_file_summary_table()
    
    st.markdown("""<div style="border-top: 1px solid blue; margin-top: 10px; margin-bottom: 10px;"></div>""", unsafe_allow_html=True)
    
    st.markdown("""
        <h3 style='text-align: center; font-weight: bold; font-family: Cambria; font-size: 25px; padding: 5px; 
        background-color: rgb(220,240,210);color:rgb(0,0,100); border-radius: 5px;'>🚀 GLOBAL FINANCIAL ANALYSIS</h3>
    """, unsafe_allow_html=True)
    
    st.markdown("Generate comprehensive analysis organized by groups and categories.")
    
    col1, col2, col3 = st.columns(3)
    
    with col2:
        analysis_depth = st.radio(
            "**Select Analysis Depth:**",
            [
                "Quick (key high level)",
                "Standard (all enabled rules)",
                "Comprehensive (detailed breakdowns)"
            ],
            horizontal=False
        )
    
    depth_map = {
        "Quick (key high level)": "quick",
        "Standard (all enabled rules)": "standard",
        "Comprehensive (detailed breakdowns)": "comprehensive"
    }
    selected_depth = depth_map[analysis_depth]
    
    run_analysis = st.button("GET GLOBAL ANALYSIS", key="btn_global_analysis")
    
    if run_analysis:
        st.markdown("""<div style="border-top: 1px solid blue; margin-top: 1px; margin-bottom: 1px;"></div>""", unsafe_allow_html=True)
        
        orchestrator = GlobalAnalysisOrchestrator(st.session_state.file_metadata)
        st.markdown("### 🔄 Analysis in Progress...")
        
        results = orchestrator.run_analysis(selected_depth)
        
        st.session_state.global_analysis_results = results
        st.session_state.analysis_timestamp = datetime.now()
        
        st.markdown("""<div style="border-top: 1px solid blue; margin-top: 1px; margin-bottom: 1px;"></div>""", unsafe_allow_html=True)
        
        if not orchestrator.has_errors():
            st.success("✅ Analysis completed successfully!")
            
            stats = orchestrator.get_summary_statistics()
            
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.markdown(f"""<div style='background-color: #e3f2fd; padding: 8px; border-radius: 5px; text-align: center;'>
                    <div style='font-size: 12px; color: #666;'>Files</div>
                    <div style='font-size: 20px; font-weight: bold; color: #1976d2;'>{stats['total_files']}</div>
                </div>""", unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""<div style='background-color: #e8f5e9; padding: 8px; border-radius: 5px; text-align: center;'>
                    <div style='font-size: 12px; color: #666;'>Categories</div>
                    <div style='font-size: 20px; font-weight: bold; color: #388e3c;'>{stats['total_categories']}</div>
                </div>""", unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""<div style='background-color: #fff3e0; padding: 8px; border-radius: 5px; text-align: center;'>
                    <div style='font-size: 12px; color: #666;'>Records</div>
                    <div style='font-size: 20px; font-weight: bold; color: #f57c00;'>{stats['total_records']:,}</div>
                </div>""", unsafe_allow_html=True)
            
            with col4:
                dup_color = '#f44336' if stats['total_duplicates'] > 0 else '#4caf50'
                st.markdown(f"""<div style='background-color: #fce4ec; padding: 8px; border-radius: 5px; text-align: center;'>
                    <div style='font-size: 12px; color: #666;'>Duplicates</div>
                    <div style='font-size: 20px; font-weight: bold; color: {dup_color};'>{stats['total_duplicates']:,}</div>
                </div>""", unsafe_allow_html=True)
            
            with col5:
                st.markdown(f"""<div style='background-color: #f3e5f5; padding: 8px; border-radius: 5px; text-align: center;'>
                    <div style='font-size: 12px; color: #666;'>Duration</div>
                    <div style='font-size: 16px; font-weight: bold; color: #7b1fa2;'>{stats['analysis_duration']}</div>
                </div>""", unsafe_allow_html=True)
            
            st.balloons()
            st.rerun()
        else:
            st.error("⚠️ Analysis completed with errors")
            for error in orchestrator.get_errors():
                st.error(error)
    
    if 'global_analysis_results' in st.session_state:
        st.markdown("""<div style="border-top: 1px solid blue; margin-top: 10px; margin-bottom: 10px;"></div>""", unsafe_allow_html=True)
        
        results = st.session_state.global_analysis_results
        
        if 'analysis_timestamp' in st.session_state:
            st.caption(f"📅 Analysis generated: {st.session_state.analysis_timestamp.strftime('%d-%b-%Y %H:%M:%S')}")
        
        quick_summary = results.get('quick_summary', {})
        group_summaries = quick_summary.get('group_summaries', {})
        
        # 🆕 OPTION 1: Get stored dataframes with duplicate columns
        processed_dataframes = quick_summary.get('processed_dataframes', {})
        
        print(f"\n🔍 OPTION 1 - Retrieved {len(processed_dataframes)} processed dataframes")
        print(f"   Keys: {list(processed_dataframes.keys())}")
        
        if group_summaries and len(group_summaries) > 0:
            from utils.file_handler import ComparisonRulesManager
            _, exclude_patterns = ComparisonRulesManager.get_numeric_field_config()
            
            group_names = list(group_summaries.keys())
            tab_labels_level1 = [
                f"📁 {group} ({len(group_summaries[group]['category_analyses'])} categories)" 
                for group in group_names
            ]
            tab_labels_level1.append("🤖 AI REPORTS")
            
            tabs_level1 = st.tabs(tab_labels_level1)
            
            for tab_idx, group_name in enumerate(group_names):
                with tabs_level1[tab_idx]:
                    group_analysis = group_summaries[group_name]
                    
                    st.markdown(f"""
                        <div style='background-color: rgb(220,240,210); padding: 10px; border-radius: 8px; 
                        border-left: 5px solid rgb(100,149,237); margin: 10px 0;'>
                        <h3 style='margin: 0; color: rgb(0,0,105);'>📁 {group_name}</h3>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    group_stats = group_analysis['group_statistics']
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Categories", group_stats['total_categories'])
                    with col2:
                        st.metric("Total Records", f"{group_stats['total_records']:,}")
                    with col3:
                        date_range = group_stats['date_range']
                        st.write(f"**Date Range:**")
                        st.write(f"{date_range['from']} to {date_range['to']}")
                    
                    st.markdown("""<div style="border-top: 1px solid blue; margin-top: 10px; margin-bottom: 10px;"></div>""", unsafe_allow_html=True)
                    
                    category_analyses = group_analysis['category_analyses']
                    category_names = list(category_analyses.keys())
                    
                    tab_labels_level2 = [f"📊 {cat}" for cat in category_names]
                    tabs_level2 = st.tabs(tab_labels_level2)
                    
                    for cat_idx, category in enumerate(category_names):
                        with tabs_level2[cat_idx]:
                            analysis = category_analyses[category]
                            
                            # 🆕 OPTION 1: Retrieve stored dataframe
                            key = f"{group_name}_{category}"
                            original_df = processed_dataframes.get(key, pd.DataFrame())
                            
                            if original_df.empty:
                                st.error(f"❌ No stored dataframe found for key: {key}")
                                print(f"   ❌ Missing key: {key}")
                                print(f"   Available keys: {list(processed_dataframes.keys())}")
                            else:
                                print(f"   ✅ Found dataframe for key: {key}")
                                display_category_analysis(
                                    category, 
                                    analysis, 
                                    group_name, 
                                    original_df,
                                    exclude_patterns
                                )
            
            # AI REPORTS TAB
            with tabs_level1[-1]:
                st.markdown("""
                    <div style='background-color: rgb(240,248,255); padding: 10px; border-radius: 8px; 
                    border-left: 5px solid rgb(100,149,237); margin: 10px 0;'>
                    <h3 style='margin: 0; color: rgb(0,0,105);'>🤖 AI-POWERED INSIGHTS</h3>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("Generate intelligent analysis reports powered by AI.")
                st.markdown("""<div style="border-top: 1px dashed #ccc; margin: 10px 0;"></div>""", unsafe_allow_html=True)
                
                report_type = st.radio(
                    "**Select Report Type:**",
                    options=['short', 'medium', 'detailed'],
                    format_func=lambda x: {
                        'short': '📄 Short Report',
                        'medium': '📊 Medium Report',
                        'detailed': '📚 Detailed Report'
                    }[x],
                    horizontal=True
                )
                
                generate_report = st.button(f"Generate {report_type.title()} AI Report", key="btn_ai_report")
                
                if generate_report:
                    if "google" not in st.secrets or "GEMINI_API_KEY" not in st.secrets["google"]:
                        st.error("❌ Gemini API key not found.")
                    else:
                        api_key = st.secrets["google"]["GEMINI_API_KEY"]
                        
                        with st.spinner(f"🤖 Generating {report_type} AI report..."):
                            try:
                                generator = AIReportGenerator(api_key)
                                report = generator.generate_report(results, level=report_type)
                                
                                st.session_state[f'ai_report_{report_type}'] = report
                                st.success(f"✅ {report_type.title()} report generated!")
                                
                                st.markdown("""<div style="border-top: 1px solid blue; margin-top: 10px; margin-bottom: 10px;"></div>""", unsafe_allow_html=True)
                                enhanced_report = enhance_ai_report_formatting(report)
                                st.markdown(enhanced_report, unsafe_allow_html=True)
                                st.markdown("""<div style="border-top: 1px solid blue; margin-top: 10px; margin-bottom: 10px;"></div>""", unsafe_allow_html=True)
                                
                                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                st.download_button(
                                    label="📥 Download Report",
                                    data=report,
                                    file_name=f"findap_report_{report_type}_{timestamp}.md",
                                    mime="text/markdown",
                                    use_container_width=True
                                )
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                
                st.markdown("""<div style="border-top: 1px solid blue; margin-top: 20px; margin-bottom: 10px;"></div>""", unsafe_allow_html=True)
                st.markdown("### 📚 Previously Generated Reports")
                
                has_previous = False
                for r_type in ['short', 'medium', 'detailed']:
                    if f'ai_report_{r_type}' in st.session_state:
                        has_previous = True
                        with st.expander(f"📄 {r_type.title()} Report", expanded=False):
                            enhanced_report = enhance_ai_report_formatting(st.session_state[f'ai_report_{r_type}'])
                            st.markdown(enhanced_report, unsafe_allow_html=True)
                
                if not has_previous:
                    st.info("No reports generated yet.")
        else:
            st.warning("No analysis results available.")


if __name__ == "__main__":
    main()
