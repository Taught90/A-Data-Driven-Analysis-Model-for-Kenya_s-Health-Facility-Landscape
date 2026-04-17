# enhanced_dashboard_fixed.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime
import json
import os

# Set page configuration
st.set_page_config(
    page_title="Kenya Health Facilities & Population Dashboard",
    page_icon="../APP/ASSETS/PNGs/health-svgrepo-com.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'dashboard_data' not in st.session_state:
    st.session_state.dashboard_data = None
if 'population_data' not in st.session_state:
    st.session_state.population_data = None
if 'filtered_data' not in st.session_state:
    st.session_state.filtered_data = None
if 'saved_views' not in st.session_state:
    st.session_state.saved_views = {}
if 'current_view' not in st.session_state:
    st.session_state.current_view = None

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: start;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: start;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

def classify_kenya_facility(facility_name, facility_data=None):
    """
    Classify Kenyan health facilities according to the Kenya Health System
    """
    facility_str = str(facility_name).upper() if facility_name else ""
    
    # Kenya Health Facility Classifications
    classifications = {
        'Level 1': ['LEVEL1', 'LEVEL 1', 'L1', 'COMMUNITY', 'DISPENSARY'],
        'Level 2': ['LEVEL2', 'LEVEL 2', 'L2', 'HEALTH CENTRE', 'HEALTH CENTER'],
        'Level 3': ['LEVEL3', 'LEVEL 3', 'L3', 'SUB-COUNTY', 'SUBCOUNTY'],
        'Level 4': ['LEVEL4', 'LEVEL 4', 'L4', 'COUNTY', 'REFERRAL'],
        'Level 5': ['LEVEL5', 'LEVEL 5', 'L5', 'REGIONAL', 'PROVINCIAL'],
        'Level 6': ['LEVEL6', 'LEVEL 6', 'L6', 'NATIONAL', 'TEACHING', 'REFERRAL HOSPITAL']
    }
    
    # Ownership classifications
    ownership_map = {
        'REHABILITATION': 'REHABILITATION',
        'COMMUNITY-HOSP': 'COMMUNITY HOSPITAL',
        'COUNTY-GOVT': 'COUNTY GOVERNMENT HOSPITAL',
        'FBOs': 'FAITH BASED ORGANIZATIONs HOSPITAL',
        'GOVERNMENT-OF-KENYA': 'NATIONAL GOVERNMENT HOSPITAL',
        'NGOs': 'NON-GOVERNMENT ORGANIZATIONs HOSPITAL',
        'PRIVATE': 'PRIVATE HOSPITAL',
        'SHA-FACILITIES-PAYMENT-ANALYSIS': 'Mixed'
    }
    
    # KEPH Level classification
    keph_level = 'Unknown'
    for level, keywords in classifications.items():
        if any(keyword in facility_str for keyword in keywords):
            keph_level = level
            break
    
    # Ownership classification
    ownership = 'Unknown'
    for owner, keywords in ownership_map.items():
        if any(keyword in facility_str for keyword in keywords):
            ownership = owner
            break
    
    return {
        'keph_level': keph_level,
        'ownership': ownership,
        'facility_type': facility_str[:30]  # Truncated for display
    }

def load_all_datasets(data_path='../DATA/CLEANED DATA (CSV)/GEOCODED'):
    """Load all facility datasets"""
    datasets = [
        'CONTRACTED-FACILITES-REHABILITATION',
        'CONTRACTED-FACILITIES-COMMUNITY-HOSP',
        'CONTRACTED-FACILITIES-INSTITUTIONAL',
        'CONTRACTED-FACILITIES-COUNTY-GOVT',
        'CONTRACTED-FACILITIES-FBOs',
        'CONTRACTED-FACILITIES-GOVERNMENT-OF-KENYA',
        'CONTRACTED-FACILITIES-NGOs',
        'CONTRACTED-FACILITIES-PRIVATE',
        'SHA-FACILITIES-PAYMENT-ANALYSIS'
    ]
    
    all_data = []
    
    # Define KEPH level mapping based on facility type
    keph_mapping = {
        'REHABILITATION': 'Level 3',
        'COMMUNITY-HOSP': 'Level 2',
        'COUNTY-GOVT': 'Level 4',
        'FBOs': 'Level 2',
        'GOVERNMENT-OF-KENYA': 'Level 4',
        'NGOs': 'Level 2',
        'PRIVATE': 'Level 3',
        'SHA-FACILITIES-PAYMENT-ANALYSIS': 'Mixed'
    }
    
    ownership_mapping = {
        'REHABILITATION': 'REHABILITATION',
        'COMMUNITY-HOSP': 'COMMUNITY HOSPITAL',
        'COUNTY-GOVT': 'COUNTY GOVERNMENT HOSPITAL',
        'FBOs': 'FAITH BASED ORGANIZATIONs HOSPITAL',
        'GOVERNMENT-OF-KENYA': 'NATIONAL GOVERNMENT HOSPITAL',
        'NGOs': 'NON-GOVERNMENT ORGANIZATIONs HOSPITAL',
        'PRIVATE': 'PRIVATE HOSPITAL',
        'SHA-FACILITIES-PAYMENT-ANALYSIS': 'Mixed'
    }
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, dataset in enumerate(datasets):
        try:
            status_text.text(f"Loading {dataset}...")
            filename = f'{data_path}/{dataset}.csv'
            
            if os.path.exists(filename):
                df = pd.read_csv(filename)
                
                # Add metadata
                facility_type = dataset.replace('CONTRACTED-FACILITIES-', '') \
                                       .replace('CONTRACTED-FACILITES-', '')
                df['County'] = df['County']
                df['facility_category'] = facility_type
                df['ownership'] = ownership_mapping.get(facility_type, 'Unknown')
                df['keph_level'] = keph_mapping.get(facility_type, 'Level 2')
                df['data_source'] = dataset
                
                # Try to find facility name column
                name_col = None
                for col in df.columns:
                    if any(term in col.lower() for term in ['facility', 'hospital', 'name', 'facility_name']):
                        name_col = col
                        break
                
                if name_col:
                    df['Facility Name'] = df[name_col]
                else:
                    df['Facility Name'] = f"Facility_{i}_{df.index}"
                
                all_data.append(df)
                
        except Exception as e:
            st.warning(f"Could not load {dataset}: {str(e)}")
        
        progress_bar.progress((i + 1) / len(datasets))
    
    progress_bar.empty()
    status_text.empty()
    
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True, sort=False)
        return combined_df
    return None

