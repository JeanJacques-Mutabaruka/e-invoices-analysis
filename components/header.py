"""
Header Component - Application Banner
"""

import streamlit as st
from datetime import datetime


def render_header():
    """Render the application header with branding and status"""
    
    # Main header with gradient background
    st.markdown("""
        <style>
            .main-header {
                background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
                padding: 15px;
                border-radius: 10px;
                text-align: center;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            .main-header h1 {
                color: white;
                margin: 0;
                font-size: 36px;
                font-weight: bold;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            }
            .main-header p {
                color: #f0f0f0;
                margin: 5px 0 0 0;
                font-size: 16px;
            }
            .status-bar {
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 15px;
                border-left: 4px solid #667eea;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Render header
    st.markdown("""
        <div class="main-header">
            <h1>📊 e-Invoices Analysis Platform</h1>
            <p>Comprehensive Financial Data Processing & Intelligence</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Status bar
    if 'file_metadata' in st.session_state and st.session_state.file_metadata:
        total_files = len(st.session_state.file_metadata)
        status_color = "#28a745" if total_files > 0 else "#ffc107"
        status_text = f"✅ {total_files} file(s) loaded" if total_files > 0 else "⚠️ No data loaded"
        
        st.markdown(f"""
            <div class="status-bar">
                <span style="color: {status_color}; font-weight: bold;">{status_text}</span>
                <span style="float: right; color: #6c757d;">
                    📅 {datetime.now().strftime("%d %B %Y")} | ⏰ {datetime.now().strftime("%H:%M")}
                </span>
            </div>
        """, unsafe_allow_html=True)