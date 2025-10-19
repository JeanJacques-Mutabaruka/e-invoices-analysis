import streamlit as st
import pandas as pd
import sys
import os, io
import openpyxl
import xlrd
import tempfile
import time  # Import the time module
import traceback  # For detailed error logging
from datetime import datetime
from pivottablejs import pivot_ui
import streamlit.components.v1 as components
from st_aggrid import AgGrid, GridOptionsBuilder
import numpy as np

import logging

# NEW:
from utils.file_handler import cls_Customfiles_Filetypehandler as filehandler


lst_Dashboard_columns = ["File Name", "Worksheet", "Category", "MIN Date", "MAX Date", "Nb Records", "File Size", "Processing Time","Upload Status"]
class cls_ebm_etax_data_analysis:
    @staticmethod
    def fn_reload_metadata():
        """Displays stored metadata before processing new uploads."""
        
        if "file_metadata" in st.session_state and st.session_state.file_metadata:
            st.markdown("""<div style='background-color: rgb(220,240,210); text-align: center; font-weight: bold; 
                color: blue; padding: 5px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                font-size: 24px; font-family: Cambria; margin-bottom: 10px;'> Summary of uploaded data</div>""",
                        unsafe_allow_html=True)

            existing_files = list(st.session_state.file_metadata.keys())

            df_existing_metadata = []
            for file_name in existing_files:
                for sheet_name, lst_values in st.session_state.file_metadata[file_name].items():
                    category, df_mycleaneddf = lst_values[0], lst_values[5]

                    if not 'TRANSACTION DATE' in df_mycleaneddf.columns:
                        df_mycleaneddf['TRANSACTION DATE'] = datetime(1900, 1, 1)
                    df_mycleaneddf['TRANSACTION DATE'] = pd.to_datetime(df_mycleaneddf['TRANSACTION DATE'], errors='coerce')
                    df_mycleaneddf = df_mycleaneddf.dropna(subset=['TRANSACTION DATE'])
                    dte_Mindate, dte_Maxdate = df_mycleaneddf['TRANSACTION DATE'].min(), df_mycleaneddf['TRANSACTION DATE'].max()

                    file_processing_time = st.session_state.file_processing_times[file_name]
                    str_processing_time = time.strftime("%M:%S", time.gmtime(file_processing_time)) + f".{int((file_processing_time % 1) * 1000):03d}"
                    str_filesize=""
                    df_existing_metadata.append([file_name, sheet_name, category, dte_Mindate, dte_Maxdate, 
                        len(df_mycleaneddf),str_filesize,str_processing_time,'Existing'])

            if df_existing_metadata:
                # df_existing = pd.DataFrame(df_existing_metadata, columns=["File Name", "Worksheet", "Category", "MIN Date", "MAX Date", "Nb Records","",""])
                df_existing = pd.DataFrame(df_existing_metadata, columns=lst_Dashboard_columns)
                st.dataframe(df_existing, height=500,use_container_width=True,hide_index=True)
            else:
                st.info("No previously uploaded data found !")
        else:
            st.info("No previously uploaded data found !")

    @staticmethod
    def fn_get_ebm_etax_dataanalyis():
        """Main function to handle file uploads, metadata extraction, and dashboard display."""

        statement_title = "FINANCIAL DATA ANALYSIS"
        st.markdown(f"""
            <h1 style='text-align: center; font-weight: bold; font-family: Cambria; font-size: 50px; padding: 8px;
            border-radius: 5px; position: sticky;'>{statement_title}</h1>
        """, unsafe_allow_html=True)

        # st.text_area("", "This page allows you to analyze uploaded financial data...")

        # Initialize session state for confirmation
        if "confirm_clear" not in st.session_state:
            st.session_state.confirm_clear = False

        # Add CSS for button and table styling
        st.markdown("""
            <style>
                /* Button Styling */
                div[data-testid="stButton"] > button {
                    background-color: rgb(220,240,210);
                    font-weight: bold;
                    color: red;
                    padding: 10px;
                    border-radius: 5px;
                    font-family: Cambria;
                    display: flex;
                    justify-content: flex-end;
                }
                div[data-testid="stButton"] > button:hover {
                    background-color: rgb(200,230,190);
                }
            
            </style>
        """, unsafe_allow_html=True)        # # Align button to the right

        obj_btnclearmemory = st.button("CLEAR MEMORY", key="clear_memory", )
        if obj_btnclearmemory:
            st.session_state.confirm_clear = True

        # Handle the confirmation step
        if st.session_state.confirm_clear:
            confirm = st.radio("Are you sure you want to clear the memory?", ["No", "Yes"],index=None,horizontal=True, key="confirmation_radio")
            if confirm == "Yes":
                st.session_state.confirm_clear = False
                st.success("Memory cleared successfully!")
                st.session_state.file_metadata = {}  # Reset stored data
                st.session_state.file_processing_times = {}
                # st.info("🛑 Existing data in memory has been deleted. Only new uploaded files will be processed.")
            elif confirm == "No":
                st.session_state.confirm_clear = False
                st.info("Memory clearing canceled.")


        st.markdown("""<div style='background-color: rgb(220,240,210); text-align: center; font-weight: bold; 
            color: blue; padding: 5px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            font-size: 24px; font-family: Cambria; margin-bottom: 10px;'>UPLOAD FINANCIAL DATA TO BE ANALYSED</div>""",
                    unsafe_allow_html=True)

        with st.expander("UPLOAD FILES FOR ANALYSIS", expanded=True):
            st.markdown("""<div style="border-top: 1px solid blue; margin-top: 1px; margin-bottom: 1px;"></div>""", unsafe_allow_html=True,)
            uploaded_files = st.file_uploader("", type=["xls", "xlsx", "xlsb", "xlsm"], accept_multiple_files=True)
            st.markdown("""<div style="border-top: 1px solid blue; margin-top: 1px; margin-bottom: 1px;"></div>""", unsafe_allow_html=True,)
            
            dict_file_data, dict_file_names = {}, {}
            if uploaded_files:
                start_time = time.time()

                # Initialize session state
                if "file_metadata" not in st.session_state:
                    st.session_state.file_metadata = {}
                if "file_processing_times" not in st.session_state:
                    st.session_state.file_processing_times = {}

                dte_Process_start_time = datetime.now()
                st.session_state.file_processing_times[dte_Process_start_time] = dte_Process_start_time
                for i, file in enumerate(uploaded_files, start=1):
                    # Process only if the file is new
                    if file.name not in st.session_state.file_metadata:
                        file_start_time = time.time()

                        dic_myfile_metadata_and_stdzed_dfs = cls_ebm_etax_data_analysis.fn_get_metadata_and_stdzed_dfs(file)
                        st.session_state.file_metadata[file.name] = dic_myfile_metadata_and_stdzed_dfs

                        file_end_time = time.time()
                        st.session_state.file_processing_times[file.name] = file_end_time - file_start_time

                    # Retrieve stored metadata
                    dic_myfile_metadata_and_stdzed_dfs = st.session_state.file_metadata[file.name]
                    file_processing_time = st.session_state.file_processing_times[file.name]

                    str_processing_time = time.strftime("%M:%S", time.gmtime(file_processing_time)) + \
                                          f".{int((file_processing_time % 1) * 1000):03d}"

                    dict_file_data, dict_file_names = cls_ebm_etax_data_analysis.fn_get_metadata_from_files(
                        i, file, dic_myfile_metadata_and_stdzed_dfs, str_processing_time, dict_file_data, dict_file_names
                    )
                dte_Process_end_time = datetime.now()
                st.session_state.file_processing_times[dte_Process_end_time] = dte_Process_end_time
                st.markdown("""<div style="border-top: 1px solid blue; margin-top: 1px; margin-bottom: 1px;"></div>""", unsafe_allow_html=True,)
                cls_ebm_etax_data_analysis.fn_display_metadata_dashboard(dict_file_data, dict_file_names, lst_Dashboard_columns, dte_Process_start_time,dte_Process_end_time)
                st.markdown("""<div style="border-top: 1px solid blue; margin-top: 1px; margin-bottom: 1px;"></div>""", unsafe_allow_html=True,)
            # Display existing metadata in memory before new uploads
            cls_ebm_etax_data_analysis.fn_reload_metadata()
            st.markdown("""<div style="border-top: 1px solid blue; margin-top: 1px; margin-bottom: 1px;"></div>""", unsafe_allow_html=True,)

        #cls_aggregator.fn_combine()

    @staticmethod
    def fn_get_metadata_from_files(i, file, dic_myfile_metadata_and_stdzed_dfs, str_processing_time, dict_file_data, dict_file_names):
        """Extracts metadata from uploaded files and stores them in a dictionary."""
        file_size = round(len(file.getvalue()) / 1024, 2)
        int_countsheets = 1

        for sheet_name, lst_values in dic_myfile_metadata_and_stdzed_dfs.items():
            category, df_mycleaneddf = lst_values[0], lst_values[5]

            if not 'TRANSACTION DATE' in df_mycleaneddf.columns:
                df_mycleaneddf['TRANSACTION DATE'] = datetime(1900, 1, 1)
            df_mycleaneddf['TRANSACTION DATE'] = pd.to_datetime(df_mycleaneddf['TRANSACTION DATE'], errors='coerce')
            df_mycleaneddf['ORIGIN_FILE'] = file.name
            df_mycleaneddf = df_mycleaneddf.dropna(subset=['TRANSACTION DATE'])
            dte_Mindate, dte_Maxdate = df_mycleaneddf['TRANSACTION DATE'].min(), df_mycleaneddf['TRANSACTION DATE'].max()

            dict_key = f"{file.name}--{sheet_name}"
            if dict_key not in dict_file_data:
                dict_file_data[dict_key] = [
                    # i, f'{i:02d}.{int_countsheets:02d}--{file.name}', sheet_name, category,
                    f'{i:02d}.{int_countsheets:02d}--{file.name}', sheet_name, category,
                    dte_Mindate, dte_Maxdate, len(df_mycleaneddf), f"{file_size} KB", str_processing_time,'New Upload'
                ]
                dict_file_names[f'{i:02d}.{int_countsheets:02d}--{file.name}'] = f'{i:02d}.{int_countsheets:02d}--{file.name}'

            int_countsheets += 1

        return dict_file_data, dict_file_names

    @staticmethod
    def fn_display_metadata_dashboard(dict_file_data, dict_file_names, lst_Dashboard_columns,dte_Process_start_time = datetime.now(),dte_Process_end_time = datetime.now()):
        """Displays metadata dashboard with filters."""
        df_dashboard = pd.DataFrame(dict_file_data.values(), columns=lst_Dashboard_columns)
        df_dashboard[["MIN Date", "MAX Date"]] = df_dashboard[["MIN Date", "MAX Date"]].apply(pd.to_datetime, errors='coerce')

        # Date Filters
        cols_dates = st.columns(2)
        with cols_dates[0]:
            dte_Mindate = df_dashboard["MIN Date"].min()
            dte_Mindate = dte_Mindate.date() if pd.notna(dte_Mindate) else datetime(1900, 1, 1).date()
            Filter_Mindate = st.date_input("START Date", value=dte_Mindate, format="YYYY-MM-DD")

        with cols_dates[1]:
            dte_Maxdate = df_dashboard["MAX Date"].max() or datetime(2100, 1, 1)
            dte_Maxdate = dte_Maxdate.date() if pd.notna(dte_Maxdate) else datetime(2100, 1, 1).date()
            Filter_Maxdate = st.date_input("END Date", value=dte_Maxdate, format="YYYY-MM-DD")

        df_dashboard = df_dashboard.loc[
            (df_dashboard["MIN Date"] >= pd.to_datetime(Filter_Mindate)) &
            (df_dashboard["MAX Date"] <= pd.to_datetime(Filter_Maxdate) + pd.Timedelta(days=1))
            # (df_dashboard["MAX Date"] <= pd.to_datetime(Filter_Maxdate))
        ]

        # Category & File Filters
        selected_categories = st.multiselect("Filter by Category:", df_dashboard["Category"].unique(), default=df_dashboard["Category"].unique())
        # selected_files = st.multiselect("SELECT FILES:", list(dict_file_names.keys()), default=list(dict_file_names.keys()))
        # df_included_files = df_dashboard[df_dashboard["File Name"].isin(selected_files)]
        df_included_files = df_dashboard

        # df_dashboard = df_dashboard[df_dashboard["Category"].isin(selected_categories) & df_dashboard["File Name"].isin(selected_files)]
        # df_dashboard = df_dashboard[df_dashboard["File Name"].isin(selected_files)]

        # Display Dashboard
        # st.dataframe(df_dashboard.drop(columns=["N°"]), use_container_width=True, height=500, hide_index=True)
        st.dataframe(df_dashboard, use_container_width=True, height=500, hide_index=True)

        # Total Processing Time Calculation
        total_processing_time = sum(
            float(row.split(":")[0]) * 60 + float(row.split(":")[1].split(".")[0]) + float("0." + row.split(".")[1]) 
            for row in df_included_files["Processing Time"]
        )
        total_time_str = time.strftime("%M", time.gmtime(total_processing_time)) + ' Min ' + \
                        time.strftime("%S", time.gmtime(total_processing_time)) + ' Sec ' + \
                        f"{int((total_processing_time % 1) * 100):02d}" + "'"

        # Display Processing Stats
        col_01, col_02, col_03 = st.columns([1,1,2])
        with col_01:
            str_Processing_start = f"Data load START : {dte_Process_start_time.strftime('%d-%b-%Y %H:%M:%S')}"
            st.markdown(f"<div style='background-color: rgb(220,240,210);font-weight: bold; font-style: italic; color: blue; padding: 2px; border-radius: 5px; font-family: Cambria; display: inline-block;'>{str_Processing_start}</div>", unsafe_allow_html=True)
        with col_02:
            str_Processing_end = f"Data load END : {dte_Process_end_time.strftime('%d-%b-%Y %H:%M:%S')}"
            st.markdown(f"<div style='background-color: rgb(220,240,210);font-weight: bold; font-style: italic; color: blue; padding: 2px; border-radius: 5px; font-family: Cambria; display: inline-block;'>{str_Processing_end}</div>", unsafe_allow_html=True)
        with col_03:
            str_Processing_message = f"Total processing time for selected files ({len(df_included_files)} files): {total_time_str}"
            st.markdown(f"<div style='background-color: rgb(220,240,210);font-weight: bold; font-style: italic; color: blue; padding: 2px; border-radius: 5px; font-family: Cambria; display: inline-block;'>{str_Processing_message}</div>", unsafe_allow_html=True)


    @staticmethod
    def fn_get_metadata_and_stdzed_dfs(file):
        tmp_file_path = None  # Ensure variable exists
        dic_myfilesheetscategories = {}

        for str_extension in ['.xls', '.xlsx', '.xlsb', '.xlsm']:
            if file.name.endswith(str_extension):
                with tempfile.NamedTemporaryFile(delete=False, suffix=str_extension) as tmp_file:
                    tmp_file.write(file.read())
                    tmp_file_path = tmp_file.name

        # Ensure file was properly created
        if not tmp_file_path:
            raise ValueError(f"⚠️ No valid file extension found for '{file.name}'")

        obj_file = os.path.abspath(tmp_file_path)
        str_Folderpath = ""

        try:
            # Retrieve the sheets categories for the uploaded file
            dic_myfilesheetscategories = filehandler.fn_get_Uploadedfile_Sheetscategories(str_Folderpath, obj_file)
            if not isinstance(dic_myfilesheetscategories, dict):
                raise ValueError("Invalid file structure: Expected a dictionary but received a different type.")

            # List of sheet names & Temporary dictionary to hold updates
            lst_Sheets = list(dic_myfilesheetscategories.keys())
            dic_updated_sheets = {}

            for str_mysheetname in lst_Sheets:
                try:
                    # Extract details safely with default values to avoid KeyErrors
                    file_metadata = dic_myfilesheetscategories.get(str_mysheetname, ["Unknown", 0, [], [], []])
                    str_Filecategory, int_myheaderrow, lst_mycurrentheaders, lst_mycurrentheaders_idx, lst_Findapnewheaders = file_metadata

                    # Log metadata values
                    logging.debug(f"Processing sheet: {str_mysheetname}")
                    logging.debug(f"File Metadata: Category={str_Filecategory}, HeaderRow={int_myheaderrow}, "
                                f"CurrentHeaders={lst_mycurrentheaders}, HeaderIndexes={lst_mycurrentheaders_idx}, "
                                f"NewHeaders={lst_Findapnewheaders}")

                    dic_listheadersgroup = {}
                    if str_Filecategory.upper() in ['UNKNOWN', None, '']:
                        int_myheaderrow = 0

                    # Convert the sheet to a dataframe
                    df_mysheet2dataframe = filehandler.fn_convert_Worksheet2dataframe(
                        str_Folderpath, obj_file, str_Filecategory, str_mysheetname, int_myheaderrow, lst_mycurrentheaders,
                        lst_mycurrentheaders_idx, lst_Findapnewheaders, dic_listheadersgroup)

                    df_mysheet2dataframe = filehandler.fn_handle_specific_cases(str_Filecategory,df_mysheet2dataframe)

                    # Store the dataframe in a temporary dictionary
                    dic_updated_sheets[str_mysheetname] = [str_Filecategory, int_myheaderrow, lst_mycurrentheaders,
                                                            lst_mycurrentheaders_idx, lst_Findapnewheaders, df_mysheet2dataframe]

                except Exception as e:
                    st.error(f"⚠️ Error processing sheet '{str_mysheetname}': {e}")
                    logging.error(f"Error processing sheet '{str_mysheetname}': {e}")
                    logging.error(traceback.format_exc())

            # Apply updates to the dictionary AFTER iteration
            for sheet_name, lst_updated in dic_updated_sheets.items():
                dic_myfilesheetscategories[sheet_name] = lst_updated

        except FileNotFoundError as e:
            st.error(f"⚠️ File not found: {e}")
            logging.error(f"File not found: {e}")
        except ValueError as e:
            st.error(f"⚠️ Data format error: {e}")
            logging.error(f"Data format error: {e}")
        except Exception as e:
            st.error(f"⚠️ Unexpected error: {e}")
            logging.error(f"Unexpected error: {e}")
            logging.error(traceback.format_exc())

        return dic_myfilesheetscategories
