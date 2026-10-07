# Binance Order Book

A real-time Binance order book built in Python using REST and WebSocket market data.

The application maintains a local copy of the Binance order book by combining an initial REST API snapshot with continuous WebSocket depth updates. It handles event sequencing, detects gaps in the update stream, resynchronizes when necessary, and displays the current top levels of the order book directly in the terminal.

## Features

- Real-time Binance market depth via WebSockets
- Initial order book snapshot via REST API
- REST/WebSocket order book synchronization
- Local bid and ask book maintenance
- Binance update ID sequence handling
- Automatic gap detection and resynchronization
- WebSocket reconnection with exponential backoff
- Configurable ping interval and timeout
- Subscribe and unsubscribe support
- Asynchronous processing with `asyncio`
- Live terminal order book display
- Best bid, best ask, spread, and update ID display

## How It Works

A local order book cannot be built reliably by simply listening to WebSocket events after startup. The application first buffers incoming depth events while retrieving a REST snapshot.

```text
                    Binance
                       │
              ┌────────┴────────┐
              │                 │
              ▼                 ▼
          REST API          WebSocket
          Snapshot        Depth Updates
              │                 │
              │                 ▼
              │           Event Buffer
              │                 │
              └────────┬────────┘
                       │
                       ▼
                 Synchronization
                       │
                       ▼
               Local Order Book
                ┌─────────────┐
                │    Bids     │
                │    Asks     │
                └──────┬──────┘
                       │
                       ▼
                Terminal Display
```

### 1. WebSocket Connection

The application connects to the Binance WebSocket API and subscribes to the depth stream:

```text
<symbol>@depth@100ms
```

For the current configuration:

```text
btcusdt@depth@100ms
```

If the initial WebSocket connection fails, the application retries using exponential backoff.

### 2. REST Snapshot

After starting the WebSocket receiver, the application retrieves an order book snapshot from the Binance REST API.

The snapshot contains:

- `lastUpdateId`
- Bid price levels
- Ask price levels

The current snapshot depth is configured to 100 levels.

### 3. Synchronization

WebSocket events received while the REST request is being performed are stored in a buffer.

Each Binance depth event contains:

```text
U = first update ID in the event
u = final update ID in the event
```

After receiving the REST snapshot, the application searches the buffered events for an update satisfying:

```text
U <= lastUpdateId + 1 <= u
```

Older events are ignored.

Once the correct event is found, the REST snapshot becomes the initial local order book and WebSocket updates are applied from that point forward.

### 4. Updating the Local Order Book

Bid and ask updates are applied to local dictionaries.

For each price level:

```text
quantity == 0  → remove the price level
quantity > 0   → insert or update the price level
```

The application tracks the latest processed update ID as it processes the stream.

### 5. Gap Detection

While processing live updates, the application verifies that incoming events continue from the current local update ID.

If the expected sequence is broken:

```text
GAP DETECTED - RESYNCHRONIZING
```

the application retrieves a new REST snapshot and synchronizes the local order book again.

## Terminal Display

The current version displays the top 10 BTCUSDT bid and ask levels.

Example layout:

```text
╔═══════════════════════════════════════════════════════════════╗
║                    BTCUSDT ORDER BOOK                        ║
╠═══════════════════════════════╦═══════════════════════════════╣
║             BIDS              ║             ASKS              ║
╠═══════════════╦═══════════════╬═══════════════╦═══════════════╣
║     PRICE     ║   QUANTITY    ║     PRICE     ║   QUANTITY    ║
╠═══════════════╬═══════════════╬═══════════════╬═══════════════╣
║      ...      ║      ...      ║      ...      ║      ...      ║
╚═══════════════╩═══════════════╩═══════════════╩═══════════════╝
```

The application also displays:

```text
Best Bid | Best Ask | Spread | Update ID
```

The terminal display refreshes once per second.

## Project Structure

```text
.
├── config.py
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
├── logs/
│   └── logfile.log
└── src/
    └── binance.py
```

### Files

| File | Description |
| --- | --- |
| `main.py` | Application entry point and asynchronous task orchestration |
| `config.py` | Binance endpoints and runtime configuration |
| `src/binance.py` | REST, WebSocket, synchronization, and order book implementation |
| `requirements.txt` | Python dependencies |
| `.gitignore` | Files excluded from version control |

Log files and Python cache files are excluded from Git.

## Requirements

- Python 3
- `websockets`
- `requests`

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Running

Run the application from the project root:

```bash
python main.py
```

The current configuration uses:

```text
BTCUSDT
```

After startup, the application will:

1. Connect to the Binance WebSocket API.
2. Subscribe to BTCUSDT depth updates.
3. Start buffering incoming WebSocket events.
4. Retrieve a REST order book snapshot.
5. Synchronize the snapshot with the buffered events.
6. Maintain the local order book using subsequent updates.
7. Display the top bid and ask levels in the terminal.

Stop the application with:

```text
Ctrl+C
```

## Configuration

Runtime configuration is defined in `config.py`.

The current settings include:

```python
PING_INTERVAL = 10
PING_TIMEOUT = 10

RETRY_DELAY = 1
MAX_RETRY_DELAY = 30

DEPTH_LIMIT = 100
```

The WebSocket connection starts with a one-second retry delay and uses exponential backoff up to a maximum delay of 30 seconds.

## Technologies

- Python
- asyncio
- WebSockets
- REST APIs
- Binance Spot Market Data

## Purpose

This project was built to explore real-time market data processing and the synchronization challenges involved in maintaining a local order book from multiple asynchronous data sources.

Concepts demonstrated by the project include:

- Asynchronous programming
- WebSocket communication
- REST API integration
- Event buffering
- Sequence synchronization
- Gap detection and recovery
- Local state management
- Real-time terminal visualization

## Disclaimer

This project is intended for educational and development purposes. It consumes public Binance market data and does not place or manage trades.
