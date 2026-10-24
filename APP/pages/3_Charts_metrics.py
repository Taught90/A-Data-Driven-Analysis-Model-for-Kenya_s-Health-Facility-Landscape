from pathlib import Path
from datetime import datetime
import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Kenya Health Facilities & Population Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_FACILITY_PATH = BASE_DIR / "APP" / "CLEANED DATA (CSV)" / "GEOCODED"
DEFAULT_POPULATION_PATH = BASE_DIR / "APP" / "CLEANED DATA (CSV)"
ASSET_PATH = BASE_DIR / "APP" / "ASSETS" / "PNGs"

# enhanced_dashboard_fixed.py is inside APP/pages/
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent.parent

DEFAULT_FACILITY_PATH = (
    "APP/CLEANED DATA (CSV)/GEOCODED"
)

DEFAULT_POPULATION_PATH = (
    "APP/CLEANED DATA (CSV)"
)

ASSET_PATH = "APP/ASSETS/PNGs"


DATASETS = [
    "CONTRACTED-FACILITES-REHABILITATION",
    "CONTRACTED-FACILITIES-COMMUNITY-HOSP",
    "CONTRACTED-FACILITIES-INSTITUTIONAL",
    "CONTRACTED-FACILITIES-COUNTY-GOVT",
    "CONTRACTED-FACILITIES-FBOs",
    "CONTRACTED-FACILITIES-GOVERNMENT-OF-KENYA",
    "CONTRACTED-FACILITIES-NGOs",
    "CONTRACTED-FACILITIES-PRIVATE",
    "SHA-FACILITIES-PAYMENT-ANALYSIS",
]

FACILITY_METADATA = {
    "REHABILITATION": ("REHABILITATION", "Level 3"),
    "COMMUNITY-HOSP": ("COMMUNITY HOSPITAL", "Level 2"),
    "INSTITUTIONAL": ("INSTITUTIONAL", "Unknown"),
    "COUNTY-GOVT": ("COUNTY GOVERNMENT", "Level 4"),
    "FBOs": ("FAITH-BASED ORGANIZATION", "Level 2"),
    "GOVERNMENT-OF-KENYA": ("NATIONAL GOVERNMENT", "Level 4"),
    "NGOs": ("NON-GOVERNMENTAL ORGANIZATION", "Level 2"),
    "PRIVATE": ("PRIVATE", "Level 3"),
    "SHA-FACILITIES-PAYMENT-ANALYSIS": ("Mixed", "Mixed"),
}

KEPH_COLORS = {
    "Level 1": "#E45756",
    "Level 2": "#F58518",
    "Level 3": "#EEC643",
    "Level 4": "#4C78A8",
    "Level 5": "#7A5195",
    "Level 6": "#B279A2",
    "Mixed": "#54A24B",
    "Unknown": "#808080",
}


