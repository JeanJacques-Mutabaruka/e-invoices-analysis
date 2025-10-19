"""
Settings Page - User preferences and app configuration
"""

import streamlit as st
import sys
sys.path.append('..')
from utils.config import APP_CONFIG, NUMBER_FORMAT, DATE_FORMAT


def main():
    st.title("⚙️ Settings & Preferences")
    
    st.markdown("""
    Configure your application preferences and settings.
    """)
    
    # User