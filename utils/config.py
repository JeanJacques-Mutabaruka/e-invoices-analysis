"""
Application Configuration
"""

import streamlit as st


# App metadata
APP_CONFIG = {
    'name': 'e-Invoices Analysis',
    'version': '1.0.0',
    'description': 'Comprehensive Financial Data Processing & Analysis Platform',
    'author': 'FINDAP Financial Solutions',
    'contact': 'support@findap.com'
}

# Streamlit page configuration
PAGE_CONFIG = {
    'page_title': 'e-Invoices Analysis Platform',
    'page_icon': '📊',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded',
    'menu_items': {
        'Get Help': 'mailto:support@findap.com',
        'Report a bug': 'mailto:support@findap.com',
        'About': f"""
        # {APP_CONFIG['name']}
        Version: {APP_CONFIG['version']}
        
        A comprehensive platform for processing and analyzing financial data including:
        - EBM/e-SDC invoices
        - Bank statements
        - VAT returns
        - Payroll data
        - Custom financial reports
        
        © 2025 {APP_CONFIG['author']}
        """
    }
}

# File paths configuration
PATHS = {
    'media_root': 'Findap_mediafiles',
    'sample_data': 'data/sample_data',
    'processed_data': 'data/processed',
    'aws_param_folder': 'FINDAP_FILES PARAMETERS/',
    'aws_param_filename': 'FINDAP_Filetypes_Parameters.xlsx'
}

# Supported file types
SUPPORTED_FILE_TYPES = {
    'excel': ['.xls', '.xlsx', '.xlsm', '.xlsb'],
    'csv': ['.csv'],
    'all': ['.xls', '.xlsx', '.xlsm', '.xlsb', '.csv']
}

# Data categories
DATA_CATEGORIES = {
    'SALES': {
        'color': '#28a745',
        'icon': '💰',
        'description': 'Sales transactions and invoices'
    },
    'PURCHASES': {
        'color': '#dc3545',
        'icon': '🛒',
        'description': 'Purchase transactions and expenses'
    },
    'BANK': {
        'color': '#007bff',
        'icon': '🏦',
        'description': 'Bank statements and transactions'
    },
    'VAT': {
        'color': '#ffc107',
        'icon': '📋',
        'description': 'VAT returns and tax data'
    },
    'PAYROLL': {
        'color': '#17a2b8',
        'icon': '👥',
        'description': 'Payroll and employee compensation'
    },
    'OTHER': {
        'color': '#6c757d',
        'icon': '📄',
        'description': 'Other financial data'
    }
}

# Number formatting
NUMBER_FORMAT = {
    'decimal_places': 2,
    'thousands_separator': ',',
    'currency_symbol': 'RWF',
    'negative_format': '({value})'  # Parentheses for negatives
}

# Date formatting
DATE_FORMAT = {
    'display': '%d-%b-%Y',
    'input': '%Y-%m-%d',
    'filename': '%Y%m%d_%H%M%S'
}

# Chart colors
CHART_COLORS = {
    'primary': '#667eea',
    'secondary': '#764ba2',
    'success': '#28a745',
    'danger': '#dc3545',
    'warning': '#ffc107',
    'info': '#17a2b8',
    'gradient': ['#667eea', '#764ba2', '#f093fb']
}

# Performance thresholds
PERFORMANCE_LIMITS = {
    'max_file_size_mb': 50,
    'max_records_per_file': 1000000,
    'max_files_per_upload': 10,
    'processing_timeout_seconds': 300
}


def setup_page_config():
    """Setup Streamlit page configuration"""
    st.set_page_config(**PAGE_CONFIG)


def get_category_style(category):
    """Get styling for a data category"""
    cat_info = DATA_CATEGORIES.get(category, DATA_CATEGORIES['OTHER'])
    return f"background-color: {cat_info['color']}; color: white; padding: 5px 10px; border-radius: 5px;"