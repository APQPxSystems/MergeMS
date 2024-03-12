# Import Libraries
# import hmac
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime, timedelta, date
from io import BytesIO

# Streamlit Configurations
st.set_page_config(page_title="ME Dept Apps", layout="wide")
hide_st_style = """
                <style>
                #MainMenu {visibility:hidden;}
                footer {visibility:hidden;}
                header {visibility:hidden;}
                </style>
                """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Remove top white space
st.markdown("""
        <style>
                .block-container {
                    padding-top: 0rem;
                    padding-bottom: 0rem;
                    padding-left: 1rem;
                    padding-right: 1rem;
                }
        </style>
        """, unsafe_allow_html=True)

# App title and info
st.markdown("<p class='app_sub_title'>MANUFACTURING ENGINEERING DEPARTMENT | SYSTEMS ENGINEERING</p>", unsafe_allow_html=True)
# Tagline
st.markdown("<p class='tagline'>Mitigating Encumbrances; Moving towards Excellence</p>", unsafe_allow_html=True)
st.markdown("<p class='app_title'>MANUFACTURING ENGINEERING WEB APP</p>", unsafe_allow_html=True)     
st.markdown("""<p class='app_info'>This web app is a collection of Manufacturing Engineering Department's automation tools.
            This runs on streamlit's cloud server and is not connected to any database.
            Therefore, any data uploaded will not be saved or collected and will vanish everytime the app is refreshed.</p>""", unsafe_allow_html=True)

# User Roles
credential_col1, credential_col2 = st.columns([2,1])
with credential_col1:
    user_role = st.selectbox("Select your department.", ["Manufacturing Engineering",
                                                        "Production",
                                                        "Production Engineering",
                                                        "Quality Assurance"])
with credential_col2:
    app_key = st.text_input("Enter department key.", type="password")
    
