# APP/PAGES/3_🏆_County_Performance.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime

# Page configuration (must be first Streamlit command)
st.set_page_config(
    page_title="County Performance | Kenya Health Dashboard",
    page_icon="../ASSETS/PNGs/health-svgrepo-com.png",
    layout="wide"
)


def show_county_performance():
    """Main County Performance Dashboard"""
    
    st.title("🏆 County Performance Dashboard")
    st.markdown("""
    <div style='background-color: #1E88E520; padding: 1rem; border-radius: 10px; margin-bottom: 2rem;'>
        <b>📊 Compare and rank county healthcare facility performance</b><br>
        Identifies top-performing counties and provides actionable insights for improvement.
    </div>
    """, unsafe_allow_html=True)
    
    # Check if data is loaded in session state
    if 'dashboard_data' not in st.session_state or st.session_state.dashboard_data is None:
        # st.warning("⚠️ Please load data first using the main dashboard page")
        pass
        
        # Add a button to go to main page
        if st.button("📊 Go to Main Dashboard to Load Data"):
            pass

        
        # Show preview
        st.info("""
        ### 📋 This dashboard will show:
        - **County Rankings** - Which counties perform best
        - **Performance Metrics** - Facilities per 10k, KEPH levels, etc.
        - **Comparison Tools** - Compare multiple counties
        - **Improvement Insights** - Actionable recommendations
        
        👈 Click the button above to load data first
        """)
        return
    
    # Get data from session state
    df = st.session_state.dashboard_data
    pop_df = st.session_state.population_data
    
    # Detect county column
    county_col = None
    for col in df.columns:
        if 'county' in col.lower():
            county_col = col
            break
    
    if county_col is None:
        st.error("No county column found in the data!")
        return
    
    # Sidebar filters
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Metric weights
        st.subheader("📊 Score Weights")
        access_w = st.slider("Access Weight", 0, 100, 30, key="perf_access")
        quality_w = st.slider("Quality Weight", 0, 100, 30, key="perf_quality")
        efficiency_w = st.slider("Efficiency Weight", 0, 100, 20, key="perf_efficiency")
        equity_w = st.slider("Equity Weight", 0, 100, 20, key="perf_equity")
        
        # Normalize
        total = access_w + quality_w + efficiency_w + equity_w
        if total != 100:
            st.warning(f"Weights sum to {total}%")
            norm = 100 / total
        else:
            norm = 1
        
        st.markdown("---")
        
        # Tier thresholds
        st.subheader("🎯 Tier Thresholds")
        tier1 = st.slider("Tier 1 (Excellent)", 50, 100, 80)
        tier2 = st.slider("Tier 2 (Good)", 30, 90, 60)
        tier3 = st.slider("Tier 3 (Developing)", 0, 80, 40)
        
        st.markdown("---")
        
        # Calculate button
        if st.button("🔄 Calculate Rankings", use_container_width=True):
            st.rerun()
    
    # Calculate performance metrics
    with st.spinner("📊 Calculating county performance..."):
        performance_data = []
        counties = df[county_col].dropna().unique()
        
        for county in counties:
            county_df = df[df[county_col] == county]
            
            # Get population
            pop = None
            if pop_df is not None:
                county_upper = county.upper().strip()
                matches = pop_df[pop_df['County'].str.upper().str.strip() == county_upper]
                if len(matches) > 0:
                    pop = matches.iloc[0]
            
            total_pop = pop['Total'] if pop is not None and pd.notna(pop.get('Total')) else 0
            
            # Calculate metrics
            metrics = {
                'County': county,
                'Facilities': len(county_df),
                'Facilities per 10k': (len(county_df) / (total_pop / 10000)) if total_pop > 0 else 0,
                'KEPH 4+ %': (len(county_df[county_df['keph_level'].isin(['Level 4', 'Level 5', 'Level 6'])]) / len(county_df) * 100) if len(county_df) > 0 else 0,
                'Population': total_pop,
            }
            
            # Add access, quality, efficiency, equity scores
            metrics['Access Score'] = min(100, metrics['Facilities per 10k'] / 5 * 100)
            metrics['Quality Score'] = metrics['KEPH 4+ %']
            metrics['Efficiency Score'] = min(100, metrics['Facilities'] / max(1, total_pop / 50000) * 100)
            metrics['Equity Score'] = min(100, metrics['Facilities per 10k'] / 2 * 100)
            
            # Composite score
            metrics['Composite Score'] = (
                metrics['Access Score'] * (access_w * norm / 100) +
                metrics['Quality Score'] * (quality_w * norm / 100) +
                metrics['Efficiency Score'] * (efficiency_w * norm / 100) +
                metrics['Equity Score'] * (equity_w * norm / 100)
            )
            
            # Determine tier
            if metrics['Composite Score'] >= tier1:
                metrics['Tier'] = "🏆 Excellent"
            elif metrics['Composite Score'] >= tier2:
                metrics['Tier'] = "✅ Good"
            elif metrics['Composite Score'] >= tier3:
                metrics['Tier'] = "📊 Developing"
            elif metrics['Composite Score'] >= 20:
                metrics['Tier'] = "⚠️ Basic"
            else:
                metrics['Tier'] = "🚨 Critical"
            
            performance_data.append(metrics)
        
        perf_df = pd.DataFrame(performance_data)
        perf_df = perf_df.sort_values('Composite Score', ascending=False).reset_index(drop=True)
        perf_df.insert(0, 'Rank', range(1, len(perf_df) + 1))
    
    # ==================== DISPLAY ====================
    
    # Top 3 Performers
    st.header("🏆 Top Performing Counties")
    
    top3 = perf_df.head(3)
    cols = st.columns(3)
    medals = ['🥇', '🥈', '🥉']
    colors = ['#FFD700', '#C0C0C0', '#CD7F32']
    
    for i, (_, row) in enumerate(top3.iterrows()):
        with cols[i]:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {colors[i]}20, {colors[i]}40);
                        border: 2px solid {colors[i]};
                        border-radius: 10px;
                        padding: 20px;
                        text-align: center;">
                <h1 style="font-size: 48px;">{medals[i]}</h1>
                <h2>{row['County']}</h2>
                <h1 style="color: {colors[i]}; font-size: 42px;">{row['Composite Score']:.1f}%</h1>
                <div style="display: flex; justify-content: center; gap: 10px;">
                    <span style="background: #333; color: white; padding: 5px 10px; border-radius: 20px;">🏥 {row['Facilities']}</span>
                    <span style="background: #333; color: white; padding: 5px 10px; border-radius: 20px;">👥 {row['Facilities per 10k']:.2f}/10k</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Leaderboard", 
        "🗺️ Tier Distribution",
        "📊 County Comparison",
        "🎯 Insights"
    ])
    
    with tab1:
        st.subheader("County Performance Leaderboard")
        
        # Display dataframe
        display_cols = ['Rank', 'County', 'Composite Score', 'Tier', 'Facilities', 'Facilities per 10k', 'KEPH 4+ %']
        st.dataframe(
            perf_df[display_cols].style.format({
                'Composite Score': '{:.1f}%',
                'Facilities per 10k': '{:.2f}',
                'KEPH 4+ %': '{:.1f}%'
            }),
            use_container_width=True,
            height=500,
            column_config={
                "Composite Score": st.column_config.ProgressColumn("Score", format="%.1f%%", min_value=0, max_value=100)
            }
        )
        
        # Download button
        csv = perf_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Performance Data", csv, "county_performance.csv", "text/csv")
    
    with tab2:
        st.subheader("Performance Tier Distribution")
        
        # Pie chart
        tier_counts = perf_df['Tier'].value_counts()
        fig = px.pie(
            values=tier_counts.values,
            names=tier_counts.index,
            title="Counties by Performance Tier",
            color=tier_counts.index,
            color_discrete_map={
                '🏆 Excellent': '#FFD700',
                '✅ Good': '#C0C0C0',
                '📊 Developing': '#CD7F32',
                '⚠️ Basic': '#FF6B6B',
                '🚨 Critical': '#FF0000'
            }
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Tier summary table
        st.subheader("Tier Summary")
        summary_data = []
        for tier in ['🏆 Excellent', '✅ Good', '📊 Developing', '⚠️ Basic', '🚨 Critical']:
            count = len(perf_df[perf_df['Tier'] == tier])
            pct = (count / len(perf_df) * 100) if len(perf_df) > 0 else 0
            summary_data.append({'Tier': tier, 'Count': count, 'Percentage': f'{pct:.1f}%'})
        
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)
    
    with tab3:
        st.subheader("Compare Counties")
        
        # Multi-select for counties
        all_counties = perf_df['County'].tolist()
        compare = st.multiselect(
            "Select counties to compare (2-4 recommended)",
            options=all_counties,
            default=all_counties[:3] if len(all_counties) >= 3 else all_counties,
            max_selections=6
        )
        
        if len(compare) >= 2:
            compare_df = perf_df[perf_df['County'].isin(compare)]
            
            # Bar chart comparison
            fig = make_subplots(rows=1, cols=2, subplot_titles=('Composite Score (%)', 'Facilities per 10k'))
            
            fig.add_trace(
                go.Bar(x=compare_df['County'], y=compare_df['Composite Score'], 
                       marker_color='#1E88E5', text=compare_df['Composite Score'].round(1)),
                row=1, col=1
            )
            
            fig.add_trace(
                go.Bar(x=compare_df['County'], y=compare_df['Facilities per 10k'],
                       marker_color='#2ECC71', text=compare_df['Facilities per 10k'].round(2)),
                row=1, col=2
            )
            
            fig.update_layout(height=400, showlegend=False, title_text="County Comparison")
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Comparison table
            st.dataframe(compare_df[['County', 'Composite Score', 'Tier', 'Facilities', 'Facilities per 10k', 'KEPH 4+ %']], 
                        use_container_width=True)
    
    with tab4:
        st.subheader("Improvement Insights")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### ⚠️ Priority Intervention Counties")
            bottom5 = perf_df.tail(5)
            for _, row in bottom5.iterrows():
                with st.expander(f"📍 {row['County']} - {row['Composite Score']:.1f}% ({row['Tier']})"):
                    st.metric("Facilities", row['Facilities'])
                    st.metric("Facilities per 10k", f"{row['Facilities per 10k']:.2f}")
                    
                    # Recommendations
                    st.markdown("**💡 Recommendations:**")
                    if row['Facilities per 10k'] < 2:
                        st.markdown("- 🏥 Build new health centers")
                    if row['KEPH 4+ %'] < 20:
                        st.markdown("- 📈 Upgrade facilities to Level 4+")
                    if row['Facilities'] < 10:
                        st.markdown("- 🏗️ Prioritize new facility construction")
        
        with col2:
            st.markdown("### 📈 Performance Gaps")
            
            # Calculate gaps
            top_avg = perf_df.head(5)[['Facilities per 10k', 'KEPH 4+ %']].mean()
            bottom_avg = perf_df.tail(5)[['Facilities per 10k', 'KEPH 4+ %']].mean()
            
            gaps = pd.DataFrame({
                'Metric': ['Facilities per 10k', 'KEPH Level 4+ %'],
                'Top 5 Avg': [top_avg['Facilities per 10k'], top_avg['KEPH 4+ %']],
                'Bottom 5 Avg': [bottom_avg['Facilities per 10k'], bottom_avg['KEPH 4+ %']]
            })
            
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Top 5 Counties', x=gaps['Metric'], y=gaps['Top 5 Avg'], marker_color='#2ECC71'))
            fig.add_trace(go.Bar(name='Bottom 5 Counties', x=gaps['Metric'], y=gaps['Bottom 5 Avg'], marker_color='#E74C3C'))
            fig.update_layout(title='Performance Gap Analysis', barmode='group', height=350)
            st.plotly_chart(fig, use_container_width=True)
            
            # National averages
            st.markdown("### 📊 National Averages")
            st.metric("Avg Facilities per County", f"{perf_df['Facilities'].mean():.0f}")
            st.metric("National Avg per 10k", f"{perf_df['Facilities per 10k'].mean():.2f}")
            st.metric("Avg Composite Score", f"{perf_df['Composite Score'].mean():.1f}%")

# Run the page
if __name__ == "__main__":
    show_county_performance()