def load_population_data(data_path='../DATA/CLEANED DATA (CSV)/'):
    """Load and clean population data"""

    try:
        # Find first file containing 'population' (case-insensitive)
        population_files = [
            f for f in os.listdir(data_path)
            if 'population' in f.lower()
        ]

        if not population_files:
            return None

        pop_file = os.path.join(data_path, population_files[0])
        pop_df = pd.read_csv(pop_file)

        # Standardize county names
        if 'County' in pop_df.columns:
            pop_df['County'] = (
                pop_df['County']
                .astype(str)
                .str.strip()
                .str.upper()
            )

        # Convert numeric columns safely (handles commas)
        for col in pop_df.columns:
            pop_df[col] = (
                pop_df[col]
                .astype(str)
                .str.replace(',', '', regex=False)
            )

            pop_df[col] = pd.to_numeric(pop_df[col], errors='ignore')

        return pop_df

    except Exception as e:
        st.error(f"Error loading population data: {e}")
        return None

def create_facility_location_viewer(df, pop_df=None, lat_col=None, lon_col=None, 
                                    county_col=None, selected_county=None):
    """Create interactive facility location viewer with color-coded markers"""
    
    if lat_col is None or lon_col is None:
        # Try to detect coordinate columns
        for col in df.columns:
            if 'lat' in col.lower():
                lat_col = col
            if 'lon' in col.lower() or 'lng' in col.lower():
                lon_col = col
        
        if lat_col is None or lon_col is None:
            return None
    
    # Filter for geocoded data
    geo_df = df.dropna(subset=[lat_col, lon_col]).copy()
    
    if len(geo_df) == 0:
        return None
    
    # Filter by county if specified
    if selected_county and county_col and county_col in geo_df.columns:
        geo_df = geo_df[geo_df[county_col] == selected_county]
    
    # Create color map for KEPH levels
    color_map = {
        'Level 1': '#FF4B4B',  # Red
        'Level 2': '#FF8A4B',  # Orange
        'Level 3': '#FFB84B',  # Yellow
        'Level 4': '#4B9EFF',  # Blue
        'Level 5': '#6B4BFF',  # Purple
        'Level 6': '#9E4BFF',  # Violet
        'Mixed': '#4BFFB8',    # Green
        'Unknown': '#808080'    # Gray
    }
    
    # Create the map
    fig = go.Figure()
    
    # Add facility markers by KEPH level
    for keph_level, color in color_map.items():
        type_df = geo_df[geo_df['keph_level'] == keph_level]
        if len(type_df) > 0:
            fig.add_trace(go.Scattermapbox(
                lat=type_df[lat_col],
                lon=type_df[lon_col],
                mode='markers',
                marker=dict(
                    size=10,
                    color=color,
                    opacity=0.7
                ),
                name=keph_level,
                text=type_df.apply(lambda row: create_hover_text(row, county_col), axis=1),
                hoverinfo='text'
            ))
    
    # Center map
    if selected_county and county_col:
        county_data = geo_df[geo_df[county_col] == selected_county]
        if len(county_data) > 0:
            center_lat = county_data[lat_col].mean()
            center_lon = county_data[lon_col].mean()
        else:
            center_lat, center_lon = -1.286389, 36.817223
    else:
        center_lat, center_lon = -1.286389, 36.817223
    
    fig.update_layout(
        mapbox=dict(
            style='carto-positron',
            center=dict(lat=center_lat, lon=center_lon),
            zoom=6 if not selected_county else 8
        ),
        height=800,
        margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(169,169,169)"
        ),
        title="Facility Locations by KEPH Level"
    )
    
    return fig

