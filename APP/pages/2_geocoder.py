import streamlit as st
import pandas as pd
import os
from geopy.geocoders import Nominatim, ArcGIS
from geopy.extra.rate_limiter import RateLimiter
import time
import folium
from streamlit_folium import folium_static
import plotly.graph_objects as go
from io import BytesIO
import numpy as np

# Set page configuration
st.set_page_config(
    page_title="Kenya Healthcare Facilities Geocoder",
    page_icon="APP/ASSETS/PNGs/health-svgrepo-com.png",
    layout="wide"
)

# Initializing session state
if 'geocoded_df' not in st.session_state:
    st.session_state.geocoded_df = None
if 'current_dataset' not in st.session_state:
    st.session_state.current_dataset = None

# Title with Kenya
logo = st.image('APP/ASSETS/PNGs/map-pin-alt-svgrepo-com.png', width= 120)
st.title("Kenya Healthcare Facilities Geocoder")
st.markdown("Geocode healthcare facilities from SHA/NHIF datasets to get coordinates for mapping")

# Sidebar configuration
with st.sidebar:
    st.header("📁 Dataset Selection")
    
    # datasets list
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
    
    selected_dataset = st.selectbox('Select A dataset', datasets)
    
    # Data path configuration
    data_path = 'CLEANED DATA (CSV)'
    alternative_data_path = 'CLEANED DATA (CSV)/GEOCODED'
    
    st.markdown("---")
    st.header("Geocoding Settings")
    
    # Geocoding options
    use_county = st.checkbox("Include county in search", value=True, 
                             help="Adds county information to improve accuracy")
    
    geocoding_service = st.selectbox(
        "Geocoding Service",
        ["Nominatim (OpenStreetMap)", "ArcGIS (Faster)", "Both (Fallback)"]
    )
    
    batch_size = st.slider("Batch size", min_value=5, max_value=50, value=10,
                          help="Number of records to process before saving")
    
    test_mode = st.checkbox("Test mode (process only first 10 rows)", value=False)

def load_dataset(dataset_name):
    """Load the selected dataset"""
    try:
        if os.path.exists(alternative_data_path):
            filename = f'{alternative_data_path}/{dataset_name}.csv'
            df = pd.read_csv(filename)
            return df
        else:
            filename = f'{data_path}/{dataset_name}.csv'
            df = pd.read_csv(filename)
            return df
    except FileNotFoundError:
        st.error(f"File not found: {filename}")
        st.info("Please make sure your data is in the correct path:CLEANED DATA (CSV)/")
        return None
    except Exception as e:
        st.error(f"Error loading dataset: {str(e)}")
        return None

def detect_facility_columns(df):
    """Automatically detect facility name and location columns"""
    facility_cols = []
    county_cols = []
    subcounty_cols = []
    
    # Common column name patterns in Kenyan healthcare data
    facility_patterns = ['facility', 'hospital', 'health', 'clinic', 'name', 'facility_name']
    county_patterns = ['county', 'district', 'region']
    subcounty_patterns = ['subcounty', 'sub_county', 'division', 'ward']
    
    for col in df.columns:
        col_lower = col.lower()
        
        # Detect facility name columns
        if any(pattern in col_lower for pattern in facility_patterns):
            facility_cols.append(col)
        
        # Detect county columns
        if any(pattern in col_lower for pattern in county_patterns):
            county_cols.append(col)
        
        # Detect subcounty columns
        if any(pattern in col_lower for pattern in subcounty_patterns):
            subcounty_cols.append(col)
    
    return facility_cols, county_cols, subcounty_cols