# ---------------------------------------------------------------------------
# Styling and session state
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
      .main-header {
        font-size: 2.25rem;
        color: #1E88E5;
        font-weight: 700;
        margin-bottom: .75rem;
      }
      .sub-header {
        font-size: 1.45rem;
        color: #0D47A1;
        margin-top: .75rem;
        margin-bottom: .75rem;
      }
      div[data-testid="stMetric"] {
        background: #f4f7fb;
        border: 1px solid #e2e8f0;
        padding: 12px;
        border-radius: 10px;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

for key, default in {
    "dashboard_data": None,
    "population_data": None,
    "filtered_data": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------
def find_column(df: pd.DataFrame, candidates) -> str | None:
    """Return the first column matching a candidate name or substring."""
    if df is None or df.empty:
        return None

    normalized = {str(col).strip().lower(): col for col in df.columns}
    for candidate in candidates:
        if candidate.lower() in normalized:
            return normalized[candidate.lower()]

    for col in df.columns:
        name = str(col).strip().lower()
        if any(candidate.lower() in name for candidate in candidates):
            return col
    return None


def detect_county_column(df: pd.DataFrame) -> str | None:
    """Prefer common county column names, then fall back to a county substring."""
    if df is None or df.empty:
        return None
    for candidate in ("County", "county", "County Name", "county_name"):
        if candidate in df.columns:
            return candidate
    return find_column(df, ["county"])


def detect_coordinate_columns(df: pd.DataFrame):
    """Detect latitude and longitude columns without assuming exact casing."""
    lat_col = find_column(df, ["latitude", "lat"])
    lon_col = find_column(df, ["longitude", "long", "lon", "lng"])
    return lat_col, lon_col


def normalize_county(value) -> str:
    """Normalize county labels for case-insensitive joins."""
    if pd.isna(value):
        return ""
    return " ".join(str(value).strip().upper().split())


def facility_category_from_dataset(dataset_name: str) -> str:
    """Convert a dataset filename stem to its category."""
    prefix = "CONTRACTED-FACILITIES-"
    misspelled_prefix = "CONTRACTED-FACILITES-"
    if dataset_name.startswith(prefix):
        return dataset_name[len(prefix):]
    if dataset_name.startswith(misspelled_prefix):
        return dataset_name[len(misspelled_prefix):]
    return dataset_name


def load_all_datasets(data_path=DEFAULT_FACILITY_PATH) -> pd.DataFrame | None:
    """Load and combine all available facility CSV files."""
    data_path = Path(data_path)
    if not data_path.exists():
        st.error(f"Facility data folder not found: {data_path}")
        return None

    all_data = []
    progress = st.progress(0, text="Preparing to load facility datasets...")

    for index, dataset in enumerate(DATASETS, start=1):
        file_path = data_path / f"{dataset}.csv"
        try:
            if file_path.exists():
                frame = pd.read_csv(file_path, low_memory=False)
                if frame.empty:
                    st.warning(f"{file_path.name} contains no records.")
                    continue

                category = facility_category_from_dataset(dataset)
                ownership, keph_level = FACILITY_METADATA.get(
                    category, ("Unknown", "Unknown")
                )

                frame["facility_category"] = category
                frame["ownership"] = ownership
                frame["keph_level"] = keph_level
                frame["data_source"] = dataset

                name_col = find_column(
                    frame, ["facility name", "facility", "hospital name", "hospital", "name"]
                )
                if name_col:
                    frame["Facility Name"] = frame[name_col].fillna("Unknown").astype(str)
                else:
                    frame["Facility Name"] = [
                        f"{category} facility {row_num + 1}"
                        for row_num in range(len(frame))
                    ]

                # Standardize common coordinate columns when present.
                lat_col, lon_col = detect_coordinate_columns(frame)
                if lat_col:
                    frame["latitude"] = pd.to_numeric(frame[lat_col], errors="coerce")
                if lon_col:
                    frame["longitude"] = pd.to_numeric(frame[lon_col], errors="coerce")

                county_col = detect_county_column(frame)
                if county_col and county_col != "County":
                    frame["County"] = frame[county_col]

                all_data.append(frame)
            else:
                st.warning(f"Dataset not found (skipped): {file_path}")
        except (OSError, pd.errors.ParserError, UnicodeDecodeError, ValueError) as exc:
            st.warning(f"Could not load {file_path.name}: {exc}")
        finally:
            progress.progress(index / len(DATASETS), text=f"Checked {dataset}")

    progress.empty()
    if not all_data:
        st.error("No facility datasets were loaded. Check the folder and CSV filenames.")
        return None

    combined = pd.concat(all_data, ignore_index=True, sort=False)

    # Normalize known fields to avoid type issues during filtering and plotting.
    if "keph_level" not in combined:
        combined["keph_level"] = "Unknown"
    if "ownership" not in combined:
        combined["ownership"] = "Unknown"
    if "facility_category" not in combined:
        combined["facility_category"] = "Unknown"

    return combined


def load_population_data(data_path=DEFAULT_POPULATION_PATH) -> pd.DataFrame | None:
    """Load the first CSV with 'population' in its filename."""
    data_path = Path(data_path)
    if not data_path.exists():
        st.warning(f"Population data folder not found: {data_path}")
        return None

    population_files = sorted(
        path for path in data_path.iterdir()
        if path.is_file() and "population" in path.name.lower()
        and path.suffix.lower() == ".csv"
    )
    if not population_files:
        st.warning(f"No CSV with 'population' in its filename was found in {data_path}.")
        return None

    try:
        pop_df = pd.read_csv(population_files[0], low_memory=False)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        st.error(f"Could not load population data: {exc}")
        return None

    county_col = detect_county_column(pop_df)
    if county_col and county_col != "County":
        pop_df = pop_df.rename(columns={county_col: "County"})
    if "County" in pop_df:
        pop_df["County"] = pop_df["County"].astype(str).str.strip().str.upper()
        pop_df["County_Upper"] = pop_df["County"].map(normalize_county)

    numeric_columns = [
        "Total", "Male", "Female", "Intersex", "Households",
        "Average_HouseHold_Size", "LandArea", "Population Density",
    ]
    for col in numeric_columns:
        if col in pop_df:
            pop_df[col] = pd.to_numeric(pop_df[col], errors="coerce")

    st.success(f"Loaded population data: {len(pop_df):,} rows.")
    return pop_df


def get_county_population(pop_df: pd.DataFrame | None, county_name: str):
    """Return the matching population row, or None if unavailable."""
    if pop_df is None or pop_df.empty or "County" not in pop_df:
        return None

    if "County_Upper" not in pop_df:
        pop_df = pop_df.copy()
        pop_df["County_Upper"] = pop_df["County"].map(normalize_county)

    matches = pop_df[pop_df["County_Upper"] == normalize_county(county_name)]
    return matches.iloc[0] if not matches.empty else None


def create_hover_text(row: pd.Series, county_col: str | None) -> str:
    """Build safe hover text for a facility marker."""
    parts = [
        f"<b>{row.get('Facility Name', 'Unknown')}</b>",
        f"KEPH Level: {row.get('keph_level', 'Unknown')}",
        f"Ownership: {row.get('ownership', 'Unknown')}",
    ]
    if county_col and county_col in row.index and pd.notna(row[county_col]):
        parts.append(f"County: {row[county_col]}")

    lat = row.get("latitude")
    lon = row.get("longitude")
    if pd.notna(lat) and pd.notna(lon):
        try:
            parts.append(f"Coordinates: {float(lat):.4f}, {float(lon):.4f}")
        except (TypeError, ValueError):
            pass
    return "<br>".join(parts)


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def create_facility_location_viewer(
    df: pd.DataFrame,
    county_col: str | None = None,
    selected_county: str | None = None,
):
    """Create a Plotly map of facilities with valid coordinates."""
    if df is None or df.empty:
        return None

    lat_col, lon_col = detect_coordinate_columns(df)
    if not lat_col or not lon_col:
        return None

    geo_df = df.copy()
    geo_df[lat_col] = pd.to_numeric(geo_df[lat_col], errors="coerce")
    geo_df[lon_col] = pd.to_numeric(geo_df[lon_col], errors="coerce")
    geo_df = geo_df.dropna(subset=[lat_col, lon_col])

    # Keep only plausible longitude/latitude values.
    geo_df = geo_df[
        geo_df[lat_col].between(-90, 90)
        & geo_df[lon_col].between(-180, 180)
    ]
    if selected_county and county_col and county_col in geo_df:
        geo_df = geo_df[
            geo_df[county_col].map(normalize_county) == normalize_county(selected_county)
        ]
    if geo_df.empty:
        return None

    geo_df["_hover"] = geo_df.apply(
        lambda row: create_hover_text(row, county_col), axis=1
    )

    # Use the current Plotly map trace API.
    fig = go.Figure()
    level_values = geo_df["keph_level"].fillna("Unknown").astype(str)
    for level in sorted(level_values.unique()):
        level_df = geo_df[level_values == level]
        fig.add_trace(
            go.Scattermap(
                lat=level_df[lat_col],
                lon=level_df[lon_col],
                mode="markers",
                marker=dict(
                    size=9,
                    color=KEPH_COLORS.get(level, KEPH_COLORS["Unknown"]),
                    opacity=0.75,
                ),
                name=level,
                text=level_df["_hover"],
                hovertemplate="%{text}<extra></extra>",
            )
        )

    center_lat = float(geo_df[lat_col].mean())
    center_lon = float(geo_df[lon_col].mean())
    fig.update_layout(
        map=dict(
            style="open-street-map",
            center=dict(lat=center_lat, lon=center_lon),
            zoom=6 if selected_county else 5,
        ),
        title="Facility Locations by KEPH Level",
        height=720,
        margin=dict(l=0, r=0, t=55, b=0),
        legend=dict(
            yanchor="top", y=0.99, xanchor="left", x=0.01,
            bgcolor="rgba(255,255,255,0.85)",
        ),
    )
    return fig


def create_county_drilldown(
    df: pd.DataFrame,
    pop_df: pd.DataFrame | None,
    county_col: str,
    selected_county: str,
):
    """Create a four-panel county summary."""
    county_df = df[
        df[county_col].map(normalize_county) == normalize_county(selected_county)
    ].copy()
    if county_df.empty:
        return None

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Facilities by KEPH Level",
            "Facilities by Ownership",
            "Population Demographics",
            "Facilities by Category",
        ),
        specs=[[{"type": "pie"}, {"type": "bar"}], [{"type": "bar"}, {"type": "pie"}]],
        vertical_spacing=0.16,
        horizontal_spacing=0.12,
    )

    keph_counts = county_df["keph_level"].fillna("Unknown").value_counts()
    if not keph_counts.empty:
        fig.add_trace(
            go.Pie(labels=keph_counts.index, values=keph_counts.values,
                   name="KEPH Level", textinfo="percent+label"),
            row=1, col=1,
        )

    ownership_counts = county_df["ownership"].fillna("Unknown").value_counts()
    if not ownership_counts.empty:
        fig.add_trace(
            go.Bar(x=ownership_counts.index, y=ownership_counts.values,
                   name="Ownership", text=ownership_counts.values, textposition="outside"),
            row=1, col=2,
        )

    pop_row = get_county_population(pop_df, selected_county)
    demographic_cols = ["Male", "Female", "Intersex"]
    if pop_row is not None:
        labels, values = [], []
        for col in demographic_cols:
            if col in pop_row.index and pd.notna(pop_row[col]):
                labels.append(col)
                values.append(float(pop_row[col]))
        if values:
            fig.add_trace(
                go.Bar(x=labels, y=values, name="Population",
                       text=[f"{value:,.0f}" for value in values],
                       textposition="outside"),
                row=2, col=1,
            )

    category_counts = county_df["facility_category"].fillna("Unknown").value_counts().head(8)
    if not category_counts.empty:
        fig.add_trace(
            go.Pie(labels=category_counts.index, values=category_counts.values,
                   name="Facility Category", hole=0.35, textinfo="percent+label"),
            row=2, col=2,
        )

    fig.update_layout(
        height=850,
        title_text=f"Detailed Analysis: {selected_county} County",
        title_x=0.5,
        showlegend=False,
    )
    fig.update_xaxes(title_text="Ownership Type", row=1, col=2)
    fig.update_yaxes(title_text="Number of Facilities", row=1, col=2)
    fig.update_xaxes(title_text="Demographic Group", row=2, col=1)
    fig.update_yaxes(title_text="Population", row=2, col=1)
    return fig


