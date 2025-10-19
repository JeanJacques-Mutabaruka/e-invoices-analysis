"""
Footer Component - Application Footer
"""

import streamlit as st
from datetime import datetime


def render_footer():
    """Render the application footer"""
    
    st.markdown("---")
    
    st.markdown("""
        <style>
            .footer {
                text-align: center;
                padding: 20px;
                background-color: #f8f9fa;
                border-radius: 10px;
                margin-top: 30px;
            }
            .footer p {
                margin: 5px 0;
                color: #6c757d;
            }
            .footer a {
                color: #667eea;
                text-decoration: none;
            }
            .footer a:hover {
                text-decoration: underline;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="footer">
            <p><strong>📊 e-Invoices Analysis Platform</strong></p>
            <p>Powered by AI & Advanced Analytics | Built with ❤️ using Streamlit</p>
            <p>© {datetime.now().year} FINDAP Financial Solutions | Version 1.0.0</p>
            <p>
                <a href="mailto:support@findap.com">📧 Support</a> | 
                <a href="#" target="_blank">📚 Documentation</a> | 
                <a href="#" target="_blank">🔐 Privacy Policy</a>
            </p>
        </div>
    """, unsafe_allow_html=True)