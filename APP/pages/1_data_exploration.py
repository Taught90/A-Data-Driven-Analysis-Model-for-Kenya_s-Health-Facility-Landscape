import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(layout='wide',
                   page_icon="APP/ASSETS/PNGs/health-svgrepo-com.png",
                   )

datasets = [
    'CONTRACTED-FACILITES-REHABILITATION',
    'CONTRACTED-FACILITIES-COMMUNITY-HOSP',
    'CONTRACTED-FACILITIES-INSTITUTIONAL',
    'CONTRACTED-FACILITIES-COUNTY-GOVT',
    'CONTRACTED-FACILITIES-FBOs',
    'CONTRACTED-FACILITIES-GOVERNMENT-OF-KENYA',
    'CONTRACTED-FACILITIES-NGOs',
    'CONTRACTED-FACILITIES-PRIVATE',
    'SHA-FACILITIES-PAYMENT-ANALYSIS',
    'POPULATION DATA'
                        ]
dataset = st.sidebar.selectbox('Select A dataset',datasets)
dataset = str(dataset).replace("[","").replace("]","").replace("'", "")
data_path = ' A-Data-Driven-Analysis-Model-for-Kenya_s-Health-Facility-Landscape/DATA/CLEANED DATA (CSV)'
filename = f'{data_path}/{dataset}.csv'
download_filename = f'{dataset}.csv'


filenames = []
for additional_dataset in datasets:
    additional_dataset = str(additional_dataset).replace("[","").replace("]","").replace("'", "")
    data_path = ' A-Data-Driven-Analysis-Model-for-Kenya_s-Health-Facility-Landscape/DATA/CLEANED DATA (CSV)'
    filenames.append(f'{data_path}/{additional_dataset}.csv')
filenames.pop(8)


st.header(dataset)

if 'ALL DATASETS' not in dataset:
    # Readint the file of the dataset selected
    DataFrame = pd.read_csv(filename)
    if 'CONTRACTED-FACILITIES-FBOs' in filename:
        import regex as re
        eq = re.sub('\d+')
        DataFrame['Facility Name'].replace(eq, '')
    st.write('## Dataset Overview')
    st.write(DataFrame)

    st.write('### Filtered Data Overview')
    if 'Keph Level' in DataFrame.columns and 'County' in DataFrame.columns:
        col3, col4 = st.columns([2,3], border=True)
        keph_levels = DataFrame['Keph Level'].unique()
        counties = DataFrame['County'].unique()

        with col3:
            keph_level = st.selectbox('Select a Keph Level', keph_levels)
            # if keph_level:
        with col4:
            county = st.selectbox('Select a county', counties)
        st.write(DataFrame[
                (DataFrame['County'] == county) & 
                (DataFrame['Keph Level'] == keph_level)
                ])
    else:
        counties = DataFrame['County'].unique()
        county = st.selectbox('Select a county', counties)
        st.write(DataFrame[
                (DataFrame['County'] == county)
                ])

    # Dataset Shape and Description
    st.write('### Dataset Shape and Description')
    col1, col2 = st.columns([1,4], border=True)
    with col1:
        st.write('### Dataset Shape')
        st.write(f'##### {DataFrame.shape.__str__()}')
    with col2:
        st.write('#### Description')
        st.write(DataFrame.describe())
    st.download_button(label='download CSV',
                       file_name = download_filename,
                       data = DataFrame.to_csv(index=False))


elif dataset == 'ALL DATASETS':

    list_of_DataFrames = []
    for filename in filenames:
        DataFrame = pd.read_csv(filename)
        list_of_DataFrames.append(DataFrame)
    combined_Dataframe = pd.concat(list_of_DataFrames, ignore_index=True)


    st.write('## Dataset Overview')
    st.write(combined_Dataframe)

    st.write('### Filtered Data Overview')
    if 'Keph Level' in combined_Dataframe.columns and 'County' in combined_Dataframe.columns:
        col3, col4 = st.columns([2,3], border=True)
        keph_levels = combined_Dataframe['Keph Level'].unique()
        counties = combined_Dataframe['County'].unique()

        with col3:
            keph_level = st.selectbox('Select a Keph Level', keph_levels)
            # if keph_level:
        with col4:
            county = st.selectbox('Select a county', counties)
        # Print rows where County is either 'NAIROBI' or 'KIAMBU'
        st.write(combined_Dataframe[
                (combined_Dataframe['County'] == county) & 
                (combined_Dataframe['Keph Level'] == keph_level)
                ])
        
    else:
        counties = combined_Dataframe['County'].unique()
        county = st.selectbox('Select a county', counties)

    # Dataset Shape and Description
    st.write('### Dataset Shape and Description')
    col1, col2 = st.columns([1,4], border=True)
    with col1:
        st.write('### Dataset Shape')
        st.write(f'##### {combined_Dataframe.shape.__str__()}')
    with col2:
        st.write('#### Description')
        st.write(combined_Dataframe.describe())


    