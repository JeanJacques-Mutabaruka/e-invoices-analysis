import numpy as np
import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
from io import BytesIO
from datetime import date,datetime, timedelta
from dateutil.relativedelta import relativedelta
# NEW:
from utils.file_handler import cls_Customfiles_Filetypehandler as filehandler

class cls_Loan_schedule:

    @staticmethod
    def fn_init():
        str_Pagetitle = "📈 LOAN MANAGEMENT"
        st.markdown(f"""
            <h1 style='text-align: center; font-weight: bold; font-family: Cambria; font-size: 40px; padding: 10px; background-color: rgb(220,240,210);color:rgb(0,0,105);
            border-radius: 15px; position: sticky;'>{str_Pagetitle}</h1>
        """, unsafe_allow_html=True)
    @staticmethod
    def fn_format_numbers(value):
        """Format numbers with commas and parentheses for negatives, and dates as 'dd-mmm-YYYY'."""
        if isinstance(value, (int, float)):
            return f"({abs(value):,.2f})" if value < 0 else f"{value:,.2f}"
        elif isinstance(value, (datetime, date, pd.Timestamp)):
            return value.strftime("%d-%b-%Y")
        return value

    @staticmethod
    def fn_generate_loan_schedule(amount, disbursement_date, start_date, end_date, interest_rate, frequency, periodicity, method):
        lst_repayment_dates = []
        lst_instalment = []
        lst_principals = []
        lst_interests = []
        lst_balances = []
        lst_period_amount = []
        
        # Year basis for interest calculation
        int_Yearbasisdays = 365

        # Generate repayment dates based on periodicity
        current_date = start_date
        while current_date < end_date:
            lst_repayment_dates.append(current_date)
            if periodicity == 'DAYS':
                current_date += timedelta(days=frequency)
            elif periodicity == 'WEEKS':
                current_date += timedelta(weeks=frequency)
            elif periodicity == 'MONTHS':
                current_date += relativedelta(months=frequency)

        total_periods = len(lst_repayment_dates)
        remaining_balance = amount

        # Compute periodic interest rate
        if periodicity == "DAYS":
            periodic_interest_rate = (interest_rate / 100)/int_Yearbasisdays
        elif periodicity == "WEEKS":
            periodic_interest_rate = (interest_rate / 100)/52
        elif periodicity == "MONTHS":
            periodic_interest_rate = (interest_rate / 100)/12
        else:
            raise ValueError("Unsupported periodicity")

        # Calculate fixed annuity payment if method is "CONSTANT INSTALMENT"
        if method == "CONSTANT INSTALMENT":
            if periodic_interest_rate > 0:
                payment = (amount * periodic_interest_rate) / (1 - (1 + periodic_interest_rate) ** -total_periods)
            else:
                payment = amount / total_periods

        # Iterating over repayment dates
        for i, current_date in enumerate(lst_repayment_dates):
            # Compute number of days in the period
            if i == 0:
                int_period_Nbofdays = (lst_repayment_dates[i] - disbursement_date).days
            else:
                int_period_Nbofdays = (lst_repayment_dates[i] - lst_repayment_dates[i - 1]).days

            # interest = (interest_rate / 100) * remaining_balance * (int_period_Nbofdays / int_Yearbasisdays)
            interest = periodic_interest_rate * remaining_balance 

            if method == "CONSTANT PRINCIPAL AMOUNT":
                principal = amount / total_periods
                payment = principal + interest
            elif method == "random_amount":
                payment = remaining_balance * 0.1  # Arbitrary example
                principal = payment - interest
            else:  # "CONSTANT INSTALMENT"
                principal = payment - interest

            remaining_balance = max(remaining_balance - principal, 0)

            # Append to lists
            lst_instalment.append(str(i + 1))
            lst_principals.append(principal)
            lst_interests.append(interest)
            lst_balances.append(remaining_balance)
            lst_period_amount.append(payment)

        # Create DataFrame
        df_schedule = pd.DataFrame({
            "Instalment": lst_instalment,
            "Instalment Date": lst_repayment_dates,
            "Instalment Amount": lst_period_amount,
            "Interest Amount": lst_interests,
            "Principal Amount": lst_principals,
            "Remaining Balance": lst_balances
        })

        return df_schedule

    @staticmethod
    def fn_get_cutoff_balance(loan_schedule, dte_date):
        """Returns the outstanding balance at the closest instalment date ≤ dte_date."""
        loan_schedule = loan_schedule.copy()  # Prevent modifying original DataFrame
        loan_schedule["Instalment Date"] = pd.to_datetime(loan_schedule["Instalment Date"]).dt.date  

        # Ensure dte_date is within the range
        if dte_date < loan_schedule["Instalment Date"].min() or dte_date > loan_schedule["Instalment Date"].max():
            return 0
        return loan_schedule[loan_schedule["Instalment Date"] <= dte_date].iloc[-1]["Remaining Balance"]

    @staticmethod
    def fn_update_loan_enddate():
        start_date = st.session_state.loan_repayment_start_date
        end_date = st.session_state.loan_repayment_end_date
        freq = st.session_state.loan_repayment_frequency
        periodicity = st.session_state.loan_repayment_periodicity
        nb_instalments = st.session_state.int_number_instalments

        # Update End Date based on instalments
        if st.session_state.changed_field in ["int_number_instalments", "loan_repayment_periodicity", "loan_repayment_start_date"]:
            if periodicity == "DAYS":
                st.session_state.loan_repayment_end_date = start_date + timedelta(days=int(nb_instalments * freq))
            elif periodicity == "WEEKS":
                st.session_state.loan_repayment_end_date = start_date + timedelta(weeks=int(nb_instalments * freq))
            elif periodicity == "MONTHS":
                st.session_state.loan_repayment_end_date = start_date + relativedelta(months=int(nb_instalments * freq))

        # Update Number of Instalments based on end date
        elif st.session_state.changed_field == "loan_repayment_end_date":
            delta_days = (end_date - start_date).days
            if periodicity == "DAYS":
                st.session_state.int_number_instalments = delta_days // freq
            elif periodicity == "WEEKS":
                st.session_state.int_number_instalments = delta_days // (freq * 7)
            elif periodicity == "MONTHS":
                delta_months = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month
                st.session_state.int_number_instalments = delta_months // freq



