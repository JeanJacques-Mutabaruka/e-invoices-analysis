"""
Sidebar Navigation Component
"""

import streamlit as st
from datetime import datetime


def render_sidebar():
    """Render the application sidebar with navigation and quick stats"""
    
    with st.sidebar:
        # Logo and title
        st.markdown("""
            <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            border-radius: 10px; margin-bottom: 20px;'>
                <h1 style='color: white; font-size: 28px; margin: 0;'>📊</h1>
                <h2 style='color: white; font-size: 20px; margin: 5px 0;'>e-Invoices</h2>
                <p style='color: #e0e0e0; font-size: 14px; margin: 0;'>Financial Analysis Platform</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Navigation info
        st.markdown("### 🧭 Navigation")
        st.info("👈 Use the sidebar to navigate between pages")
        
        st.markdown("---")
        
        # Quick stats
        st.markdown("### 📈 Quick Stats")
        
        if 'file_metadata' in st.session_state and st.session_state.file_metadata:
            total_files = len(st.session_state.file_metadata)
            total_records = sum(
                len(values[5]) 
                for file_data in st.session_state.file_metadata.values() 
                for values in file_data.values()
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Files Loaded", total_files)
            with col2:
                st.metric("Total Records", f"{total_records:,}")
            
            # Categories breakdown
            categories = set()
            for file_data in st.session_state.file_metadata.values():
                for values in file_data.values():
                    categories.add(values[0])
            
            st.metric("Data Categories", len(categories))
        else:
            st.warning("No data loaded yet")
            st.info("👆 Upload files from the **Upload Data** page")
        
        st.markdown("---")
        
        # User info
        st.markdown("### 👤 User Info")
        st.text(f"Session: {st.session_state.get('session_id', 'N/A')[:8]}...")
        st.text(f"Time: {datetime.now().strftime('%H:%M:%S')}")
        
        st.markdown("---")
        
        # Help section
        with st.expander("❓ Quick Help"):
            st.markdown("""
            **Getting Started:**
            1. 📤 Upload your financial files
            2. 🔍 Analyze and compare data
            3. 📊 View insights and reports
            4. 💰 Manage loan schedules
            
            **Supported Files:**
            - EBM Sales/Purchases
            - Bank Statements
            - VAT Returns (Etax)
            - Payroll Data
            - Custom Excel formats
            """)
        
        # Theme toggle (future feature)
        # st.markdown("---")
        # theme = st.toggle("🌙 Dark Mode", value=False)
        
        return None  # Page routing handled by Streamlit multipage