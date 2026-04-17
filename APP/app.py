import streamlit as st
import pandas as pd
import os


st.set_page_config(layout='wide')


st.title('Kenya Health Facility Landscape Analysis Dashboard')
st.write('Transforming Data into Actionable Healthcare Intelligence')

st.header('Overview')
st.write('''Welcome to the Kenya Health Facility Landscape Analysis Dashboard, 
         an interactive data visualization platform developed as part of an undergraduate research project at The Co-operative University of Kenya. 
         This dashboard transforms raw health facility data from the Social Health Authority (SHA) into meaningful insights for healthcare planning, 
         policy development, and strategic decision-making.
         The platform provides a comprehensive, data-driven view of Kenya's health facility infrastructure, 
         enabling users to explore facility distribution, assess coverage equity, and identify underserved regions across all 47 counties.''')

st.header('Purpose and Objectives')
st.write('''1. Visualize the spatial distribution of health facilities across Kenya's counties
2. Quantify healthcare access disparities through equity scoring metrics
3. Analyze the public-private mix of healthcare service provision
4. Identify coverage gaps and priority areas for infrastructure investment
5. Support evidence-based decision-making for Universal Health Coverage (UHC) initiatives''')

st.header('Data Sources')

st.write('''Data Type Source Description
Health Facilities Social Health Authority (SHA) Master facility list including names, types, locations, and ownership
Geographic Boundaries Kenya Open Data Portal County and sub-county administrative boundaries
Population Data Kenya National Bureau of Statistics (KNBS) County-level population estimates for density calculations
Spatial Reference OpenStreetMap Base maps and coordinate validation''')


datasets = [
    'CONTRACTED-FACILITES-REHABILITATION',
    'CONTRACTED-FACILITIES-COMMUNITY-HOSP',
    'CONTRACTED-FACILITIES-COUNTY-GOVT',
    'CONTRACTED-FACILITIES-FBOs',
    'CONTRACTED-FACILITIES-GOVERNMENT-OF-KENYA',
    'CONTRACTED-FACILITIES-NGOs',
    'CONTRACTED-FACILITIES-PRIVATE',
    'SHA-FACILITIES-PAYMENT-ANALYSIS'
                        ]
st.header('Datasets')
st.write(pd.DataFrame(datasets))

st.header('Key Features')
st.write('''- **Facility Location Viewer:** Visualize health facilities across Kenya with color-coded markers by facility type
- **County-Level Analysis:** Drill down into specific counties for detailed distribution patterns
- **Filtering Capabilities:** Narrow results by county, facility type, ownership, and KEPH level
- **Custom Views:** Save and share customized map configurations''')

st.header('Analytical Dashboards')
st.write('''- Distribution Analytics: Bar charts, pie charts, and heatmaps showing facility concentrations
- Equity Assessment: Coverage scores and gap analysis identifying underserved populations
- Comparative Tools: Benchmark counties against national averages and peer regions
- Trend Indicators: Track changes in facility distribution over time''')

st.header('Reporting and Export')
st.write('''- Data Export: Download filtered datasets in CSV format for further analysis
- Visualization Export: Save charts and maps as high-resolution images for reports
- Summary Reports: Generate automated county-level facility summaries''')

st.header('How To Use The Dashboard')
st.write('''**Step 1: Apply Filters:** Use the sidebar controls to select specific counties, facility types, or KEPH levels of interest.

**Step 2: Explore Visualizations:** Navigate through the tabs to access different analytical views:

- Interactive Map: Geographic distribution of facilities
- Analysis: Charts showing facility counts by category
- Equity Assessment: Coverage scores and gap identification
- Data Explorer: Raw facility data with search functionality

**Step 3: Generate Insights:** Hover over visualizations for detailed information, click on elements to filter, and use the export functions to save your findings.

**Step 4: Download Results:** Export filtered datasets or visualization images for inclusion in reports, presentations, or further analysis.''')

st.header('Limitations and Considerations')
st.write('''- Coordinate Accuracy: Some facilities utilize county centroids rather than exact locations
- Data Currency: Reflects the most recent SHA dataset; facilities opened after this period may not be included
- Service Capacity: Represents facility presence, not operational capacity or service quality
- Population Data: Uses official census estimates which may not capture recent demographic shifts''')

st.header('Citations and Acknowledgement')
st.write('''**Citation:**\n
Kelvin Mutuku Muthama. (2026). Kenya Health Facility Landscape Analysis Dashboard Streamlit. The Co-operative University of Kenya.

**Data Source Acknowledgment:**\n
This dashboard utilizes data provided by the Social Health Authority (SHA) Kenya. The Authority bears no responsibility for the analyses, interpretations, or conclusions derived from these data.''')

st.write('This dashboard is part of an undergraduate research project at The Co-operative University of Kenya, School of Computing and Mathematics. For questions, feedback, or collaboration inquiries, please contact:')
col1, col2, col3 = st.columns(3, border=True)
with col1:
    st.write('G-mail: muthamakelvinmutuku@gmail.com')
with col2:
    st.write('WhatsApp: 0789813147')
with col3:
    st.write('Telegram: @tel_tush')

st.write('© 2024 | All Rights Reserved | Data Source: Social Health Authority (SHA) Kenya')