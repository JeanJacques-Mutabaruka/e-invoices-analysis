"""
e-Invoices Analysis - Financial Data Processing & Analysis Platform
Main Controller - Application Entry Point
"""

import streamlit as st
from components.sidebar import render_sidebar
from components.header import render_header
from components.footer import render_footer
from utils.config import APP_CONFIG, setup_page_config

# Set page configuration (must be first Streamlit command)
setup_page_config()


def main():
    """Main application controller"""
    
    # Render header
    render_header()
    
    # Render sidebar navigation
    page = render_sidebar()
    
    # Initialize session state
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.file_metadata = {}
        st.session_state.file_processing_times = {}
        st.session_state.user_preferences = {
            'theme': 'light',
            'currency': 'RWF',
            'date_format': 'YYYY-MM-DD'
        }
    
    # Welcome message on first load
    if 'first_visit' not in st.session_state:
        st.session_state.first_visit = False
        st.balloons()
        st.success("🎉 Welcome to e-Invoices Analysis! Upload your financial data to get started.")
    
    # Page routing (handled by Streamlit's native multipage)
    # This controller just manages global state and common elements
    
    # Render footer
    render_footer()


if __name__ == "__main__":
    main()