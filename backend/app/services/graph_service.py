import logging
import requests
import urllib.parse
from typing import Optional, List, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"


class GraphService:
    """
    Service for interacting with the Microsoft Graph API.
    It handles the construction of API calls and returns raw data.
    """

    def __init__(self, token: str):
        self.headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

    def get_user_id(self, email: str) -> Optional[str]:
        """Fetches the ID for a user by their email."""
        url = f"{GRAPH_ENDPOINT}/users/{email}"
        try:
            resp = requests.get(url, headers=self.headers)
            if resp.status_code == 200:
                return resp.json().get('id')
            logger.warning(f"Could not find user ID for {email}. Status: {resp.status_code}")
        except requests.RequestException as e:
            logger.error(f"Request error getting user ID for {email}: {e}")
        return None

    def get_user_details(self, email: str) -> Optional[Dict[str, str]]:
        """Fetches display name and department for a user."""
        url = f"{GRAPH_ENDPOINT}/users/{email}?$select=department,displayName"
        try:
            resp = requests.get(url, headers=self.headers)
            if resp.status_code == 200:
                data = resp.json()
                return {"name": data.get('displayName', email), "team": data.get('department', 'Unassigned')}
            logger.warning(f"Could not get details for {email}. Status: {resp.status_code}")
        except requests.RequestException as e:
            logger.error(f"Request error getting details for {email}: {e}")
        return None

    def get_meeting_id_from_link(self, user_id: str, join_url: str) -> Optional[str]:
        """Finds an online meeting ID using the organizer's ID and the meeting join URL."""
        # Primary method: Exact match on the join URL
        url = f"{GRAPH_ENDPOINT}/users/{user_id}/onlineMeetings"
        params = {"$filter": f"JoinWebUrl eq '{join_url}'"}
        try:
            resp = requests.get(url, headers=self.headers, params=params)
            if resp.status_code == 200 and resp.json().get('value'):
                return resp.json()['value'][0]['id']

            # Fallback method for cases where the URL format differs slightly
            logger.info("Exact match for meeting link failed, trying fallback lookup...")
            decoded_url = urllib.parse.unquote(join_url)
            if 'meetup-join/' in decoded_url:
                thread_id = decoded_url.split('meetup-join/')[1].split('/0?')[0]
                # Fetch recent meetings and match by thread ID
                recent_meetings_resp = requests.get(url, headers=self.headers, params={"$top": 20})
                if recent_meetings_resp.status_code == 200:
                    for meeting in recent_meetings_resp.json().get('value', []):
                        if thread_id in urllib.parse.unquote(meeting.get('joinWebUrl', '')):
                            logger.info(f"Found meeting with fallback method: {meeting['id']}")
                            return meeting['id']
        except requests.RequestException as e:
            logger.error(f"Request error getting meeting ID: {e}")
        return None

    def get_attendance_reports(self, user_id: str, meeting_id: str) -> List[Dict[str, Any]]:
        """Fetches all attendance reports for a specific meeting."""
        url = f"{GRAPH_ENDPOINT}/users/{user_id}/onlineMeetings/{meeting_id}/attendanceReports"
        try:
            resp = requests.get(url, headers=self.headers)
            if resp.status_code == 200:
                return resp.json().get('value', [])
        except requests.RequestException as e:
            logger.error(f"Request error getting attendance reports: {e}")
        return []

    def get_attendance_records(self, report_url: str) -> List[Dict[str, Any]]:
        """Fetches attendance records from a specific report URL."""
        # Select both email and the intervals to get join/leave times.
        url_with_params = f"{report_url}?$select=emailAddress,attendanceIntervals"
        try:
            resp = requests.get(url_with_params, headers=self.headers)
            if resp.status_code == 200:
                return resp.json().get('value', [])
        except requests.RequestException as e:
            logger.error(f"Request error getting attendance records from {report_url}: {e}")
        return []
