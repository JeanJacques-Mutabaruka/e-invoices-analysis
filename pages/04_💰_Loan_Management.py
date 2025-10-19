"""
Loan Management Page - Wrapper for loan schedule model
"""

import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.loan_schedule import cls_Loan_schedule_display


def main():
    # Call the loan schedule display from models
    cls_Loan_schedule_display.fn_display_loanschedules()


if __name__ == "__main__":
    main()