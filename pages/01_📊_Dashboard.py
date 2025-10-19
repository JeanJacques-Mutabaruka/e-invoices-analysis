"""
Main Dashboard - Overview of loaded data and key metrics
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.config import APP_CONFIG, DATA_CATEGORIES


def main():
    st.title("📊 Dashboard - Financial Data Overview")
    
    # Check if data is loaded
    if 'file_metadata' not in st.session_state or not st.session_state.file_metadata:
        st.warning("⚠️ No data loaded yet. Please upload your financial files first.")
        st.info("👉 Go to the **📤 Upload Data** page to get started.")
        
        # Show sample capabilities
        st.markdown("### 🎯 What You Can Do:")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **📤 Upload & Process**
            - Multi-format support (Excel, CSV)
            - Automatic categorization
            - 150+ data formats recognized
            """)
        
        with col2:
            st.markdown("""
            **🔍 Analyze & Compare**
            - Cross-dataset comparison
            - Duplicate detection
            - Variance analysis
            """)
        
        with col3:
            st.markdown("""
            **📊 Reports & Insights**
            - Dynamic pivot tables
            - Export to Excel
            - Visual dashboards
            """)
        
        return
    
    # Data is loaded - show dashboard
    st.success("✅ Data loaded successfully!")
    
    # Aggregate statistics
    total_files = len(st.session_state.file_metadata)
    total_sheets = sum(len(sheets) for sheets in st.session_state.file_metadata.values())
    
    all_dataframes = []
    category_counts = {}
    
    for file_data in st.session_state.file_metadata.values():
        for sheet_data in file_data.values():
            category = sheet_data[0]
            df = sheet_data[5]
            
            all_dataframes.append(df)
            category_counts[category] = category_counts.get(category, 0) + len(df)
    
    total_records = sum(len(df) for df in all_dataframes)
    
    # Key metrics
    st.markdown("### 📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Files", total_files, help="Number of uploaded files")
    
    with col2:
        st.metric("Total Worksheets", total_sheets, help="Number of processed worksheets")
    
    with col3:
        st.metric("Total Records", f"{total_records:,}", help="Total number of data records")
    
    with col4:
        st.metric("Categories", len(category_counts), help="Unique data categories")
    
    st.markdown("---")
    
    # Date range
    st.markdown("### 📅 Data Coverage")
    
    date_ranges = []
    for df in all_dataframes:
        if 'TRANSACTION DATE' in df.columns:
            df['TRANSACTION DATE'] = pd.to_datetime(df['TRANSACTION DATE'], errors='coerce')
            valid_dates = df['TRANSACTION DATE'].dropna()
            if not valid_dates.empty:
                date_ranges.append((valid_dates.min(), valid_dates.max()))
    
    if date_ranges:
        overall_min = min(d[0] for d in date_ranges)
        overall_max = max(d[1] for d in date_ranges)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Earliest Date", overall_min.strftime("%d-%b-%Y"))
        with col2:
            st.metric("Latest Date", overall_max.strftime("%d-%b-%Y"))
        with col3:
            days_span = (overall_max - overall_min).days
            st.metric("Date Span", f"{days_span} days")
    
    st.markdown("---")
    
    # Category breakdown
    st.markdown("### 📂 Data by Category")
    
    if category_counts:
        # Create DataFrame for display
        df_categories = pd.DataFrame([
            {
                'Category': cat,
                'Records': count,
                'Percentage': f"{(count/total_records)*100:.1f}%"
            }
            for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        ])
        
        # Display as colored cards
        cols = st.columns(min(3, len(category_counts)))
        for idx, (cat, count) in enumerate(sorted(category_counts.items(), key=lambda x: x[1], reverse=True)):
            with cols[idx % 3]:
                cat_info = DATA_CATEGORIES.get(
                    cat if cat in DATA_CATEGORIES else 'OTHER',
                    DATA_CATEGORIES['OTHER']
                )
                
                st.markdown(f"""
                    <div style='background-color: {cat_info['color']}; color: white; padding: 20px; 
                    border-radius: 10px; text-align: center; margin-bottom: 10px;'>
                        <h1 style='margin: 0; font-size: 36px;'>{cat_info['icon']}</h1>
                        <h3 style='margin: 10px 0;'>{cat}</h3>
                        <p style='font-size: 24px; margin: 0;'>{count:,}</p>
                        <p style='margin: 5px 0; opacity: 0.9;'>records</p>
                    </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Recent activity
    st.markdown("### 🕒 Recent Activity")
    
    if 'file_processing_times' in st.session_state:
        recent_files = []
        for filename, processing_time in st.session_state.file_processing_times.items():
            if isinstance(filename, str):  # Skip datetime entries
                recent_files.append({
                    'File': filename,
                    'Processing Time': f"{processing_time:.2f}s" if isinstance(processing_time, (int, float)) else str(processing_time)
                })
        
        if recent_files:
            df_recent = pd.DataFrame(recent_files[-5:])  # Last 5 files
            st.dataframe(df_recent, use_container_width=True, hide_index=True)
    
    # Quick actions
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Upload More Data", use_container_width=True):
            st.switch_page("pages/02_📤_Upload_Data.py")
    
    with col2:
        if st.button("🔍 Analyze Data", use_container_width=True):
            st.switch_page("pages/03_🔍_Data_Analysis.py")
    
    with col3:
        if st.button("📈 View Reports", use_container_width=True):
            st.switch_page("pages/05_📈_Reports.py")


if __name__ == "__main__":
    main()