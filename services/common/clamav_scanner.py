"""ClamAV Scanner Service."""
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from prometheus_client import Histogram, Counter
import os

LOGGER = logging.getLogger(__name__)

CLAMAV_SCAN_DURATION = Histogram(
    "clamav_scan_duration_seconds",
    "Time taken to scan content with ClamAV",
    labelnames=("result",),
)
UPLOAD_QUARANTINED = Counter(
    "upload_quarantined_total",
    "Total uploads quarantined by ClamAV",
    labelnames=("threat_name",),
)

class ScanStatus(Enum):
    CLEAN = "clean"
    QUARANTINED = "quarantined"
    SCAN_PENDING = "scan_pending"
    ERROR = "error"

@dataclass
class ScanResult:
    status: ScanStatus
    threat_name: Optional[str] = None
    error_message: Optional[str] = None

class ClamAVScanner:
    def __init__(self, socket_path: Optional[str] = None, host: Optional[str] = None, port: Optional[int] = None):
        self._socket_path = socket_path or os.environ.get("SA01_CLAMAV_SOCKET", "/var/run/clamav/clamd.sock")
        self._host = host or os.environ.get("SA01_CLAMAV_HOST")
        self._port = port or int(os.environ.get("SA01_CLAMAV_PORT", "3310"))

    def _get_clamd(self):
        import pyclamd
        # Try UNIX socket
        try:
            client = pyclamd.ClamdUnixSocket(self._socket_path)
            if client.ping():
                return client
        except Exception as exc:
            LOGGER.debug("ClamAV UNIX socket connection failed", extra={"error": str(exc), "path": self._socket_path})

        # Try Network socket
        if self._host:
            try:
                client = pyclamd.ClamdNetworkSocket(self._host, self._port, timeout=30)
                if client.ping():
                    return client
            except Exception as exc:
                LOGGER.debug("ClamAV Network socket connection failed", extra={"error": str(exc), "host": self._host, "port": self._port})
        
        raise ConnectionError("ClamAV unavailable")

    def scan_bytes(self, content: bytes) -> ScanResult:
        start = time.time()
        try:
            try:
                clamd = self._get_clamd()
            except ConnectionError as exc:
                return ScanResult(status=ScanStatus.ERROR, error_message=str(exc))

            result = clamd.scan_stream(content)
            duration = time.time() - start
            
            if result is None:
                CLAMAV_SCAN_DURATION.labels(result="clean").observe(duration)
                return ScanResult(status=ScanStatus.CLEAN)
            
            if 'stream' in result:
                status, threat = result['stream']
                if status == 'FOUND':
                    CLAMAV_SCAN_DURATION.labels(result="threat").observe(duration)
                    UPLOAD_QUARANTINED.labels(threat_name=threat).inc()
                    return ScanResult(status=ScanStatus.QUARANTINED, threat_name=threat)
            
            CLAMAV_SCAN_DURATION.labels(result="clean").observe(duration)
            return ScanResult(status=ScanStatus.CLEAN)

        except ImportError:
            return ScanResult(status=ScanStatus.SCAN_PENDING, error_message="pyclamd not installed")
        except Exception as exc:
            duration = time.time() - start
            CLAMAV_SCAN_DURATION.labels(result="error").observe(duration)
            LOGGER.exception("ClamAV scan error")
            return ScanResult(status=ScanStatus.ERROR, error_message=str(exc))
            
    def ping(self) -> bool:
        try:
            self._get_clamd()
            return True
        except Exception:
            return False
