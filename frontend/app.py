import streamlit as st
import requests
import pandas as pd

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Standup Performance Analytics V2")
st.title("Standup Performance Analytics")

# --- Backend Configuration ---
BACKEND_URL = "http://localhost:8000"


# --- Helper Functions ---
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_projects():
    """Fetches the list of active projects from the backend."""
    try:
        res = requests.get(f"{BACKEND_URL}/projects")
        if res.status_code == 200:
            return [p['project_tag'] for p in res.json()]
        else:
            st.error(f"Failed to fetch projects. Status: {res.status_code}")
            return []
    except requests.ConnectionError:
        st.error("Connection Error: Could not connect to the backend.")
        return []


# --- Sidebar ---
with st.sidebar:
    st.header("Report Settings")
    
    projects = get_projects()
    if not projects:
        st.warning("No active projects found. Please configure projects in the backend.")
        st.stop()
        
    project_tag = st.selectbox("Select Project", options=projects)
    
    s_date = st.date_input("Start Date")
    e_date = st.date_input("End Date")
    
    btn = st.button("Generate Report", type="primary", use_container_width=True)

# --- Main Content ---
if btn:
    with st.spinner("Analyzing standup data... This may take a moment."):
        try:
            payload = {
                "project_tag": project_tag,
                "start_date": str(s_date),
                "end_date": str(e_date),
            }
            res = requests.post(f"{BACKEND_URL}/analyze", json=payload)

            if res.status_code != 200:
                st.error(f"Error from backend: {res.json().get('detail', res.text)}")
            else:
                data = res.json()
                
                if "message" in data or not data.get("performance_data"):
                    st.warning(data.get("message", "No attendance data found for this period."))
                else:
                    # --- KPIs ---
                    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                    kpi1.metric(
                        "Total Meetings",
                        data.get('total_meetings', 0),
                        help="Total number of meetings that occurred on working days within the selected date range."
                    )
                    kpi2.metric(
                        "Avg. Duration",
                        f"{data.get('avg_duration_minutes', 0):.1f} min",
                        help="Average duration of each meeting in minutes."
                    )
                    kpi3.metric(
                        "Avg. Team Punctuality",
                        f"{data.get('team_punctuality_avg', 0):.1f}%",
                        help="The average on-time joining percentage across all team members."
                    )
                    kpi4.metric(
                        "Avg. Attendees",
                        f"{data.get('avg_users_per_meeting', 0):.1f}",
                        help="Average number of team members attending each meeting."
                    )
                    
                    st.divider()

                    # --- DataFrames ---
                    df = pd.DataFrame(data['performance_data'])
                    df.rename(columns={'DaysAttended': 'Days Attended', 'DaysOnTime': 'Days On Time'}, inplace=True)
                    
                    sorted_df = df.sort_values(by='Attendance %', ascending=False)
                    top_5 = sorted_df.head(5)
                    bottom_5 = sorted_df.tail(5)

                    # --- Tabs for Display ---
                    tab1, tab2, tab3 = st.tabs(["🏆 Performance Highlights", "👥 Full Team Report", "⏰ Join/Leave Details"])

                    with tab1:
                        st.subheader("Top 5 Attendees")
                        st.dataframe(
                            top_5[['Name', 'Team', 'Attendance %', 'Punctuality %']]
                            .style.background_gradient(subset=['Attendance %'], cmap="Greens")
                            .format({'Attendance %': '{:.1f}%', 'Punctuality %': '{:.1f}%'}),
                        )
                        st.caption("Top 5 team members by attendance percentage.")

                        st.divider()

                        st.subheader("Bottom 5 Attendees")
                        st.dataframe(
                            bottom_5[['Name', 'Team', 'Attendance %', 'Punctuality %']]
                            .style.background_gradient(subset=['Attendance %'], cmap="Reds_r")
                            .format({'Attendance %': '{:.1f}%', 'Punctuality %': '{:.1f}%'}),
                        )
                        st.caption("Bottom 5 team members by attendance percentage.")

                    with tab2:
                        st.subheader("Full Team Breakdown")
                        # Use a tooltip on the dataframe itself for the main explanation
                        st.dataframe(
                            sorted_df[['Name', 'Team', 'Days Attended', 'Attendance %', 'Punctuality %']]
                            .style.background_gradient(subset=['Attendance %'], cmap="Blues")
                            .format({'Attendance %': '{:.1f}%', 'Punctuality %': '{:.1f}%'}),
                            hide_index=True,
                            use_container_width=True,
                        )
                        st.caption("Full report for all team members. Attendance % = (Days Attended / Total Meetings) * 100. Punctuality % = (Days On Time / Days Attended) * 100.")

                    with tab3:
                        st.subheader("Daily Join and Leave Times")
                        if 'daily_attendance' in data and data['daily_attendance']:
                            daily_df = pd.DataFrame(data['daily_attendance'])
                            daily_df['JoinTime'] = daily_df['JoinTime'].fillna('N/A')
                            daily_df['LeaveTime'] = daily_df['LeaveTime'].fillna('N/A')
                            st.dataframe(
                                daily_df[['Name', 'Date', 'JoinTime', 'LeaveTime']],
                                hide_index=True,
                                use_container_width=True
                            )
                            st.caption("Shows the first join and last leave time for each participant in each meeting.")
                        else:
                            st.warning("No daily attendance data available.")

        except requests.ConnectionError as e:
            st.error(f"Connection Error: Could not connect to the backend at {BACKEND_URL}. Please ensure it is running.")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