def create_hover_text(row, county_col):
    """Create hover text for facilities"""
    text = f"<b>{row.get('Facility Name', 'Unknown')}</b><br>"
    text += f"KEPH Level: {row.get('keph_level', 'Unknown')}<br>"
    text += f"Ownership: {row.get('ownership', 'Unknown')}<br>"
    if county_col and county_col in row:
        text += f"County: {row[county_col]}<br>"
    if 'latitude' in row and 'longitude' in row:
        text += f"Coordinates: {row['latitude']:.4f}, {row['longitude']:.4f}"
    return text

def create_county_drilldown(df, pop_df, county_col, selected_county):
    """Create detailed county-level analysis"""
    
    if selected_county is None:
        return None
    
    # Filter for selected county
    county_df = df[df[county_col] == selected_county].copy()
    
    # Get population data for the county
    county_pop = pop_df[pop_df['County'] == selected_county].iloc[0] if pop_df is not None and selected_county in pop_df['County'].values else None
    
    # Create subplot figure
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Facilities by KEPH Level', 'Facilities by Ownership',
                       'Population Demographics', 'Facility Distribution'),
        specs=[[{'type': 'pie'}, {'type': 'bar'}],
               [{'type': 'bar'}, {'type': 'pie'}]],
        vertical_spacing=0.15,
        horizontal_spacing=0.15
    )
    
    # 1. KEPH Level distribution pie chart
    keph_counts = county_df['keph_level'].value_counts()
    fig.add_trace(
        go.Pie(
            labels=keph_counts.index,
            values=keph_counts.values,
            name="KEPH Level",
            marker=dict(colors=px.colors.qualitative.Set3),
            textinfo='percent+label',
            hoverinfo='label+percent+value'
        ),
        row=1, col=1
    )
    
    # 2. Ownership distribution bar chart
    ownership_counts = county_df['ownership'].value_counts()
    fig.add_trace(
        go.Bar(
            x=ownership_counts.index,
            y=ownership_counts.values,
            name="Ownership",
            marker_color='lightblue',
            text=ownership_counts.values,
            textposition='outside'
        ),
        row=1, col=2
    )
    
    # 3. Population demographics
    if county_pop is not None:
        demographics = ['Male', 'Female', 'Intersex']
        values = [county_pop.get('Male', 0), 
                 county_pop.get('Female', 0), 
                 county_pop.get('Intersex', 0)]
        
        fig.add_trace(
            go.Bar(
                x=demographics,
                y=values,
                name="Population",
                marker_color=['#4B9EFF', '#FF9E4B', '#9E4BFF'],
                text=[f"{v:,.0f}" for v in values],
                textposition='outside'
            ),
            row=2, col=1
        )
    
    # 4. Facility type distribution
    category_counts = county_df['facility_category'].value_counts().head(5)
    fig.add_trace(
        go.Pie(
            labels=category_counts.index,
            values=category_counts.values,
            name="Facility Types",
            marker=dict(colors=px.colors.qualitative.Pastel),
            textinfo='percent+label',
            hole=0.3
        ),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        height=1000,
        showlegend=False,
        title_text=f"📊 Detailed Analysis: {selected_county} County",
        title_x=0.5
    )
    
    # Update axes
    fig.update_xaxes(title_text="Ownership Type", row=1, col=2)
    fig.update_yaxes(title_text="Number of Facilities", row=1, col=2)
    fig.update_xaxes(title_text="Demographics", row=2, col=1)
    fig.update_yaxes(title_text="Population", row=2, col=1)
    
    return fig

