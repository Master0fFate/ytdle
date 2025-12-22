import socket
import urllib.request
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class NetworkStatus:
    ONLINE = "Online"
    OFFLINE = "Offline"
    CHECKING = "Checking"


def check_internet_connection(timeout: float = 5.0, test_host: str = "8.8.8.8", test_port: int = 53) -> bool:
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((test_host, test_port))
        return True
    except socket.error:
        return False


def check_http_connection(url: str = "https://www.google.com", timeout: float = 5.0) -> bool:
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except Exception:
        return False


class NetworkMonitor:
    def __init__(self):
        self._last_status: Optional[bool] = None
        self._timeout = 5.0

    def check(self) -> bool:
        result = check_internet_connection(timeout=self._timeout)
        self._last_status = result
        logger.info(f"Network status: {NetworkStatus.ONLINE if result else NetworkStatus.OFFLINE}")
        return result

    def get_status(self) -> str:
        if self._last_status is None:
            return NetworkStatus.CHECKING
        return NetworkStatus.ONLINE if self._last_status else NetworkStatus.OFFLINE

    def is_online(self) -> Optional[bool]:
        return self._last_status
