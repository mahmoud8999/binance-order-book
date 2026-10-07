from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

BINANCE_URI = "wss://stream.binance.com:9443/ws"
BINANCE_URL = "https://api.binance.com/api/v3/depth"

PING_INTERVAL = 10
PING_TIMEOUT = 10
RETRY_DELAY = 1
MAX_RETRY_DELAY = 30

DEPTH_LIMIT = 100

LOGFILE = PROJECT_ROOT / "logs" / "logfile.log"
