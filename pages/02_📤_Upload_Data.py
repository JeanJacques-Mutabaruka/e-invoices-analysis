"""
Data Upload Page - Wrapper for data processing service
"""

import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.data_processor import cls_ebm_etax_data_analysis


def main():
    # Call the data processing service
    cls_ebm_etax_data_analysis.fn_get_ebm_etax_dataanalyis()


if __name__ == "__main__":
    main()