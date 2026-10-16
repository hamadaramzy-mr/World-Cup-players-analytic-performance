import streamlit as st
import pandas as pd
import plotly.express as px

# Page Configuration
st.set_page_config(
    page_title="World Cup 2026 Analytics",
    page_icon="⚽",
    layout="wide"
)

# Load Data
@st.cache_data
def load_data():
    file_path = 'fifa_world_cup_2026_full_stats.csv'
    df = pd.read_csv(file_path, header=1, encoding='utf-8')
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading CSV file: {e}")
    st.stop()

# Validate Player Column
if 'Player' not in df.columns:
    possible_player_cols = [col for col in df.columns if 'player' in col.lower()]
    if possible_player_cols:
        df.rename(columns={possible_player_cols[0]: 'Player'}, inplace=True)
    else:
        st.error("The 'Player' column was not found. Please verify the CSV format.")
        st.stop()

# Flag Emojis Function
def get_flag_emoji(country_string):
    if not isinstance(country_string, str):
        return "⚽"
    
    flags = {
        'Egypt': '🇪🇬', 'eg': '🇪🇬',
        'France': '🇫🇷', 'fr': '🇫🇷',
        'Argentina': '🇦🇷', 'ar': '🇦🇷',
        'England': '🏴󠁧󠁢󠁥󠁮󠁧󠁿', 'eng': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
        'Brazil': '🇧🇷', 'br': '🇧🇷',
        'Spain': '🇪🇸', 'es': '🇪🇸',
        'Germany': '🇩🇪', 'de': '🇩🇪',
        'Portugal': '🇵🇹', 'pt': '🇵🇹',
        'Morocco': '🇲🇦', 'ma': '🇲🇦',
        'Saudi Arabia': '🇸🇦', 'sa': '🇸🇦',
        'Tunisia': '🇹🇳', 'tn': '🇹🇳',
        'Qatar': '🇶🇦', 'qa': '🇶🇦',
        'Jordan': '🇯🇴', 'jo': '🇯🇴',
        'United States': '🇺🇸', 'us': '🇺🇸',
        'Norway': '🇳🇴', 'no': '🇳🇴'
    }
    
    for key, flag in flags.items():
        if key.lower() in country_string.lower():
            return flag
    return "⚽"

if 'Squad' in df.columns:
    df['Flag'] = df['Squad'].apply(get_flag_emoji)
    df['Display_Team'] = df['Flag'] + " " + df['Squad'].astype(str)
else:
    df['Display_Team'] = "⚽ Unknown"

# Clean Numeric Data & Normalize Column Names
numeric_cols = ['Goals', 'Assists', 'Minutes', 'Min', 'Gls', 'Ast', 'Starts', 'MP']
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

if 'Gls' in df.columns and 'Goals' not in df.columns:
    df['Goals'] = df['Gls']
if 'Ast' in df.columns and 'Assists' not in df.columns:
    df['Assists'] = df['Ast']
if 'Min' in df.columns and 'Minutes' not in df.columns:
    df['Minutes'] = df['Min']

# Dynamic Initials Avatar Generator (Fallback)
def get_player_image(player_name):
    formatted_name = player_name.replace(" ", "+")
    return f"https://ui-avatars.com/api/?name={formatted_name}&background=1f2937&color=fff&size=256&bold=true"

# Sidebar Navigation
st.sidebar.markdown("### Main Menu")
app_mode = st.sidebar.radio(
    "Select Section:", 
    ["📊 Player Statistics", "⚔️ Team Comparison", "👥 Player Head-to-Head"]
)

# 1. Statistics Section
if app_mode == "📊 Player Statistics":
    st.title("⚽ FIFA World Cup Player Performance Dashboard")
    st.write("An application to explore and analyze player statistics based on authentic tournament data.")

    if 'Squad' in df.columns:
        teams = ['All'] + sorted(df['Squad'].dropna().unique().tolist())
        selected_team = st.sidebar.selectbox("Filter by Team", teams)
        
        if selected_team != 'All':
            filtered_df = df[df['Squad'] == selected_team]
        else:
            filtered_df = df
    else:
        filtered_df = df

    st.subheader("📋 Dataset Table")
    display_table_cols = ['Player', 'Display_Team', 'Goals', 'Assists'] if 'Goals' in df.columns else df.columns[:5]
    st.dataframe(filtered_df[[c for c in display_table_cols if c in filtered_df.columns]], use_container_width=True)

    st.subheader("📈 Visualizations")
    if 'Goals' in filtered_df.columns and not filtered_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Top Goal Scorers")
            top_scorers = filtered_df.nlargest(10, 'Goals')
            fig_goals = px.bar(
                top_scorers, x='Player', y='Goals', color='Display_Team', text='Goals'
            )
            st.plotly_chart(fig_goals, use_container_width=True)
            
        with col2:
            if 'Assists' in filtered_df.columns:
                st.markdown("##### Top Assist Providers")
                top_assists = filtered_df.nlargest(10, 'Assists')
                fig_assists = px.bar(
                    top_assists, x='Player', y='Assists', color='Display_Team', text='Assists'
                )
                st.plotly_chart(fig_assists, use_container_width=True)

        # Team goal share breakdown with dynamic text threshold
        st.markdown("---")
        st.subheader("🍩 Team Goal Share Distribution")
        if 'Squad' in df.columns:
            team_goals = df.groupby('Display_Team')['Goals'].sum().reset_index()
            team_goals = team_goals[team_goals['Goals'] > 0]
            
            if not team_goals.empty:
                total_goals = team_goals['Goals'].sum()
                team_goals['Percentage'] = (team_goals['Goals'] / total_goals) * 100
                
                # Show percentage text only if >= 3%, otherwise hide text on chart (visible on hover)
                team_goals['Display_Text'] = team_goals.apply(
                    lambda row: f"{row['Percentage']:.1f}%" if row['Percentage'] >= 3.0 else "", axis=1
                )
                
                fig_pie_teams = px.pie(
                    team_goals, 
                    names='Display_Team', 
                    values='Goals', 
                    hole=0.4,
                    custom_data=['Percentage']
                )
                
                fig_pie_teams.update_traces(
                    text=team_goals['Display_Text'],
                    textinfo='text',
                    hovertemplate="<b>%{label}</b><br>Goals: %{value}<br>Share: %{customdata[0]:.2f}%<extra></extra>"
                )
                
                fig_pie_teams.update_layout(
                    legend=dict(
                        orientation="h",
                        yanchor="top",
                        y=-0.2,
                        xanchor="center",
                        x=0.5
                    ),
                    margin=dict(t=30, b=80, l=30, r=30)
                )
                st.plotly_chart(fig_pie_teams, use_container_width=True)
            else:
                st.info("No aggregated team goals found.")