def geocode_facilities_kenya(df, facility_col, county_col=None, subcounty_col=None, 
                            service='nominatim', test_mode=False):
    """
    Geocode Kenyan healthcare facilities with improved accuracy
    """
    
    # Initialize geocoder
    if service == 'nominatim' or service == 'Both (Fallback)':
        geolocator = Nominatim(user_agent="kenya_healthcare_geocoder")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    else:
        geolocator = ArcGIS(user_agent="kenya_healthcare_geocoder")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=0.5)
    
    # Add Kenya to search context
    country = "Kenya"
    
    # Initialize columns
    df['latitude'] = np.nan
    df['longitude'] = np.nan
    df['geocoded_address'] = ''
    df['geocoding_status'] = 'Pending'
    df['matched_county'] = ''
    
    # Limit rows if in test mode
    if test_mode:
        df = df.head(10).copy()
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_rows = len(df)
    successful = 0
    failed = 0
    
    for idx, row in df.iterrows():
        try:
            # Build search query
            facility_name = str(row[facility_col]) if pd.notna(row[facility_col]) else ""
            
            # Add location context
            location_parts = [facility_name]
            
            if county_col and pd.notna(row.get(county_col, '')):
                location_parts.append(str(row[county_col]))
            
            if subcounty_col and pd.notna(row.get(subcounty_col, '')):
                location_parts.append(str(row[subcounty_col]))
            
            location_parts.append(country)
            query = ", ".join(location_parts)
            
            status_text.text(f"📍 Geocoding: {query[:100]}...")
            
            # Try multiple search variations if needed
            location = None
            search_variations = [
                query,
                f"{facility_name}, {country}",
                f"{facility_name}, health facility, {country}"
            ]
            
            for search_query in search_variations:
                try:
                    location = geocode(search_query)
                    if location:
                        break
                except:
                    continue
            
            if location:
                df.at[idx, 'latitude'] = location.latitude
                df.at[idx, 'longitude'] = location.longitude
                df.at[idx, 'geocoded_address'] = location.address
                df.at[idx, 'geocoding_status'] = 'Success'
                
                # Try to extract county from geocoded address
                if 'county' in location.address.lower():
                    df.at[idx, 'matched_county'] = 'Found in address'
                
                successful += 1
            else:
                df.at[idx, 'geocoding_status'] = 'Failed - No results'
                failed += 1
            
        except Exception as e:
            df.at[idx, 'geocoding_status'] = f'Error: {str(e)[:50]}'
            failed += 1
        
        # Update progress
        progress_bar.progress((idx + 1) / total_rows)
        
        # Save intermediate results
        if (idx + 1) % batch_size == 0:
            st.session_state.geocoded_df = df.copy()
    
    progress_bar.empty()
    status_text.empty()
    
    st.success(f"""
    ✅ Geocoding complete!
    - Successful: {successful} facilities
    - Failed: {failed} facilities
    - Success rate: {(successful/total_rows)*100:.1f}%
    """)
    
    return st.session_state.geocoded_df

def create_kenya_map(df):
    """Create a map focused on Kenya"""
    map_df = df.dropna(subset=['latitude', 'longitude']).copy()
    
    if map_df.empty:
        st.warning("No coordinates available to display on map")
        return None
    
    # Kenya's approximate center
    kenya_center = [-1.286389, 36.817223]  # Nairobi
    
    m = folium.Map(location=kenya_center, zoom_start=6)
    
    # Add markers with county colors if available
    for idx, row in map_df.iterrows():
        # Create popup with facility details
        popup_text = f"""
        <b>{row.get(facility_col, 'Facility')}</b><br>
        County: {row.get(county_col, 'N/A')}<br>
        Status: {row.get('geocoding_status', 'N/A')}<br>
        Lat: {row['latitude']:.4f}<br>
        Lon: {row['longitude']:.4f}
        """
        
        # Different colors based on geocoding success
        icon_color = 'green' if row.get('geocoding_status') == 'Success' else 'orange'
        
        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color=icon_color, icon='plus', prefix='fa')
        ).add_to(m)
    
    return m

