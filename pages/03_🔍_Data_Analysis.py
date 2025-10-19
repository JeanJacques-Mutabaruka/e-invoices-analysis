"""
Data Analysis Page - Wrapper for comparison component
"""

import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from components.comparison import cls_Comparison


def main():
    # Call the comparison component
    cls_Comparison.fn_compare_groups()


if __name__ == "__main__":
    main()