# 2. Team Comparison Section
elif app_mode == "⚔️ Team Comparison":
    st.title("⚔️ Country & Team Comparison")
    st.write("Compare rates, scores, and total metrics between two or more national teams side-by-side.")

    if 'Squad' in df.columns:
        all_teams = sorted(df['Squad'].dropna().unique().tolist())
        selected_teams = st.multiselect("Select Teams to Compare (Choose 2 or more):", all_teams, default=all_teams[:2] if len(all_teams) >= 2 else all_teams)

        if len(selected_teams) > 0:
            comp_df = df[df['Squad'].isin(selected_teams)]
            
            st.subheader("📊 Aggregate Team Comparison")
            available_metrics = [col for col in ['Goals', 'Assists', 'Starts', 'Minutes'] if col in comp_df.columns]
            metrics_grouped = comp_df.groupby('Display_Team')[available_metrics].sum().reset_index()
            st.dataframe(metrics_grouped, use_container_width=True)

            col_a, col_b = st.columns(2)
            with col_a:
                if 'Goals' in metrics_grouped.columns:
                    st.markdown("##### Total Goals Comparison")
                    fig_comp_bar = px.bar(
                        metrics_grouped, x='Display_Team', y='Goals', color='Display_Team', text='Goals', barmode='group'
                    )
                    st.plotly_chart(fig_comp_bar, use_container_width=True)

            with col_b:
                if 'Goals' in metrics_grouped.columns:
                    st.markdown("##### Team Goal Share Breakdown")
                    fig_comp_pie = px.pie(
                        metrics_grouped, names='Display_Team', values='Goals', hole=0.3
                    )
                    st.plotly_chart(fig_comp_pie, use_container_width=True)
                
            st.subheader("📋 Detailed Roster for Selected Teams")
            desired_cols = ['Display_Team', 'Player', 'Goals', 'Assists', 'Minutes', 'Starts']
            safe_detail_cols = [c for c in desired_cols if c in comp_df.columns]
            st.dataframe(comp_df[safe_detail_cols], use_container_width=True)
        else:
            st.warning("Please select at least one team from the multiselect menu above.")
    else:
        st.error("The 'Squad' column is missing from the dataset, preventing team comparison.")

# 3. Player Head-to-Head Comparison
elif app_mode == "👥 Player Head-to-Head":
    st.title("👥 Player Head-to-Head Comparison")
    st.write("Select two players to compare their tournament metrics, performance records, and avatars side-by-side.")

    if 'Player' in df.columns:
        players_list = sorted(df['Player'].dropna().unique().tolist())
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            player1 = st.selectbox("Select Player 1:", players_list, index=0 if len(players_list) > 0 else 0)
        with col_p2:
            player2 = st.selectbox("Select Player 2:", players_list, index=1 if len(players_list) > 1 else 0)

        if player1 and player2:
            p1_data = df[df['Player'] == player1].iloc[0]
            p2_data = df[df['Player'] == player2].iloc[0]

            col_img1, col_img2 = st.columns(2)
            
            with col_img1:
                st.subheader(f"⭐ {player1}")
                st.write(f"Team: {p1_data.get('Display_Team', 'Unknown')}")
                st.image(get_player_image(player1), width=250)
                    
            with col_img2:
                st.subheader(f"⭐ {player2}")
                st.write(f"Team: {p2_data.get('Display_Team', 'Unknown')}")
                st.image(get_player_image(player2), width=250)

            st.markdown("---")
            st.subheader("📊 Direct Stats Comparison")
            
            metrics_to_compare = [c for c in ['Goals', 'Assists', 'Minutes', 'Starts', 'MP'] if c in df.columns]
            
            comparison_table = pd.DataFrame({
                'Metric': metrics_to_compare,
                player1: [p1_data[m] for m in metrics_to_compare],
                player2: [p2_data[m] for m in metrics_to_compare]
            })
            
            st.dataframe(comparison_table, use_container_width=True)

            chart_data = pd.melt(
                comparison_table, 
                id_vars=['Metric'], 
                value_vars=[player1, player2],
                var_name='Player', 
                value_name='Value'
            )
            
            fig_h2h = px.bar(
                chart_data, 
                x='Metric', 
                y='Value', 
                color='Player', 
                barmode='group',
                text='Value'
            )
            st.plotly_chart(fig_h2h, use_container_width=True)
    else:
        st.error("Player column missing.")