if user_role == "Manufacturing Engineering" and app_key == "MESE24":

    automation_app = st.selectbox("Select Automation Tool:", 
                                ["Merge Master Sample Automation (Labels)",
                                "Merge Master Sample (Products to Merge)"])

    # Merge Master Sample
    if automation_app == "Merge Master Sample Automation (Labels)":
        # App Title and Info
        st.title("Merge Master Sample (Labels)")
        st.markdown("""How to Use: On your .xls file of merge master sample, delete the rows that contain
                    the signatories and revisions. Then, unmerge the merged cells within the dataframe. Save the file as .csv.
                    Drag and drop the file on the upload box and the data will be automatically edited.""")

        # Upload File --- Must Be CSV
        raw_data = st.file_uploader("Upload file here:")

        if raw_data is not None:
            raw_data = pd.read_csv(raw_data)
            st.title("Original Data")
            st.write(raw_data)

            # Concatenate Column Contents -- Conn, AcceNo, ExteNo into a new column 'Conn'
            raw_data['Conn'] = raw_data['Conn'].astype(str) + raw_data['AcceNo'].astype(str) + raw_data['ExteNo'].astype(str)

            # Convert 'Conn' column values to integers, handling NaN values and non-numeric values
            raw_data['Conn'] = pd.to_numeric(raw_data['Conn'].str.replace(r'[^0-9]', '', regex=True), errors='coerce', downcast='integer')

            # Drop the 'AcceNo' and 'ExteNo' columns
            raw_data.drop(["AcceNo", "ExteNo"], axis=1, inplace=True)

            # Rename columns after specified start column
            rename_start_column = st.text_input("Enter the start column for renaming:")
            characters_to_replace_input = st.number_input("Enter the number of characters to replace with '*':", min_value=0, step=1)
            applicability_symbol = st.text_input("Input used applicability symbol:")
            
            # Count of applicability_symbol in all columns after rename_start_column
            if rename_start_column and applicability_symbol:
                count_row = raw_data.iloc[:, raw_data.columns.get_loc(rename_start_column):].apply(lambda col: col.astype(str).str.count(applicability_symbol)).sum()
                count_row.name = "Count of Applicable Parts" 
                count_row = count_row.to_frame().T
                count_row = count_row.drop(rename_start_column, axis=1)
                count_row = count_row.transpose()

                st.title("Count of Applicable Parts Per Product")
                st.dataframe(count_row.style.highlight_max(axis=0), width=700)


            def rename_columns(raw_data, start_column, characters_to_replace):
                rename_mapping = {}
                start_renaming = False
                fixed_star_count = 2  # Set the fixed number of '*' characters
            
                for col in raw_data.columns:
                    if col == start_column:
                        start_renaming = True
                    if start_renaming and col != start_column:
                        new_col_name = col[:-min(characters_to_replace, len(col))].strip() + '*' * fixed_star_count
                        rename_mapping[col] = new_col_name
            
                raw_data.rename(columns=rename_mapping, inplace=True)
                raw_data = raw_data.rename(columns={start_column + '*' * fixed_star_count: start_column})
            
                return raw_data
            
            raw_data = rename_columns(raw_data, rename_start_column, characters_to_replace_input)

            # Replace "●" values with corresponding column names
            for col in raw_data.columns:
                raw_data[col] = raw_data[col].replace(applicability_symbol, col)

            # Concatenate "Length" to "PartsName" if "Length" has a value
            if 'Length' in raw_data.columns:
                raw_data['PartsName'] = raw_data.apply(lambda row: f"{row['PartsName']} L={row['Length']}" if pd.notna(row['Length']) else row['PartsName'], axis=1)

            # Drop PartsClass, PartsCode, Length, Method, Qty, Attachment Process
            columns_to_drop = ['PartsClass', 'PartsCode', 'Length', 'Method', 'Qty', 'Attachment Process']
            raw_data.drop(columns=columns_to_drop, inplace=True)

            # Transpose the DataFrame without including the index
            transposed_data = raw_data.transpose().reset_index(drop=True)

            # Define a custom function to shift non-null values upwards
            def shift_cells_up(col):
                non_null_values = col.dropna()
                col[:len(non_null_values)] = non_null_values
                col[len(non_null_values):] = None
                return col

            # Apply the custom function to each column
            transposed_data = transposed_data.apply(shift_cells_up, axis=0)
            
            # Add a blank column every after a column in transposed-data
            [transposed_data.insert(i + 1, f'Blank_{i}', np.nan, allow_duplicates=True) for i in range(transposed_data.shape[1] - 1, 0, -1)]
            
            # Display Edited Data
            st.title("Edited Data")
            st.write(transposed_data)

            # Download Button
            @st.cache_data
            def convert_df(df):
                # IMPORTANT: Cache the conversion to prevent computation on every rerun
                return df.to_csv().encode('utf-8')

            csv = convert_df(transposed_data)

            st.download_button(
                label="Download Edited Data as CSV",
                data=csv,
                file_name='MergeMasterSample_Automated.csv',
                mime='text/csv',
            )
        st.write("__________________________________________________")

    # Merge Master Sample (Products to Merge)
    if automation_app == "Merge Master Sample (Products to Merge)":
        st.title("Merge Master Sample (Products to Merge)")
        
        # Upload CSV
        csv_file = st.file_uploader("Upload csv file here:")
        
        if csv_file is not None:
            csv_file = pd.read_csv(csv_file)
            st.subheader("Preview of Uploaded File")
            st.dataframe(csv_file)
            
            # Applicability Symbol Input
            applicability_symbol = st.text_input("Input used applicability symbol:")
            
            # Step 1 -- Total of Applicable Parts per Product -- Additional Column
            def count_occurrences(row, value):
                return (row==value).sum()
            
            # Apply the custom function to each row of the DataFrame
            csv_file['Total Applicable C'] = csv_file.apply(lambda row: count_occurrences(row, applicability_symbol), axis=1)
            
            # st.write("Added Total Applicability Column")
            # st.dataframe(csv_file)
            
            # Step 2 -- Delete all rows with the maximum value in the Total Applicable column
            drop_row_condition = csv_file['Total Applicable C'] == csv_file['Total Applicable C'].max()
            csv_file = csv_file[~drop_row_condition]
            
            # st.write("Dropped rows with maximum value")
            # st.dataframe(csv_file)
            
            # Step 3 -- Total of Applicable Products per Part -- Additional Row
        
            # Transpose dataframe
            csv_file = csv_file.transpose()
            
            # Add another column -- Total Applicable R
            def count_occurrences(row, value):
                return (row==value).sum()
            
            # Apply the custom function to each row of the DataFrame
            csv_file['Total Applicable R'] = csv_file.apply(lambda row: count_occurrences(row, applicability_symbol), axis=1)
            
            # Transpose dataframe
            csv_file = csv_file.transpose()
            
            # st.write("Added Total Applicability Row")
            # st.dataframe(csv_file)
            
            # Step 4 - Print the column name of the row with highest value of Total Applicable R
            mother_product = csv_file.iloc[-1].idxmax()
            
            # st.title(f"Mother Product -> {mother_product}")
            
            # Step 5 -- Drop unnecessary columns
            # Multiselect box to choose columns to drop
            columns_to_drop = st.multiselect("Select columns to drop:", csv_file.columns)
            
            branch_column = st.selectbox("Select Branch Column:", csv_file.columns)
        
            # Button to drop selected columns
            if st.button("Generate Proucts Required for Merge Master Sample"):
                # Drop selected columns
                csv_file = csv_file.drop(columns=columns_to_drop)
                
                # Display the DataFrame after dropping selected columns
                # st.subheader("DataFrame after dropping selected columns:")
                # st.write(csv_file)
            
                # Step 6 -- Final
                
        
        
                # Step 7 -- Final, Final
                # Initialize a list to store the deleted values in the 'Part' column and the chosen column name for each iteration
                deleted_values_per_iteration = []
        
                # Continue the process until the DataFrame is empty
                while not csv_file.empty:
                    # Identify the column with the highest count of non-NaN values
                    column_with_max_count = csv_file.iloc[:, 1:].count().idxmax()
                    
                    # Remove rows with non-NaN values in the identified column
                    deleted_values = csv_file.loc[~csv_file[column_with_max_count].isna(), branch_column].tolist()
                    
                    # Append the chosen column name to the list
                    deleted_values_per_iteration.append({'Column': column_with_max_count, 'DeletedValues': deleted_values})
                    
                    # Update the DataFrame by removing rows with non-NaN values in the identified column
                    csv_file = csv_file[csv_file[column_with_max_count].isna()]
        
                # Display the deleted values and the chosen column for each iteration
                st.title("Products Needed to Form the Merge Master Sample")
                for i, values_dict in enumerate(deleted_values_per_iteration, start=1):
                    column_name = values_dict['Column']
                    deleted_values = values_dict['DeletedValues']
                    
                    # Highlight the first iteration as the "Mother Product"
                    if i == 1:
                        st.subheader(f'{i}: Mother Product: {column_name} \n Branches: {deleted_values}')
                    else:
                        st.subheader(f'{i}: Additional Product: {column_name} \n Branches: {deleted_values}')


st.write("______________________________________________________")  


with open('MergeMasterSample\style.css') as f:
    css = f.read()

st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)
