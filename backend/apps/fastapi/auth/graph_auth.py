import logging
import msal
from typing import Optional

from backend.apps.libs.utils.config.config import settings

logger = logging.getLogger(__name__)


class GraphAuth:
    """
    Handles authentication with Microsoft Graph API using the OAuth2 Client Credentials flow.
    It caches the token in memory to optimize performance.
    """

    def __init__(self):
        self._token_cache = {}
        self.authority = f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}"
        self.scope = [settings.GRAPH_SCOPE]

        self.app = msal.ConfidentialClientApplication(
            client_id=settings.AZURE_CLIENT_ID,
            authority=self.authority,
            client_credential=settings.AZURE_CLIENT_SECRET,
        )

    def get_token(self) -> Optional[str]:
        """
        Retrieves an access token for Microsoft Graph API.

        Tries to get a token from the cache first. If not available or expired,
        it acquires a new token from Azure AD.

        Returns:
            An access token string if successful, otherwise None.
        """
        accounts = self.app.get_accounts()
        result = self.app.acquire_token_silent(self.scope, account=accounts[0] if accounts else None)

        if not result:
            logger.info("No suitable token in cache. Acquiring a new one from AAD.")
            result = self.app.acquire_token_for_client(scopes=self.scope)

        if "access_token" in result:
            logger.info("Access token acquired successfully.")
            return result["access_token"]
        else:
            error_details = result.get("error_description", "No error description provided.")
            logger.error(f"Failed to acquire access token: {error_details}")
            return None


graph_auth_manager = GraphAuth()

def get_auth_token() -> str:
    """
    Dependency injector for FastAPI to get the auth token.
    Raises an exception if the token cannot be obtained.
    """
    token = graph_auth_manager.get_token()
    if not token:
        raise Exception("Could not authenticate with Microsoft Graph API.")
    return token
