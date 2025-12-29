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
        res = requests.get(f"{BACKEND_URL}/projects/active")
        if res.status_code == 200:
            return [p['project_tag'] for p in res.json()]
        else:
            st.error(f"Failed to fetch projects. Status: {res.status_code}")
            return []
    except requests.ConnectionError:
        st.error("Connection Error: Could not connect to the backend.")
        return []

@st.cache_data(ttl=5) # Short cache for admin page
def get_all_projects():
    """Fetches all projects from the backend."""
    try:
        res = requests.get(f"{BACKEND_URL}/projects")
        if res.status_code == 200:
            return res.json()
        else:
            st.error(f"Failed to fetch all projects. Status: {res.status_code}")
            return []
    except requests.ConnectionError:
        st.error("Connection Error: Could not connect to the backend.")
        return []


# --- Page Rendering ---
def render_analytics_page():
    # --- Sidebar for Analytics ---
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
    st.header("Analytics Dashboard")
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
                        sub_tab1, sub_tab2, sub_tab3 = st.tabs(["🏆 Performance Highlights", "👥 Full Team Report", "⏰ Join/Leave Details"])

                        with sub_tab1:
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

                        with sub_tab2:
                            st.subheader("Full Team Breakdown")
                            # Use a tooltip on the dataframe itself for the main explanation
                            st.dataframe(
                                sorted_df[['Name', 'Team', 'Days Attended', 'Attendance %', 'Punctuality %']]
                                .style.background_gradient(subset=['Attendance %'], cmap="Blues")
                                .format({'Attendance %': '{:.1f}%', 'Punctuality %': '{:.1f}%'}),
                                hide_index=True,
                                use_container_width=True,
                            )
                            st.caption("Full report for all team members. Attendance % = (Days Attended / Total Meetings) * 100. Punctuality % = (Days OnTime / Days Attended) * 100.")

                        with sub_tab3:
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
    else:
        st.info("Select a project and date range in the sidebar to generate a report.")

def render_manage_projects_page():
    st.header("Manage Projects")

    # --- Edit Project Form ---
    if 'editing_project' in st.session_state:
        project_tag_to_edit = st.session_state['editing_project']
        project_to_edit = next((p for p in get_all_projects() if p['project_tag'] == project_tag_to_edit), None)

        if project_to_edit:
            with st.form("edit_project_form"):
                st.subheader(f"Editing: {project_to_edit['project_tag']}")
                email = st.text_input("Organizer Email", value=project_to_edit['organizer_email'])
                link = st.text_input("Meeting Link", value=project_to_edit['meeting_link'])
                is_active = st.checkbox("Is Active", value=project_to_edit['is_active'])
                
                update_btn, cancel_btn = st.columns(2)
                if update_btn.form_submit_button("Update Project", use_container_width=True):
                    payload = {"organizer_email": email, "meeting_link": link, "is_active": is_active}
                    try:
                        res = requests.put(f"{BACKEND_URL}/projects/{project_tag_to_edit}", json=payload)
                        if res.status_code == 200:
                            st.success("Project updated successfully.")
                            del st.session_state['editing_project']
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"Failed to update project: {res.json().get('detail', res.text)}")
                    except requests.ConnectionError:
                        st.error("Connection Error.")
                
                if cancel_btn.form_submit_button("Cancel", use_container_width=True):
                    del st.session_state['editing_project']
                    st.rerun()

    # --- Add New Project Form ---
    with st.form("add_project_form", clear_on_submit=True):
        st.subheader("Add New Project")
        new_project_tag = st.text_input("Project Tag (must be unique)")
        new_organizer_email = st.text_input("Organizer Email")
        new_meeting_link = st.text_input("Meeting Link")
        submitted = st.form_submit_button("Add Project")

        if submitted:
            if not all([new_project_tag, new_organizer_email, new_meeting_link]):
                st.error("All fields are required.")
            else:
                payload = {
                    "project_tag": new_project_tag,
                    "organizer_email": new_organizer_email,
                    "meeting_link": new_meeting_link
                }
                try:
                    res = requests.post(f"{BACKEND_URL}/projects", json=payload)
                    if res.status_code == 200:
                        st.success(f"Project '{new_project_tag}' created successfully.")
                        st.cache_data.clear()
                    else:
                        st.error(f"Failed to create project: {res.json().get('detail', res.text)}")
                except requests.ConnectionError:
                    st.error("Connection Error: Could not connect to the backend.")

    st.divider()

    # --- Existing Projects ---
    st.subheader("Existing Projects")
    if st.button("Refresh List"):
        st.cache_data.clear()

    projects = get_all_projects()
    if not projects:
        st.warning("No projects found.")
        return

    for project in projects:
        with st.expander(f"{project['project_tag']} ({'Active' if project['is_active'] else 'Inactive'})"):
            st.write(f"**Organizer Email:** {project['organizer_email']}")
            st.write(f"**Meeting Link:** {project['meeting_link']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Edit", key=f"edit_{project['project_tag']}", use_container_width=True):
                    st.session_state['editing_project'] = project['project_tag']
                    st.rerun()
            with col2:
                if st.button("Delete", key=f"delete_{project['project_tag']}", use_container_width=True, type="primary"):
                    try:
                        res = requests.delete(f"{BACKEND_URL}/projects/{project['project_tag']}")
                        if res.status_code == 200:
                            st.success(f"Project '{project['project_tag']}' deleted successfully.")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"Failed to delete project. Status: {res.status_code}")
                    except requests.ConnectionError:
                        st.error("Connection Error: Could not connect to the backend.")

# --- Main Navigation ---
tab1, tab2 = st.tabs(["Analytics", "Manage Projects"])

with tab1:
    render_analytics_page()

with tab2:
    render_manage_projects_page()