def create_county_comparison(df, pop_df, county_col, selected_counties):
    """Create county comparison dashboard"""
    
    if len(selected_counties) < 2:
        return None
    
    comparison_data = []
    
    for county in selected_counties:
        county_df = df[df[county_col] == county]
        pop_row = pop_df[pop_df['County'] == county].iloc[0] if county in pop_df['County'].values else None
        
        # Get KEPH level breakdown
        keph_levels = county_df['keph_level'].value_counts().to_dict()
        
        data = {
            'County': county,
            'Total Facilities': len(county_df),
            'Facility Types': county_df['facility_category'].nunique(),
            'Geocoded': county_df['latitude'].notna().sum() if 'latitude' in county_df.columns else 0,
            'Level 1': keph_levels.get('Level 1', 0),
            'Level 2': keph_levels.get('Level 2', 0),
            'Level 3': keph_levels.get('Level 3', 0),
            'Level 4': keph_levels.get('Level 4', 0),
            'Level 5': keph_levels.get('Level 5', 0),
            'Level 6': keph_levels.get('Level 6', 0)
        }
        
        if pop_row is not None:
            data.update({
                'Population': pop_row.get('Total', 0),
                'Population Density': pop_row.get('Population Density', 0),
                'Households': pop_row.get('Households', 0),
                'Facilities per 10k People': round(len(county_df) / (pop_row.get('Total', 1) / 10000), 2)
            })
        
        comparison_data.append(data)
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # Create comparison charts
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Total Facilities by County', 'Facilities per 10k Population',
                       'KEPH Level Distribution', 'Geocoding Success Rate'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}],
               [{'type': 'bar'}, {'type': 'bar'}]]
    )
    
    # Total facilities
    fig.add_trace(
        go.Bar(
            x=comparison_df['County'],
            y=comparison_df['Total Facilities'],
            name='Total Facilities',
            marker_color='royalblue',
            text=comparison_df['Total Facilities'],
            textposition='outside'
        ),
        row=1, col=1
    )
    
    # Facilities per 10k people
    if 'Facilities per 10k People' in comparison_df.columns:
        fig.add_trace(
            go.Bar(
                x=comparison_df['County'],
                y=comparison_df['Facilities per 10k People'],
                name='Per 10k People',
                marker_color='crimson',
                text=comparison_df['Facilities per 10k People'],
                textposition='outside',
                texttemplate='%{text:.2f}'
            ),
            row=1, col=2
        )
    
    # KEPH Level distribution (stacked bar)
    keph_cols = ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5', 'Level 6']
    available_keph = [col for col in keph_cols if col in comparison_df.columns]
    
    for level in available_keph:
        fig.add_trace(
            go.Bar(
                x=comparison_df['County'],
                y=comparison_df[level],
                name=level,
                text=comparison_df[level]
            ),
            row=2, col=1
        )
    
    # Geocoding success rate
    if 'Geocoded' in comparison_df.columns:
        success_rate = (comparison_df['Geocoded'] / comparison_df['Total Facilities'] * 100).round(1)
        fig.add_trace(
            go.Bar(
                x=comparison_df['County'],
                y=success_rate,
                name='Success Rate',
                marker_color='green',
                text=success_rate,
                textposition='outside',
                texttemplate='%{text}%'
            ),
            row=2, col=2
        )
    
    # Update layout
    fig.update_layout(
        height=1200,
        barmode='group' if len(available_keph) > 0 else 'relative',
        title_text="📊 County Comparison Dashboard",
        title_x=0.5,
        showlegend=True,
        legend=dict(
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Update axes
    fig.update_xaxes(title_text="County", row=1, col=1)
    fig.update_xaxes(title_text="County", row=1, col=2)
    fig.update_xaxes(title_text="County", row=2, col=1)
    fig.update_xaxes(title_text="County", row=2, col=2)
    
    fig.update_yaxes(title_text="Number of Facilities", row=1, col=1)
    fig.update_yaxes(title_text="Facilities per 10k", row=1, col=2)
    fig.update_yaxes(title_text="Number of Facilities", row=2, col=1)
    fig.update_yaxes(title_text="Success Rate (%)", row=2, col=2)
    
    return fig, comparison_df

def save_custom_view(df, filters, view_name):
    """Save current filter configuration"""
    view_config = {
        'name': view_name,
        'timestamp': datetime.now().isoformat(),
        'filters': filters,
        'record_count': len(df)
    }
    
    if 'saved_views' not in st.session_state:
        st.session_state.saved_views = {}
    
    st.session_state.saved_views[view_name] = view_config
    return True

def main():
    # Header
    logo = st.image('../APP/ASSETS/PNGs/metrics-svgrepo-com.png', width= 120)
    st.markdown('<h1 class="main-header">Kenya Health Facilities & Population Dashboard</h1>', 
                unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("../APP/ASSETS/PNGs/resources-svgrepo-com.png", 
                 width=120)
        
        expander_logo = 'ASSETS/PNGs/controls-svgrepo-com.png'
        with st.markdown(f"## {expander_logo} Dashboard Controls"):
            st.image(expander_logo, width= 50)
        
        # Data loading

        with st.expander("Data Management", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Load Data", use_container_width=True, key="load_data"):
                    with st.spinner("Loading facility data..."):
                        df = load_all_datasets()
                        if df is not None:
                            st.session_state.dashboard_data = df
                            
                            # Load population data
                            pop_df = load_population_data()
                            if pop_df is not None:
                                st.session_state.population_data = pop_df
                                st.success(f"Loaded {len(pop_df)} counties population data")
                            
                            st.success(f"Loaded {len(df):,} facilities!")
            
            with col2:
                if st.button("Clear", use_container_width=True, key="clear_data"):
                    st.session_state.dashboard_data = None
                    st.session_state.population_data = None
                    st.session_state.filtered_data = None
                    st.rerun()
        
        # Filters
        if st.session_state.dashboard_data is not None:
            df = st.session_state.dashboard_data
            
            filter_icon = '../APP/ASSETS/PNGs/filter-svgrepo-com.png'
            with st.expander(F"{filter_icon} Filters", expanded=True):
                # Expander icon
                st.image(filter_icon, width=50)
                # Detect county column
                county_col = None
                for col in df.columns:
                    if 'county' in col.lower():
                        county_col = col
                        break
                
                # County filter
                if county_col:
                    counties = ['All'] + sorted(df[county_col].dropna().unique().tolist())
                    selected_counties = st.multiselect(f" Select Counties", options=counties[1:],default=[],key="county_filter", help="Filter by one or more counties")
                
                
                else:
                    selected_counties = []
                
                # KEPH Level filter
                if 'keph_level' in df.columns:
                    keph_levels = ['All'] + sorted(df['keph_level'].dropna().unique().tolist())
                    selected_keph = st.multiselect(
                        "KEPH Level",
                        options=keph_levels[1:],
                        default=[],
                        key="keph_filter"
                    )
                else:
                    selected_keph = []
                
                # Ownership filter
                if 'ownership' in df.columns:
                    ownership_types = ['All'] + sorted(df['ownership'].dropna().unique().tolist())
                    selected_ownership = st.multiselect(
                        "Ownership Type",
                        options=ownership_types[1:],
                        default=[],
                        key="ownership_filter"
                    )
                else:
                    selected_ownership = []
                
                # Apply filters
                if st.button("✅ Apply Filters", use_container_width=True, key="apply_filters"):
                    filtered_df = df.copy()
                    
                    if selected_counties and county_col:
                        filtered_df = filtered_df[filtered_df[county_col].isin(selected_counties)]
                    
                    if selected_keph:
                        filtered_df = filtered_df[filtered_df['keph_level'].isin(selected_keph)]
                    
                    if selected_ownership:
                        filtered_df = filtered_df[filtered_df['ownership'].isin(selected_ownership)]
                    
                    st.session_state.filtered_data = filtered_df
                    st.success(f"Filtered to {len(filtered_df):,} facilities")
    
    # Main content
    if st.session_state.dashboard_data is not None:
        df = st.session_state.filtered_data if st.session_state.filtered_data is not None else st.session_state.dashboard_data
        pop_df = st.session_state.population_data
        
        # Detect county column
        county_col = None
        for col in df.columns:
            if 'county' in col.lower():
                county_col = col
                break
        
        # Create tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "🗺️ Facility Location Viewer", 
            "📊 County-Level Analysis",
            "📈 County Comparison",
            "📋 Data Explorer"
        ])
        
        with tab1:
            st.markdown('<h2 class="sub-header">Facility Location Viewer</h2>', 
                       unsafe_allow_html=True)
            
            if county_col:
                drill_down_county = st.selectbox(
                    "🔍 Drill down to specific county (optional)",
                    options=['All Counties'] + sorted(df[county_col].dropna().unique().tolist()),
                    key="drilldown_select"
                )
                selected_county = None if drill_down_county == 'All Counties' else drill_down_county
            else:
                selected_county = None
            
            fig = create_facility_location_viewer(
                df, pop_df, 
                county_col=county_col,
                selected_county=selected_county
            )
            
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("""
                **📍 Map Features:**
                - **Colored markers** indicate KEPH Level (1-6)
                - **Hover over markers** for facility details
                - **Use county dropdown** to focus on specific areas
                """)
            else:
                st.warning("No geocoded facilities available. Please run geocoding tool first.")
        
        with tab2:
            st.markdown('<h2 class="sub-header">County-Level Analysis</h2>', 
                       unsafe_allow_html=True)
            
            if county_col and pop_df is not None:
                # County selector
                counties = sorted(df[county_col].dropna().unique().tolist())
                selected_county_detail = st.selectbox(
                    "Select County for Detailed Analysis",
                    options=counties,
                    key="county_detail"
                )
                
                # Display county metrics
                county_df = df[df[county_col] == selected_county_detail]
                county_pop = pop_df[pop_df['County'] == selected_county_detail].iloc[0] if selected_county_detail in pop_df['County'].values else None
                
                # Metrics row
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Facilities", len(county_df))
                with col2:
                    st.metric("KEPH Levels", county_df['keph_level'].nunique())
                with col3:
                    if county_pop is not None:
                        total_pop = county_pop.get('Total')
                        
                        if pd.notna(total_pop):
                            st.metric("Population", f"{total_pop:,.0f}")
                        else:
                            st.metric("Population", "N/A")
                    else:
                        st.metric("Population", "N/A")
                with col4:
                    if county_pop is not None and not pd.isna(county_pop.get('Population Density')):
                        density = county_pop['Population Density']
                        st.metric("Population Density\n", f"{density:.1f}/km²")
                    else:
                        st.metric("Population Density", "N/A")
                
                # Detailed analysis chart
                fig = create_county_drilldown(df, pop_df, county_col, selected_county_detail)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                
                # Facility list
                with st.expander("View Facilities in this County"):
                    display_cols = ['Facility Name', 'keph_level', 'ownership', 'facility_category']
                    display_cols = [col for col in display_cols if col in county_df.columns]
                    
                    if county_col in county_df.columns:
                        st.dataframe(
                            county_df[display_cols].head(50),
                            use_container_width=True,
                            height=300
                        )
            else:
                st.info("County or population data not available")
        
        with tab3:
            st.markdown('<h2 class="sub-header">County Comparison</h2>', 
                       unsafe_allow_html=True)
            
            if county_col and pop_df is not None:
                counties = sorted(df[county_col].dropna().unique().tolist())
                
                compare_counties = st.multiselect(
                    "Select Counties to Compare (minimum 2)",
                    options=counties,
                    default=counties[:3] if len(counties) >= 3 else None,
                    key="compare_counties"
                )
                
                if len(compare_counties) >= 2:
                    fig, comparison_df = create_county_comparison(df, pop_df, county_col, compare_counties)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    
                    st.subheader("Comparison Data")
                    st.dataframe(comparison_df, use_container_width=True)
                    
                    csv = comparison_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Comparison",
                        data=csv,
                        file_name=f"county_comparison_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )

                else:
                    st.info("Please select at least 2 counties to compare")
            else:
                st.info("County or population data not available")
        
        with tab4:
            st.markdown('<h2 class="sub-header">Data Explorer</h2>', 
                       unsafe_allow_html=True)
            
            all_cols = df.columns.tolist()
            default_cols = ['Facility Name', 'keph_level', 'ownership', 'facility_category']
            if county_col:
                default_cols.append(county_col)
            default_cols = [col for col in default_cols if col in all_cols]
            
            selected_cols = st.multiselect(
                "Select columns to display",
                options=all_cols,
                default=default_cols,
                key="explorer_cols"
            )
            
            if selected_cols:
                st.dataframe(
                    df[selected_cols].head(100),
                    use_container_width=True,
                    height=500
                )
                
                st.caption(f"Showing first 100 of {len(df):,} records")
                
                csv = df[selected_cols].to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Visible Data",
                    data=csv,
                    file_name=f"facility_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    
    else:
        # Welcome screen
        st.markdown("""
        <div style="text-align: center; padding: 3rem;">
            <h2>👋 Welcome to the Kenya Health Facilities & Population Dashboard</h2>
            <p style="font-size: 1.2rem; color: #666; margin: 2rem;">
                Click the <b>'Load Data'</b> button in the sidebar to get started.
            </p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()