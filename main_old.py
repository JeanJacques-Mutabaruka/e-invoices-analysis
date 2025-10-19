import streamlit as st
import findap_streamlit.Loan_schedule
import findap_streamlit.ebm_etax_data_analysis
import findap_streamlit.home
import findap_streamlit.comparison
import findap_streamlit.agri_financial_model  # NEW MODULE

# Set the page config
st.set_page_config(page_title="FINANCIAL MODELLING", layout="wide", page_icon=":material/thumb_up:")

# Initialize session state for menu navigation
if "obj_menu_findata" not in st.session_state:
    st.session_state.obj_menu_findata = "AGRIBUSINESS FINANCIAL MODEL"

# Custom CSS for styling the sidebar and radio buttons
st.sidebar.markdown("""
    <style>
        .menu-title {
            font-size: 20px; 
            font-weight: bold; 
            color: rgb(0,0,255); 
            padding: 8px 0px;
            font-family: Cambria;
            display: flex;
            justify-content: flex-end;
        }
        
        .sidebar {
            background-color: #2c3e50; 
            padding: 10px;
            border-radius: 10px;
        }

        .stRadio > div {
            padding: 1px;
            border-radius: 8px;
            margin-top: 10px;
            margin-bottom: 10px;
        }
        
        .stRadio div[role="radiogroup"] label {
            font-size: 20px;
            font-family: Cambria;
            color: white !important;
            padding: 5px 10px;
            margin: 10px 0;
            border-radius: 5px;
        }

        .stRadio div[role="radiogroup"] label[data-baseweb="radio"] {
            background-color: RGB(190,190,190);
            padding: 8px;
            border-radius: 5px;
        }
    </style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("<div class='menu-title'>AGRIBUSINESS FINANCIAL MODELLING</div>", unsafe_allow_html=True)
    
    obj_menu_findata = st.radio(
        "",  
        [
            "AGRIBUSINESS FINANCIAL MODEL"  # NEW OPTION
            # "LOAD FINANCIAL DATA", 
            # "COMPARISON & ANALYSIS",  
            # "LOANS MANAGEMENT",
        ],
        key='obj_menu_findata'
    )

if obj_menu_findata == "AGRIBUSINESS FINANCIAL MODEL":
    findap_streamlit.agri_financial_model.cls_AgriFinancialModel.fn_render_main()  # NEW ENTRY POINT
# elif obj_menu_findata == "LOAD FINANCIAL DATA":
#     findap_streamlit.ebm_etax_data_analysis.cls_ebm_etax_data_analysis.fn_get_ebm_etax_dataanalyis()
# elif obj_menu_findata == "COMPARISON & ANALYSIS":
#     findap_streamlit.comparison.cls_Comparison.fn_compare_groups()
# elif obj_menu_findata == "LOANS MANAGEMENT":
#     findap_streamlit.Loan_schedule.cls_Loan_schedule_display.fn_display_loanschedules()
# elif obj_menu_findata == "Home":
#     findap_streamlit.home.app()