def create_county_comparison(
    df: pd.DataFrame,
    pop_df: pd.DataFrame | None,
    county_col: str,
    selected_counties: list[str],
):
    """Create county comparison charts and a comparison table."""
    if len(selected_counties) < 2:
        return None, None

    rows = []
    for county in selected_counties:
        county_df = df[
            df[county_col].map(normalize_county) == normalize_county(county)
        ]
        lat_col, lon_col = detect_coordinate_columns(county_df)
        geocoded_count = 0
        if lat_col and lon_col:
            lat = pd.to_numeric(county_df[lat_col], errors="coerce")
            lon = pd.to_numeric(county_df[lon_col], errors="coerce")
            geocoded_count = int((lat.notna() & lon.notna()).sum())

        level_counts = county_df["keph_level"].fillna("Unknown").value_counts()
        pop_row = get_county_population(pop_df, county)

        total_population = None
        if pop_row is not None and "Total" in pop_row.index:
            value = pd.to_numeric(pd.Series([pop_row["Total"]]), errors="coerce").iloc[0]
            if pd.notna(value) and value > 0:
                total_population = float(value)

        total_facilities = len(county_df)
        row = {
            "County": county,
            "Total Facilities": total_facilities,
            "Facility Types": county_df["facility_category"].nunique(),
            "Geocoded": geocoded_count,
            "Geocoding Success Rate (%)": round(geocoded_count / total_facilities * 100, 1)
                if total_facilities else 0.0,
            "Level 1": int(level_counts.get("Level 1", 0)),
            "Level 2": int(level_counts.get("Level 2", 0)),
            "Level 3": int(level_counts.get("Level 3", 0)),
            "Level 4": int(level_counts.get("Level 4", 0)),
            "Level 5": int(level_counts.get("Level 5", 0)),
            "Level 6": int(level_counts.get("Level 6", 0)),
            "Population": total_population,
            "Population Density": None,
            "Households": None,
            "Land Area (km²)": None,
            "Avg Household Size": None,
            "Facilities per 10k People": (
                round(total_facilities / (total_population / 10000), 2)
                if total_population else None
            ),
        }
        if pop_row is not None:
            for output_col, source_col in [
                ("Population Density", "Population Density"),
                ("Households", "Households"),
                ("Land Area (km²)", "LandArea"),
                ("Avg Household Size", "Average_HouseHold_Size"),
            ]:
                if source_col in pop_row.index and pd.notna(pop_row[source_col]):
                    row[output_col] = pop_row[source_col]
        rows.append(row)

    comparison_df = pd.DataFrame(rows)
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Total Facilities by County",
            "Facilities per 10,000 People",
            "KEPH Level Distribution",
            "Geocoding Success Rate",
        ),
    )

    fig.add_trace(
        go.Bar(x=comparison_df["County"], y=comparison_df["Total Facilities"],
               name="Total Facilities", text=comparison_df["Total Facilities"],
               textposition="outside"),
        row=1, col=1,
    )
    fig.add_trace(
        go.Bar(x=comparison_df["County"], y=comparison_df["Facilities per 10k People"],
               name="Facilities per 10k", text=comparison_df["Facilities per 10k People"],
               textposition="outside", hovertemplate="%{x}<br>%{y:.2f}<extra></extra>"),
        row=1, col=2,
    )

    for level in ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5", "Level 6"]:
        fig.add_trace(
            go.Bar(x=comparison_df["County"], y=comparison_df[level], name=level),
            row=2, col=1,
        )

    fig.add_trace(
        go.Bar(x=comparison_df["County"], y=comparison_df["Geocoding Success Rate (%)"],
               name="Geocoding Success Rate", text=comparison_df["Geocoding Success Rate (%)"],
               texttemplate="%{text}%", textposition="outside"),
        row=2, col=2,
    )
    fig.update_layout(
        height=900,
        title_text="County Comparison Dashboard",
        title_x=0.5,
        barmode="stack",
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1),
    )
    fig.update_yaxes(title_text="Facilities", row=1, col=1)
    fig.update_yaxes(title_text="Facilities per 10,000 people", row=1, col=2)
    fig.update_yaxes(title_text="Facilities", row=2, col=1)
    fig.update_yaxes(title_text="Success rate (%)", row=2, col=2)
    return fig, comparison_df


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
def main():
    logo = ASSET_PATH / "metrics-svgrepo-com.png"
    sidebar_logo = ASSET_PATH / "resources-svgrepo-com.png"

    header_col1, header_col2 = st.columns([1, 8])
    with header_col1:
        if logo.exists():
            st.image(str(logo), width=90)
    with header_col2:
        st.markdown(
            '<h1 class="main-header">Kenya Health Facilities & Population Dashboard</h1>',
            unsafe_allow_html=True,
        )
        st.caption("Explore facility distribution, county populations, and geocoding coverage.")

    with st.sidebar:
        if sidebar_logo.exists():
            st.image(str(sidebar_logo), width=90)
        st.header("Dashboard Controls")

        with st.expander("Data Management", expanded=True):
            if st.button("Load / Reload Data", use_container_width=True, key="load_data"):
                with st.spinner("Loading datasets..."):
                    facilities = load_all_datasets()
                    population = load_population_data()
                    if facilities is not None:
                        st.session_state.dashboard_data = facilities
                        st.session_state.population_data = population
                        st.session_state.filtered_data = None
                        st.success(f"Loaded {len(facilities):,} facility records.")
                        st.rerun()

            if st.button("Clear Data", use_container_width=True, key="clear_data"):
                st.session_state.dashboard_data = None
                st.session_state.population_data = None
                st.session_state.filtered_data = None
                for key in ["county_filter", "keph_filter", "ownership_filter"]:
                    st.session_state.pop(key, None)
                st.rerun()

        base_df = st.session_state.dashboard_data
        if base_df is not None:
            county_col_for_filter = detect_county_column(base_df)
            with st.expander("Filters", expanded=True):
                county_options = (
                    sorted(base_df[county_col_for_filter].dropna().astype(str).unique())
                    if county_col_for_filter else []
                )
                keph_options = sorted(base_df["keph_level"].dropna().astype(str).unique())
                ownership_options = sorted(base_df["ownership"].dropna().astype(str).unique())

                selected_counties = st.multiselect(
                    "County", county_options, key="county_filter"
                )
                selected_keph = st.multiselect(
                    "KEPH Level", keph_options, key="keph_filter"
                )
                selected_ownership = st.multiselect(
                    "Ownership", ownership_options, key="ownership_filter"
                )

                if st.button("Apply Filters", use_container_width=True):
                    filtered = base_df.copy()
                    if selected_counties and county_col_for_filter:
                        filtered = filtered[
                            filtered[county_col_for_filter].astype(str).isin(selected_counties)
                        ]
                    if selected_keph:
                        filtered = filtered[filtered["keph_level"].astype(str).isin(selected_keph)]
                    if selected_ownership:
                        filtered = filtered[filtered["ownership"].astype(str).isin(selected_ownership)]
                    st.session_state.filtered_data = filtered
                    st.rerun()

                if st.button("Reset Filters", use_container_width=True):
                    st.session_state.filtered_data = None
                    for key in ["county_filter", "keph_filter", "ownership_filter"]:
                        st.session_state[key] = []
                    st.rerun()

    if st.session_state.dashboard_data is None:
        st.info("Load the facility and population CSV files using the sidebar to begin.")
        st.markdown(
            """
            **Expected folders**
            - `APP/CLEANED DATA (CSV)/GEOCODED/` — facility CSV files
            - `APP/CLEANED DATA (CSV)/` — a CSV whose filename contains `population`
            """
        )
        return

    all_df = st.session_state.dashboard_data
    df = st.session_state.filtered_data
    if df is None:
        df = all_df
    pop_df = st.session_state.population_data
    county_col = detect_county_column(df)

    st.caption(f"Showing {len(df):,} facility records out of {len(all_df):,} loaded records.")
    tab_map, tab_county, tab_compare, tab_explorer = st.tabs(
        ["Facility Location Viewer", "County-Level Analysis", "County Comparison", "Data Explorer"]
    )

    with tab_map:
        st.markdown('<h2 class="sub-header">Facility Location Viewer</h2>', unsafe_allow_html=True)
        if county_col:
            county_values = sorted(df[county_col].dropna().astype(str).unique())
            selected_county_map = st.selectbox(
                "Focus on a county",
                ["All Counties"] + county_values,
                key="map_county_select",
            )
            if selected_county_map == "All Counties":
                selected_county_map = None
        else:
            selected_county_map = None

        map_fig = create_facility_location_viewer(
            df, county_col=county_col, selected_county=selected_county_map
        )
        if map_fig is not None:
            st.plotly_chart(map_fig, use_container_width=True)
            st.caption("Marker colours represent the KEPH level assigned in the source-processing logic.")
        else:
            st.warning("No valid geocoded facilities were found. Check the latitude and longitude columns.")

    with tab_county:
        st.markdown('<h2 class="sub-header">County-Level Analysis</h2>', unsafe_allow_html=True)
        if not county_col:
            st.info("A county column was not found in the facility data.")
        elif df.empty:
            st.info("No facility records match the current filters.")
        else:
            counties = sorted(df[county_col].dropna().astype(str).unique())
            selected_county = st.selectbox("Select a county", counties, key="county_detail_select")
            county_df = df[df[county_col].map(normalize_county) == normalize_county(selected_county)]
            population_row = get_county_population(pop_df, selected_county)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Facilities", f"{len(county_df):,}")
            m2.metric("KEPH Levels", str(county_df["keph_level"].nunique()))
            total_pop = population_row.get("Total") if population_row is not None and "Total" in population_row.index else None
            density = population_row.get("Population Density") if population_row is not None and "Population Density" in population_row.index else None
            m3.metric("Population", f"{total_pop:,.0f}" if pd.notna(total_pop) else "N/A")
            m4.metric("Population Density", f"{density:,.1f}/km²" if pd.notna(density) else "N/A")

            detail_fig = create_county_drilldown(df, pop_df, county_col, selected_county)
            if detail_fig is not None:
                st.plotly_chart(detail_fig, use_container_width=True)

            with st.expander("View facilities in this county"):
                display_cols = [
                    col for col in ["Facility Name", county_col, "keph_level", "ownership", "facility_category"]
                    if col in county_df.columns
                ]
                st.dataframe(county_df[display_cols].head(100), use_container_width=True, height=350)

    with tab_compare:
        st.markdown('<h2 class="sub-header">County Comparison</h2>', unsafe_allow_html=True)
        if not county_col:
            st.info("A county column was not found in the facility data.")
        elif pop_df is None:
            st.info("Population data is unavailable. Load a population CSV to compare counties.")
        else:
            counties = sorted(df[county_col].dropna().astype(str).unique())
            defaults = counties[:3] if len(counties) >= 3 else counties
            compare_counties = st.multiselect(
                "Select at least two counties",
                options=counties,
                default=defaults,
                key="compare_counties",
            )
            if len(compare_counties) >= 2:
                compare_fig, comparison_df = create_county_comparison(
                    df, pop_df, county_col, compare_counties
                )
                if compare_fig is not None:
                    st.plotly_chart(compare_fig, use_container_width=True)
                st.dataframe(comparison_df, use_container_width=True)
                st.download_button(
                    "Download Comparison CSV",
                    data=comparison_df.to_csv(index=False).encode("utf-8"),
                    file_name=f"county_comparison_{datetime.now():%Y%m%d}.csv",
                    mime="text/csv",
                )
            else:
                st.info("Select at least two counties to compare.")

    with tab_explorer:
        st.markdown('<h2 class="sub-header">Data Explorer</h2>', unsafe_allow_html=True)
        all_columns = df.columns.tolist()
        preferred = ["Facility Name", "County", "keph_level", "ownership", "facility_category"]
        defaults = [col for col in preferred if col in all_columns]
        selected_columns = st.multiselect(
            "Columns to display", options=all_columns, default=defaults, key="explorer_columns"
        )
        if selected_columns:
            st.dataframe(df[selected_columns].head(500), use_container_width=True, height=500)
            st.caption(f"Showing up to 500 of {len(df):,} filtered records.")
            st.download_button(
                "Download Visible Data as CSV",
                data=df[selected_columns].to_csv(index=False).encode("utf-8"),
                file_name=f"facility_data_{datetime.now():%Y%m%d}.csv",
                mime="text/csv",
            )
        else:
            st.info("Select at least one column to display.")


if __name__ == "__main__":
    main()