class cls_Loan_schedule_display:
    def fn_display_loanschedules():
        # Initialize session state for loan schedules
        if "loan_schedules" not in st.session_state:
            st.session_state.loan_schedules = {}

        cls_Loan_schedule.fn_init()

        # Layout: Organizing input fields into 3 columns
        col1, col2, col3 = st.columns([2, 3, 3])  # Ratios determine the relative column widths

        with col1:
            loan_id = st.text_input("Loan ID")
            loan_description = st.text_area("Loan Description")

        with col2:
            st.markdown("""
                <style>
                    /* This targets ALL visible input fields, including date inputs */
                    input {
                        text-align: center !important;
                        background-color: #E6F0E6 !important;
                        font-size: 20px !important;
                        color: rgb(0,0,250) !important;
                        height: 2.05em !important;
                        border-radius: 5px !important;
                        padding: 0px;
                    }

                </style>
            """, unsafe_allow_html=True)

            loan_amount = st.number_input("Loan Amount", min_value=0.0,format="%0.2f",)
            col21,col22 = col2.columns([1, 1])
            with col21:
                loan_disbursement_date = st.date_input("Loan Disbursement Date", format='YYYY-MM-DD', key="loan_disbursement_date")
                
                loan_repayment_start_date = st.date_input(
                    "Loan Repayment Start Date", min_value=loan_disbursement_date, format='YYYY-MM-DD', key="loan_repayment_start_date",
                    on_change=lambda: st.session_state.update({"changed_field": "loan_repayment_start_date"}) or cls_Loan_schedule.fn_update_loan_enddate()
                )

            with col22:
                int_number_instalments = st.number_input(
                    "Number of instalments", min_value=1, key="int_number_instalments",
                    on_change=lambda: st.session_state.update({"changed_field": "int_number_instalments"}) or cls_Loan_schedule.fn_update_loan_enddate()
                )

                loan_repayment_end_date = st.date_input(
                    "Loan Repayment End Date", min_value=loan_disbursement_date, format='YYYY-MM-DD', key="loan_repayment_end_date",
                    on_change=lambda: st.session_state.update({"changed_field": "loan_repayment_end_date"}) or cls_Loan_schedule.fn_update_loan_enddate()
                )
        with col3:
            col_interestrate, col_repaymethod = st.columns([1,2])
            with col_interestrate:
                loan_interest_rate = st.number_input("Annual Interest Rate (%)", min_value=0.0)
            with col_repaymethod:
                loan_repayment_method = st.selectbox("Loan Repayment Method", ["CONSTANT INSTALMENT", "CONSTANT PRINCIPAL AMOUNT",])
            
            st.markdown(f"""
                <div style='text-align: center; padding: 3px; background-color: rgb(240, 240, 240);color:rgb(0,0,250); font-size: 20px;
                border-radius: 5px; display: flex; justify-content: center;'>FREQUENCY</div>
            """, unsafe_allow_html=True)
            col_frequency, col_period = st.columns([1,1])
            with col_frequency:
                loan_repayment_frequency = st.number_input(
                    "Frequency", min_value=1, key="loan_repayment_frequency", label_visibility="collapsed",
                    on_change=lambda: st.session_state.update({"changed_field": "loan_repayment_periodicity"}) or cls_Loan_schedule.fn_update_loan_enddate()
                )

            with col_period:
                loan_repayment_periodicity = st.selectbox(
                    "Periodicity", ["DAYS", "WEEKS", "MONTHS"], key="loan_repayment_periodicity", label_visibility="collapsed",
                    on_change=lambda: st.session_state.update({"changed_field": "loan_repayment_periodicity"}) or cls_Loan_schedule.fn_update_loan_enddate()
                )

        # Generate Loan Schedule and Add to Session State
        if st.button("ADD NEW LOAN",use_container_width=True):
            if loan_id and loan_amount > 0:
                # periodicity = timedelta(days=loan_repayment_periodicity)
                loan_schedule = cls_Loan_schedule.fn_generate_loan_schedule(
                    loan_amount,
                    datetime.strptime(str(loan_disbursement_date), "%Y-%m-%d"),
                    datetime.strptime(str(loan_repayment_start_date), "%Y-%m-%d"),
                    datetime.strptime(str(loan_repayment_end_date), "%Y-%m-%d"),
                    loan_interest_rate, loan_repayment_frequency, loan_repayment_periodicity,
                    loan_repayment_method
                )
                st.session_state.loan_schedules[loan_id] = {
                    "description": loan_description,
                    "interest_rate": loan_interest_rate,
                    "loan_amount": loan_amount,
                    "disbursement_date": datetime.strptime(str(loan_disbursement_date), "%Y-%m-%d"),
                    "repayment_start_date": datetime.strptime(str(loan_repayment_start_date), "%Y-%m-%d"),
                    "repayment_end_date": datetime.strptime(str(loan_repayment_end_date), "%Y-%m-%d"),
                    "periodicity": loan_repayment_periodicity,
                    "frequency": loan_repayment_frequency,
                    "method": loan_repayment_method,
                    "schedule": loan_schedule
                }
                st.success(f"Loan schedule for '{loan_id}' has been added!")
            else:
                st.warning("Please ensure Loan ID and Loan Amount are provided.")
        
        st.markdown("""<div style="border-top: 1px solid blue; margin-top: 1px; margin-bottom: 1px;"></div>""", unsafe_allow_html=True,)
        st.markdown("""<div style="border-top: 1px solid blue; margin-top: 1px; margin-bottom: 1px;"></div>""", unsafe_allow_html=True,)
        # Display all loans in a table format
        if st.session_state.loan_schedules:
            st.write("### Loans list:")
            # Prepare data for display
            loans_data = []
            for loan_id, loan_info in st.session_state.loan_schedules.items():
                loan_schedule = loan_info['schedule']
                loans_data.append({
                    "Loan ID": loan_id,
                    "Description": loan_info["description"],
                    "Loan Amount": loan_info.get("loan_amount"),
                    "Disbursement Date": loan_info.get("disbursement_date").date() if loan_info.get("disbursement_date") != None else None,
                    "Repayment Start Date": loan_info.get("repayment_start_date").date() if loan_info.get("disbursement_date") != None else None,
                    "Repayment End Date": loan_info.get("repayment_end_date").date() if loan_info.get("disbursement_date") != None else None,
                    "Interest Rate": str(loan_info.get("interest_rate"))+'%',
                    "Repayment Periodicity": str(loan_info.get("frequency") )+ ' ' +loan_info.get("periodicity"),
                    "Repayment Method": loan_info.get("method"),
                })
            
            # Convert to DataFrame for display
            loans_df = pd.DataFrame(loans_data)

            tbl_loans_list = f"{loans_df.style.hide(axis='index').format(cls_Loan_schedule.fn_format_numbers).to_html()}"
            st.markdown(f"""
                <div style='text-align: center; padding: 3px; background-color: rgb(250, 250, 250);color:rgb(0,0,100);
                border-radius: 5px; display: flex; justify-content: center;'>{tbl_loans_list}</div>
            """, unsafe_allow_html=True)
                                    
        st.markdown("""<div style="border-top: 1px dotted blue; margin-top: 1px; margin-bottom: 1px;"></div>""", unsafe_allow_html=True,)
        # Display Loans' portfolio characteristics & Schedules
        if st.session_state.loan_schedules:
            str_title_ptf_schedule =f"LOANS PORTFOLIO CHARACTERISTICS & SCHEDULES"
            st.markdown(
                f"""<h2 style='background-color: rgb(220,240,210); font-weight: bold; color: blue; padding: 5px; border-radius: 5px;
                font-family: Cambria; text-align: center;'>{str_title_ptf_schedule}</h2>""",
                unsafe_allow_html=True)
            selected_loans = st.multiselect("", st.session_state.loan_schedules.keys(),max_selections=10)
            if selected_loans:
                with st.expander(f"🎯 CLICK HERE TO SEE DETAILS.....") :
                    col_cutoff_title, col_cutoff_date,col_empty = st.columns([6,2,2])
                    with col_cutoff_date:
                        dte_Cutoffdate = st.date_input("Date", format='YYYY-MM-DD', label_visibility="collapsed", key=f"dte_outstanding_{loan_id}")
                    with col_cutoff_title:
                        str_title_cutoff_ptf = f"CHARACTERISTICS of LOANS PORTFOLIO as of:"
                        st.markdown(
                            f"""<h5 style='background-color: rgb(220,240,210); font-weight: bold; color: blue; padding: 5px; border-radius: 5px;
                            font-family: Cambria; text-align: center;'>🎯 {str_title_cutoff_ptf} {cls_Loan_schedule.fn_format_numbers(dte_Cutoffdate)}</h5>""",
                            unsafe_allow_html=True)

                    # Initialize Cutoff Portfolio DataFrame
                    df_Cutoff_portfolio = pd.DataFrame(columns=[
                        "LOAN ID", "FROM", "TO", "NB of instalments",
                        "Total Instalments Amount", "Total Interests Amount", "Total Principal Amount", "Outstanding Balance"
                    ])

                    # Iterate over selected loans
                    for loan_id in selected_loans:
                        loan_data = st.session_state.loan_schedules[loan_id]
                        loan_data["schedule"]["Instalment Date"] = pd.to_datetime(loan_data["schedule"]["Instalment Date"])  # Ensure proper datetime format

                        obj_wholeschedule = loan_data["schedule"].copy()
                        obj_wholeschedule["Instalment Date"] = obj_wholeschedule["Instalment Date"].dt.date  # Convert to date format

                        # Filter schedule up to dte_Cutoffdate
                        df_filtered = obj_wholeschedule[obj_wholeschedule["Instalment Date"] <= dte_Cutoffdate]

                        if df_filtered.empty:
                            continue  # Skip if no instalments found

                        # Extract required values
                        min_date = df_filtered["Instalment Date"].min()
                        max_date = df_filtered["Instalment Date"].max()
                        num_instalments = len(df_filtered)
                        total_instalments_amount = df_filtered["Instalment Amount"].sum()
                        total_interest_amount = df_filtered["Interest Amount"].sum()
                        total_principal_amount = df_filtered["Principal Amount"].sum()
                        outstanding_balance = cls_Loan_schedule.fn_get_cutoff_balance(obj_wholeschedule, dte_Cutoffdate)

                        # Append results to df_Cutoff_portfolio
                        df_Cutoff_portfolio = pd.concat([df_Cutoff_portfolio, pd.DataFrame([{
                            "LOAN ID": loan_id,
                            "FROM": min_date,
                            "TO": max_date,
                            "NB of instalments": num_instalments,
                            "Total Instalments Amount": total_instalments_amount,
                            "Total Interests Amount": total_interest_amount,
                            "Total Principal Amount": total_principal_amount,
                            "Outstanding Balance": outstanding_balance
                        }])], ignore_index=True)

                    # st.dataframe(df_Cutoff_portfolio)
                    tbl_Cutoff_portfolio = f"{df_Cutoff_portfolio.style.hide(axis='index').format(cls_Loan_schedule.fn_format_numbers).to_html()}"
                    st.markdown(f"""
                        <div style='text-align: center; padding: 3px; background-color: rgb(242, 242, 242);color:rgb(0,0,250);
                        border-radius: 5px; display: flex; justify-content: center;'>{tbl_Cutoff_portfolio}</div>
                    """, unsafe_allow_html=True)
                    
                    st.markdown("""<div style="border-top: 1px solid blue; margin-top: 1px; margin-bottom: 1px;"></div>""", unsafe_allow_html=True,)
                    st.markdown("""<div style="border-top: 1px solid blue; margin-top: 1px; margin-bottom: 1px;"></div>""", unsafe_allow_html=True,)

                    str_title_loans_schedules = f"LOANS PORTFOLIO SCHEDULES BETWEEN :"
                    st.markdown(
                        f"""<h4 style='background-color: rgb(220,240,210); font-weight: bold; color: blue; padding: 5px; border-radius: 5px;
                        font-family: Cambria; text-align: center;'>{str_title_loans_schedules}</h4>""",
                        unsafe_allow_html=True)

                    col_01, col_02, col_03, col_04 = st.columns([2, 1, 1,2]) 
                    with col_02:
                        date_filter_start = st.date_input("Schedule START DATE",format="YYYY-MM-DD",)
                    with col_03:
                        date_filter_end = st.date_input("Schedule END DATE",format="YYYY-MM-DD",)

                    int_loan_count=1
                    for loan_id in selected_loans:
                        loan_data = st.session_state.loan_schedules[loan_id]
                        loan_data["schedule"]["Instalment Date"] = pd.to_datetime(loan_data["schedule"]["Instalment Date"])

                        filtered_schedule = loan_data["schedule"][
                            (loan_data["schedule"]["Instalment Date"] >= pd.Timestamp(date_filter_start)) &
                            (loan_data["schedule"]["Instalment Date"] <= pd.Timestamp(date_filter_end))
                        ]
                        str_title_loan_schedule = f"Loan Schedule for '{loan_id}': {loan_data['description']}"
                        st.markdown(f"""
                            <h5><div style='padding: 3px; background-color: rgb(165, 165, 165);color:rgb(0,0,0);
                            border-radius: 5px; display: flex; '>🎯{int_loan_count:02} - {str_title_loan_schedule}</div></h5>
                        """, unsafe_allow_html=True)

                        obj_loanschedule = f"{filtered_schedule.style.hide(axis='index').format(cls_Loan_schedule.fn_format_numbers).to_html()}"
                        st.markdown(f"""
                            <div style='text-align: center; padding: 3px; background-color: rgb(242, 242, 242);color:rgb(0,0,250);
                            border-radius: 5px; display: flex; justify-content: center;'>{obj_loanschedule}</div>
                        """, unsafe_allow_html=True)
                        int_loan_count +=1
                        st.markdown("""<div style="border-top: 1px solid green; margin-top: 1px; margin-bottom: 1px;"></div>""", unsafe_allow_html=True,)
                                        
