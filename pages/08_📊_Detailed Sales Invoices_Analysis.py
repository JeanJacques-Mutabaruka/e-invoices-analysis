# pages/08-📊_Sales_Invoice_Analysis.py
import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from components.sales_invoice_analysis import cls_InvoiceSalesAnalysis

# Page configuration
st.set_page_config(
    page_title="Sales Invoices Analysis",
    page_icon="📊",
    layout="wide"
)

# Render the sales invoice analysis module
cls_InvoiceSalesAnalysis.fn_render()