# Main app logic
if selected_dataset:
    st.subheader(f"Dataset : {selected_dataset}")
    
    # Load dataset
    with st.spinner("Loading dataset..."):
        df = load_dataset(selected_dataset)
    
    if df is not None:
        # Display dataset info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Facilities", len(df))
        with col2:
            st.metric("Columns", len(df.columns))
        with col3:
            # Check if already geocoded
            has_coords = 'latitude' in df.columns and df['latitude'].notna().any()
            st.metric("Has Coordinates", "Yes" if has_coords else "No")
        
        # Detect columns
        facility_cols, county_cols, subcounty_cols = detect_facility_columns(df)
        
        # Column selection
        st.subheader("🔍 Column Mapping")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if facility_cols:
                facility_col = st.selectbox(
                    "Facility Name Column",
                    options=facility_cols,
                    index=0 if facility_cols else None
                )
            else:
                facility_col = st.selectbox(
                    "Facility Name Column (select manually)",
                    options=df.columns
                )
        
        with col2:
            if use_county:
                if county_cols:
                    county_col = st.selectbox(
                        "County Column (optional)",
                        options=['None'] + county_cols,
                        index=1 if county_cols else 0
                    )
                else:
                    county_col = st.selectbox(
                        "County Column (select manually or None)",
                        options=['None'] + list(df.columns)
                )
                county_col = None if county_col == 'None' else county_col
            
            # Subcounty selection
            if subcounty_cols and use_county:
                subcounty_col = st.selectbox(
                    "Subcounty Column (optional)",
                    options=['None'] + subcounty_cols,
                    index=0
                )
                subcounty_col = None if subcounty_col == 'None' else subcounty_col
            else:
                subcounty_col = None
        
        # Data preview
        with st.expander("📋 Data Preview"):
            st.dataframe(df.head(10), use_container_width=True)
        
        # Geocoding button
        if st.button("🚀 Start Geocoding", type="primary", use_container_width=True):
            
            # Determine geocoding service
            if geocoding_service == "Both (Fallback)":
                # Try Nominatim first, then ArcGIS
                df_result = geocode_facilities_kenya(
                    df, facility_col, county_col, subcounty_col,
                    service='nominatim', test_mode=test_mode
                )
                
                # Try ArcGIS for failed ones
                failed_mask = df_result['geocoding_status'] != 'Success'
                if failed_mask.any():
                    st.info("🔄 Trying ArcGIS for failed facilities...")
                    df_failed = df_result[failed_mask].copy()
                    df_arcgis = geocode_facilities_kenya(
                        df_failed, facility_col, county_col, subcounty_col,
                        service='arcgis', test_mode=False
                    )
                    
                    # Update successful ones from ArcGIS
                    success_mask = df_arcgis['geocoding_status'] == 'Success'
                    df_result.loc[df_arcgis[success_mask].index] = df_arcgis[success_mask]
                    
            else:
                service = 'nominatim' if 'Nominatim' in geocoding_service else 'arcgis'
                df_result = geocode_facilities_kenya(
                    df, facility_col, county_col, subcounty_col,
                    service=service, test_mode=test_mode
                )
            
            st.session_state.geocoded_df = df_result
            st.session_state.current_dataset = selected_dataset
            st.rerun()
        
        # Display results if available
        if st.session_state.geocoded_df is not None and st.session_state.current_dataset == selected_dataset:
            st.markdown("---")
            st.subheader("🗺️ Geocoding Results")
            
            df_result = st.session_state.geocoded_df
            
            # Statistics
            success_count = (df_result['geocoding_status'] == 'Success').sum()
            total_count = len(df_result)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Successfully Geocoded", f"{success_count}/{total_count}")
            with col2:
                st.metric("Success Rate", f"{(success_count/total_count)*100:.1f}%")
            with col3:
                failed_count = (df_result['geocoding_status'] != 'Success').sum()
                st.metric("Failed", failed_count)
            
            # Map view
            map_tab, data_tab, stats_tab = st.tabs(["🗺️ Map View", "📊 Data View", "📈 Statistics"])
            
            with map_tab:
                m = create_kenya_map(df_result)
                if m:
                    folium_static(m, width=1000, height=600)
            
            with data_tab:
                st.dataframe(df_result, use_container_width=True)
                
                # Download buttons
                col1, col2 = st.columns(2)
                with col1:
                    csv = df_result.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name=f"{selected_dataset}.csv",
                        mime="text/csv"
                    )
                
                with col2:
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_result.to_excel(writer, index=False, sheet_name='Facilities')
                    
                    st.download_button(
                        label="📥 Download as Excel",
                        data=output.getvalue(),
                        file_name=f"geocoded_{selected_dataset}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            
            with stats_tab:
                # Success rate by county if county column exists
                if county_col and county_col in df_result.columns:
                    county_stats = df_result.groupby(county_col).agg({
                        'geocoding_status': lambda x: (x == 'Success').mean()
                    }).round(2) * 100
                    county_stats.columns = ['Success Rate (%)']
                    st.bar_chart(county_stats)