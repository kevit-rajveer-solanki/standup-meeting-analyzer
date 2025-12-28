import logging
from datetime import datetime
from dateutil import parser
import pandas as pd
from typing import Dict, Any, List

from app.services.graph_service import GraphService
from app.utils.date_utils import is_working_day
from app.models.schemas import StandupMeetingConfig

# Configure logging
logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Handles the business logic for calculating standup meeting analytics.
    """

    def __init__(self, graph_service: GraphService):
        self.graph_service = graph_service
        self.user_cache = {}  # In-memory cache for user details

    def _get_user_details(self, email: str) -> Dict[str, str]:
        """Cache-aware user detail fetching."""
        if not email:
            return {"name": "Unknown", "team": "Unknown"}
        if email in self.user_cache:
            return self.user_cache[email]

        details = self.graph_service.get_user_details(email)
        if details:
            info = details
        else:
            # Handle cases where user is not in the directory
            info = {"name": email, "team": "External/Guest"}
        self.user_cache[email] = info
        return info

    def analyze_project_performance(
            self,
            project_config: StandupMeetingConfig,
            start_date_str: str,
            end_date_str: str
    ) -> Dict[str, Any]:
        """
        Main function to orchestrate the performance analysis for a project.
        """
        # 1. Initial Setup
        organizer_id = self.graph_service.get_user_id(project_config.organizer_email)
        if not organizer_id:
            logger.error(f"Organizer '{project_config.organizer_email}' not found.")
            return {"error": "Organizer not found"}

        meeting_id = self.graph_service.get_meeting_id_from_link(organizer_id, project_config.meeting_link)
        if not meeting_id:
            logger.error(f"Meeting ID for link '{project_config.meeting_link}' not found.")
            return {"error": "Meeting not found"}

        # 2. Fetch and Filter Reports
        all_reports = self.graph_service.get_attendance_reports(organizer_id, meeting_id)
        if not all_reports:
            return {"message": "No meeting reports found for this period."}

        start_range = parser.parse(start_date_str).date()
        end_range = parser.parse(end_date_str).date()
        
        all_attendees = []
        meeting_durations = []

        # 3. Process each meeting report
        for report in all_reports:
            meeting_start_dt_str = report.get('meetingStartDateTime')
            if not meeting_start_dt_str:
                continue

            meeting_dt = parser.parse(meeting_start_dt_str)
            meeting_date = meeting_dt.date()

            # Filter by date range and working days
            if not (start_range <= meeting_date <= end_range and is_working_day(meeting_date)):
                continue

            # Calculate meeting duration
            meeting_end_dt_str = report.get('meetingEndDateTime')
            if meeting_end_dt_str:
                duration = (parser.parse(meeting_end_dt_str) - meeting_dt).total_seconds() / 60
                meeting_durations.append(duration)
            
            # Fetch and process attendees for this meeting
            records_url = f"https://graph.microsoft.com/v1.0/users/{organizer_id}/onlineMeetings/{meeting_id}/attendanceReports/{report['id']}/attendanceRecords"
            records = self.graph_service.get_attendance_records(records_url)

            for rec in records:
                email = rec.get('emailAddress')
                details = self._get_user_details(email)

                # Skip Guests and External users as per requirements
                if details['team'] in ["External/Guest", "Unknown", "Unassigned"]:
                    continue

                join_time = None
                leave_time = None
                is_on_time = False
                intervals = rec.get('attendanceIntervals', [])
                if intervals:
                    try:
                        join_times = [parser.parse(i['joinDateTime']) for i in intervals if i.get('joinDateTime')]
                        leave_times = [parser.parse(i['leaveDateTime']) for i in intervals if i.get('leaveDateTime')]

                        if join_times:
                            first_join = min(join_times)
                            join_time = first_join.time().isoformat(timespec='seconds')
                            if (first_join - meeting_dt).total_seconds() / 60 <= 5:
                                is_on_time = True

                        if leave_times:
                            last_leave = max(leave_times)
                            leave_time = last_leave.time().isoformat(timespec='seconds')

                    except (ValueError, TypeError):
                        pass  # Ignore if times are malformed

                all_attendees.append({
                    "Name": details['name'],
                    "Team": details['team'],
                    "Date": str(meeting_date),
                    "OnTime": is_on_time,
                    "JoinTime": join_time,
                    "LeaveTime": leave_time
                })

        if not all_attendees:
            return {"message": "Meetings were found, but no valid attendee data could be processed."}

        # 4. Aggregate Data with Pandas
        df = pd.DataFrame(all_attendees)
        total_meetings = df['Date'].nunique()

        # Person-specific metrics
        person_stats = df.groupby(['Team', 'Name']).agg(
            DaysAttended=('Date', 'nunique'),
            DaysOnTime=('OnTime', 'sum')
        ).reset_index()

        person_stats['Attendance %'] = (person_stats['DaysAttended'] / total_meetings * 100).round(1)
        # Punctuality is based on days attended, not total meetings
        person_stats['Punctuality %'] = (person_stats['DaysOnTime'] / person_stats['DaysAttended'] * 100).fillna(0).round(1)

        # Team-specific metrics
        avg_duration = sum(meeting_durations) / len(meeting_durations) if meeting_durations else 0
        avg_users_per_meeting = df.groupby('Date')['Name'].nunique().mean()

        return {
            "total_meetings": total_meetings,
            "total_people": df['Name'].nunique(),
            "avg_duration_minutes": round(avg_duration, 1),
            "avg_users_per_meeting": round(avg_users_per_meeting, 1),
            "team_punctuality_avg": round(person_stats['Punctuality %'].mean(), 1),
            "performance_data": person_stats.to_dict('records'),
            "daily_attendance": all_attendees
        }
