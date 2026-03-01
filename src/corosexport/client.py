"""Coros API client with real working endpoints."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import requests
import bcrypt, hashlib

from .models import ActivitySummary, ActivityType, ExportFormat

logger = logging.getLogger(__name__)

COROS_BASE_URL = "https://teameuapi.coros.com"
AUTH_ENDPOINT = f"{COROS_BASE_URL}/account/login"
ACTIVITIES_ENDPOINT = f"{COROS_BASE_URL}/activity/query"
DOWNLOAD_ENDPOINT = f"{COROS_BASE_URL}/activity/detail/download"

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://training.coros.com",
    "Referer": "https://training.coros.com/",
    "Content-Type": "application/json",
}


class CorosAuthError(Exception):
    pass


class CorosAPIError(Exception):
    pass


def _compute_coros_bcrypt(password: str, *, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
    """Compute the bcrypt hash and salt used for Coros authentication.

    This mirrors the frontend logic: r = genSaltSync(10); c = hashSync(ke(o), r).
    We currently model ``ke(o)`` as ``md5(password).hexdigest()``.

    The function is factored out so tests can verify that for a given
    password and a fixed salt we reproduce the browser's p1 (hash).
    """

    # ke(o) equivalent in Python
    password_md5_hex = hashlib.md5(password.encode("utf-8")).hexdigest()

    if salt is None:
        salt = bcrypt.gensalt(rounds=10)

    hashed = bcrypt.hashpw(password_md5_hex.encode("utf-8"), salt)
    return hashed, salt


class CorosClient:
    def __init__(self, email: str, password: str, timeout: int = 30):
        self.email = email
        self.password = password
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(BROWSER_HEADERS)
        self.accesstoken: Optional[str] = None
        self.user_id: Optional[str] = None

    def _check_api_response(self, data: Dict[str, Any]) -> None:
        """Check API response for errors and raise appropriate exceptions.
        
        Args:
            data: The JSON response data from Coros API
            
        Raises:
            CorosAuthError: If the access token is invalid (code 1019)
            CorosAPIError: For other API errors
        """
        if data.get("result") != "0000":
            error_message = data.get("message", "Unknown error")
            result_code = data.get("result", "unknown")
            
            # Handle invalid access token specifically
            if result_code == "1019":
                raise CorosAuthError(f"Access token is invalid: {error_message}")
            else:
                raise CorosAPIError(f"API error (code {result_code}): {error_message}")

    def authenticate(self) -> bool:
        """Authenticate with real Coros API."""
        logger.info(f"Authenticating with Coros as {self.email}")

        # replicate: r = genSaltSync(10); c = hashSync(ke(o), r)
        hashed, salt = _compute_coros_bcrypt(self.password)

        payload = {
            "account": self.email,
            "accountType": 2,
            "p1": hashed.decode("utf-8"),
            "p2": salt.decode("utf-8"),
        }

        try:
            response = self.session.post(
                AUTH_ENDPOINT, json=payload, timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            if data.get("result") != "0000":
                raise CorosAuthError(
                    f"Auth failed: {data.get('message', 'Unknown error')}"
                )

            self.accesstoken = data["data"]["accessToken"]
            self.user_id = str(data["data"]["userId"])
            self.session.cookies["CPL-coros-token"] = self.accesstoken
            #self.session.cookies["CPL-coros-region"] = "3"

            logger.info("✅ Authentication successful")
            return True

        except requests.RequestException as e:
            raise CorosAuthError(f"Network error: {e}") from e

    def get_activities(self, limit: int = 200) -> List[ActivitySummary]:
        if not self.accesstoken:
            raise CorosAPIError("Not authenticated. Call authenticate() first.")
        
        limit = 200 if limit > 200 else limit

        params = {"size": limit, "pageNumber": 1, "modeList": ""}
        headers = {
            "accesstoken": self.accesstoken,
            "yfheader": f'{{"userId":"{self.user_id}"}}'
        }
        response = self.session.get(ACTIVITIES_ENDPOINT, params=params, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        self._check_api_response(data)

        total_pages = data.get("data", {}).get("totalPage", 1)

        all_coros_activities = []
        all_coros_activities.extend(data.get("data", {}).get("dataList", []))

        for page in range(2, total_pages + 1):
            params["pageNumber"] = page
            response = self.session.get(ACTIVITIES_ENDPOINT, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            self._check_api_response(data)
            all_coros_activities.extend(data.get("data", {}).get("dataList", []))

        activities = []
        for act in all_coros_activities:
            try:
                summary = ActivitySummary(
                    activity_id=str(act["labelId"]),
                    activity_name=act.get("name", "Unnamed"),
                    activity_type=ActivityType.from_sport_type(act.get("sportType", 999)),
                    start_time=datetime.fromtimestamp(act["startTime"]),
                    end_time=datetime.fromtimestamp(act["endTime"]),
                    workout_seconds=act.get("workoutTime", 0),
                    total_seconds=act.get("totalTime", 0),
                    distance_meters=float(act.get("distance", 0)) 
                )
                activities.append(summary)
            except Exception as e:
                logger.warning(f"Failed to parse activity: {e}")
        
        return activities

    def download_activity_file(
        self, activity_id: str, activity_type: ActivityType, file_format: ExportFormat, output_path: str
    ) -> bool:
        """Download activity file."""
        if not self.accesstoken:
            raise CorosAPIError("Not authenticated.")
        
        params = {"labelId": activity_id, "sportType": activity_type.to_sport_type(), "fileType": file_format.to_file_type()}
        headers = {
            "accesstoken": self.accesstoken,
            "yfheader": f'{{"userId":"{self.user_id}"}}'
        }
        response = self.session.get(DOWNLOAD_ENDPOINT, params=params, headers=headers)
        response.raise_for_status()
        
        # Check if response is JSON (error response) or binary (file content)
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            data = response.json()
            self._check_api_response(data)

        file_url = data.get("data", {}).get("fileUrl", None)
        if file_url is None:
            return False
        
        response = self.session.get(file_url, params=params, headers=headers)
        response.raise_for_status()
        
        with open(output_path, "wb") as f:
            f.write(response.content)
        return True