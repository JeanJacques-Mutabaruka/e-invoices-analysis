# 📊 Electronic Invoices (e-invoices) Analysis Platform

**Comprehensive Financial Data Processing & Intelligence System**

Transform your financial data into actionable insights with automated processing, advanced analytics, and intelligent comparison tools.

---

## 🎯 Features

### 📤 **Data Upload & Processing**
- Multi-format support (Excel: .xls, .xlsx, .xlsb, .xlsm, CSV)
- Automatic file type detection (50+ predefined formats)
- Smart header recognition and standardization
- Real-time processing with progress tracking

### 🔍 **Advanced Analysis**
- Cross-dataset comparison and reconciliation
- Duplicate detection with configurable criteria
- Variance analysis across data sources
- Dynamic pivot tables with custom aggregations

### 💰 **Loan Management**
- Generate amortization schedules
- Support for multiple repayment methods
- Portfolio overview and analytics
- Outstanding balance calculations

### 📊 **Reports & Insights**
- Interactive dashboards
- Customizable data visualizations
- Export to Excel with formatting
- Historical trend analysis

---

## 🚀 Quick Start

### Prerequisites
```bash
Python 3.8+
pip (Python package manager)
```

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/JeanJacques-Mutabaruka/e-invoices-analysis.git
cd e-invoices-analysis
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure AWS credentials** (create `.streamlit/secrets.toml`)
```toml
AWS_STORAGE_BUCKET_NAME = "your-bucket-name"
AWS_ACCESS_KEY_ID = "your-access-key"
AWS_SECRET_ACCESS_KEY = "your-secret-key"
```

4. **Run the application**
```bash
streamlit run main.py
```

The app will open in your browser at `http://localhost:8501`

---

## 📁 Project Structure

```
e-invoices-analysis/
├── components/          # UI components and comparison tools
├── models/             # Business logic and financial models
├── services/           # Data processing services
├── utils/              # Core utilities and file handlers
├── pages/              # Streamlit pages
├── data/               # Sample data and processed files
├── Findap_mediafiles/  # Temporary files and AWS downloads
└── main.py  # Application entry point
```

---

## 📚 Supported Data Types

### ✅ Automatically Recognized:
- **EBM/e-SDC Invoices** (Sales & Purchases, V20/V21)
- **Bank Statements** (Multiple formats)
- **VAT Returns** (Etax formats)
- **Payroll Data** (Various layouts)
- **Trial Balances**
- **Custom Business Formats**

### 🔧 Processing Features:
- Date parsing (20+ international formats)
- Multilingual support (English, French, Spanish, Kinyarwanda)
- Automatic data type detection and conversion
- Illegal character cleaning for Excel compatibility

---

## 🎓 Usage Guide

### 1. Upload Data
Navigate to **📤 Upload Data** page and select your files. The system will:
- Automatically detect file types
- Extract and standardize data
- Show processing statistics

### 2. Analyze & Compare
Go to **🔍 Data Analysis** to:
- Compare datasets within the same financial group
- Apply date and duplicate filters
- Generate pivot tables
- Export results

### 3. Manage Loans
Use **💰 Loan Management** to:
- Create loan schedules
- Track multiple loans
- Calculate outstanding balances
- View portfolio characteristics

### 4. View Dashboard
The **📊 Dashboard** provides:
- Overview of loaded data
- Key metrics and statistics
- Recent activity
- Quick action buttons

---

## ⚙️ Configuration

### Number Formatting
```python
NUMBER_FORMAT = {
    'decimal_places': 2,
    'thousands_separator': ',',
    'currency_symbol': 'RWF'
}
```

### Date Formats
```python
DATE_FORMAT = {
    'display': '%d-%b-%Y',      # 01-Jan-2025
    'input': '%Y-%m-%d',        # 2025-01-01
    'filename': '%Y%m%d_%H%M%S' # 20250101_143045
}
```

---

## 🔒 Security & Privacy

- All processing done locally or in secure AWS S3
- No data transmitted to third parties
- Session-based data storage
- Configurable data retention policies

---

## 🤝 Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 📧 Support

- **Email**: support@findap.com
- **Documentation**: [Link to docs]
- **Issues**: [GitHub Issues](https://github.com/JeanJacques-Mutabaruka/e-invoices-analysis/issues)

---

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Data processing powered by [Pandas](https://pandas.pydata.org/)
- Cloud storage via [AWS S3](https://aws.amazon.com/s3/)

---

**Made with ❤️ by FINDAP Financial Solutions**

*Version 1.0.0 | © 2025*