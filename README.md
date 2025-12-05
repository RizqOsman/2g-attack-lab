# GSM C2 Dashboard

**Command & Control Dashboard for GSM Laboratory Security Research**

A high-performance FastAPI application for managing and monitoring a GSM security research laboratory using PlutoSDR and the Osmocom stack (Osmo-NITB/Osmo-MSC).

---

## ⚠️ Legal Notice

This application is designed **exclusively** for authorized security research in controlled, shielded laboratory environments. The SMS spoofing and encryption manipulation features are powerful tools that must only be used in compliance with all applicable laws and regulations.

**Unauthorized use of this software to intercept communications, spoof identities, or disrupt telecommunications services is illegal and may result in severe criminal penalties.**

By using this software, you agree that you:
- Have proper authorization for security research
- Operate in a legally compliant, isolated laboratory environment
- Accept full responsibility for your use of this software

---

## Features

- 🔍 **Real-time Subscriber Monitoring**: Query HLR database for captured IMSIs, IMEIs, and activity
- 🔐 **Encryption Control**: Toggle BTS encryption between A5/0 (null cipher) and A5/1
- 📱 **SMS Injection**: Send spoofed SMS messages to target IMSIs
- 📡 **Live Event Streaming**: WebSocket-based real-time monitoring of IMSI attach/detach events
- ⚡ **Async Architecture**: Non-blocking asyncio implementation for high performance
- 📊 **Service Health Monitoring**: Check PlutoSDR and Osmocom service status

---

## Architecture

```
┌─────────────────┐
│  FastAPI App    │
│  (Port 8000)    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌──────────┐
│ VTY    │ │ HLR DB   │
│ Client │ │ (SQLite) │
└────┬───┘ └──────────┘
     │
  ┌──┴──┐
  ▼     ▼
┌────┐ ┌────┐
│MSC │ │BTS │
│4242│ │4241│
└────┘ └────┘
```

---

## Installation

### Prerequisites

- Python 3.9 or higher
- Running Osmocom stack (Osmo-NITB or Osmo-MSC + Osmo-BTS)
- PlutoSDR hardware (optional, for status checks)
- Access to Osmocom HLR database and log files

### Setup

1. **Clone or navigate to the project directory:**
   ```bash
   cd /Users/benbeckman/Documents/2g-attack-lab
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or on Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   nano .env
   ```

5. **Update `.env` configuration:**
   ```env
   # VTY Connection
   VTY_HOST=localhost
   VTY_MSC_PORT=4242
   VTY_BTS_PORT=4241
   
   # Database (adjust path to your HLR database)
   HLR_DATABASE_PATH=/var/lib/osmocom/hlr.sqlite3
   
   # Log File (adjust to your Osmocom log location)
   OSMOCOM_LOG_PATH=/var/log/osmocom/osmo-nitb.log
   
   # Application
   APP_HOST=0.0.0.0
   APP_PORT=8000
   DEBUG_MODE=True
   ```

---

## Usage

### Starting the Application

**Development Mode** (with auto-reload):
```bash
python -m app.main
```

**Production Mode** (with Uvicorn):
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Background Service** (using systemd - example):
```bash
# Create systemd service file
sudo nano /etc/systemd/system/gsm-c2.service
```

```ini
[Unit]
Description=GSM C2 Dashboard
After=network.target osmo-nitb.service

[Service]
Type=simple
User=your-username
WorkingDirectory=/Users/benbeckman/Documents/2g-attack-lab
Environment="PATH=/Users/benbeckman/Documents/2g-attack-lab/venv/bin"
ExecStart=/Users/benbeckman/Documents/2g-attack-lab/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable gsm-c2
sudo systemctl start gsm-c2
```

### Accessing the API

- **Interactive Documentation (Swagger UI)**: http://localhost:8000/docs
- **Alternative Documentation (ReDoc)**: http://localhost:8000/redoc
- **Root API Info**: http://localhost:8000/

---

## API Endpoints

### 1. **GET /api/status** - System Status Check

Check if PlutoSDR and Osmocom services are active.

**Example:**
```bash
curl http://localhost:8000/api/status
```

**Response:**
```json
{
  "pluto_sdr_active": true,
  "osmocom_active": true,
  "details": {
    "pluto_info": "PlutoSDR module loaded",
    "osmocom_info": "osmo-nitb is running"
  },
  "timestamp": "2025-12-04T10:00:00"
}
```

---

### 2. **GET /api/subscribers** - List All Subscribers

Query HLR database for all captured subscribers.

**Example:**
```bash
curl http://localhost:8000/api/subscribers
```

**Response:**
```json
{
  "subscribers": [
    {
      "imsi": "001010000000001",
      "msisdn": "12345",
      "imei": "353870080123456",
      "last_seen": "2025-12-04T09:30:00",
      "authorized": true
    }
  ],
  "total_count": 1,
  "timestamp": "2025-12-04T10:00:00"
}
```

---

### 3. **POST /api/config/encryption** - Configure BTS Encryption

Toggle encryption between A5/0 (null cipher) and A5/1.

**Example (Set to A5/0):**
```bash
curl -X POST http://localhost:8000/api/config/encryption \
  -H "Content-Type: application/json" \
  -d '{"mode": "A5/0"}'
```

**Request Body:**
```json
{
  "mode": "A5/0"  // or "A5/1"
}
```

**Response:**
```json
{
  "success": true,
  "mode": "A5/0",
  "message": "Encryption mode set to A5/0",
  "timestamp": "2025-12-04T10:00:00"
}
```

---

### 4. **POST /api/attack/sms-spoof** - Inject Spoofed SMS

Send a spoofed SMS to a target IMSI.

**Example:**
```bash
curl -X POST http://localhost:8000/api/attack/sms-spoof \
  -H "Content-Type: application/json" \
  -d '{
    "imsi": "001010000000001",
    "sender_id": "SECURITY",
    "message": "Test message from C2 dashboard"
  }'
```

**Request Body:**
```json
{
  "imsi": "001010000000001",
  "sender_id": "SECURITY",
  "message": "Test message from C2 dashboard"
}
```

**Response:**
```json
{
  "success": true,
  "imsi": "001010000000001",
  "message": "SMS injected to IMSI 001010000000001",
  "timestamp": "2025-12-04T10:00:00"
}
```

---

### 5. **WebSocket /ws/live-feed** - Real-Time Event Stream

Stream live events from Osmocom logs (IMSI attach/detach, SMS delivery, etc.).

**Python Client Example:**
```python
import asyncio
import websockets
import json

async def monitor_events():
    uri = "ws://localhost:8000/ws/live-feed"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            event = json.loads(message)
            print(f"[{event['timestamp']}] {event['event_type']}: IMSI {event.get('imsi', 'N/A')}")
            print(f"  Raw: {event['raw_log']}")

asyncio.run(monitor_events())
```

**JavaScript Client Example:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/live-feed');

ws.onopen = () => {
    console.log('Connected to live feed');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(`[${data.timestamp}] ${data.event_type}:`, data);
};

ws.onerror = (error) => {
    console.error('WebSocket error:', error);
};
```

**Event Format:**
```json
{
  "timestamp": "2025-12-04T10:15:00",
  "event_type": "IMSI_ATTACH",
  "imsi": "001010000000001",
  "details": {
    "location_area": "1",
    "cell_id": "1"
  },
  "raw_log": "Dec  4 10:15:00 lab osmo-nitb[1234]: Attach request from 001010000000001"
}
```

**Event Types:**
- `IMSI_ATTACH`: Subscriber attached to network
- `IMSI_DETACH`: Subscriber detached from network
- `LOCATION_UPDATE`: Location update request
- `AUTH_REQUEST`: Authentication request
- `SMS_DELIVERY`: SMS delivery event
- `UNKNOWN`: Other relevant events

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VTY_HOST` | Osmocom VTY host address | `localhost` |
| `VTY_MSC_PORT` | MSC/NITB VTY port | `4242` |
| `VTY_BTS_PORT` | BTS VTY port | `4241` |
| `VTY_TIMEOUT` | VTY connection timeout (seconds) | `10` |
| `HLR_DATABASE_PATH` | Path to HLR SQLite database | `/var/lib/osmocom/hlr.sqlite3` |
| `OSMOCOM_LOG_PATH` | Path to Osmocom log file | `/var/log/osmocom/osmo-nitb.log` |
| `APP_HOST` | Application host address | `0.0.0.0` |
| `APP_PORT` | Application port | `8000` |
| `DEBUG_MODE` | Enable debug logging | `False` |

---

## Troubleshooting

### Connection Refused to VTY

**Problem:** `Connection refused to localhost:4242`

**Solutions:**
1. Verify Osmocom is running:
   ```bash
   systemctl status osmo-nitb
   # or
   ps aux | grep osmo
   ```

2. Check VTY is enabled in Osmocom config:
   ```bash
   # In osmo-nitb.cfg or osmo-msc.cfg
   line vty
    bind 127.0.0.1
   ```

3. Test VTY connection manually:
   ```bash
   telnet localhost 4242
   ```

### Database Not Found

**Problem:** `Failed to query HLR database: [Errno 2] No such file or directory`

**Solutions:**
1. Verify database path:
   ```bash
   ls -la /var/lib/osmocom/hlr.sqlite3
   ```

2. Update `.env` with correct path
3. Ensure proper file permissions

### Log File Not Found

**Problem:** WebSocket events not streaming

**Solutions:**
1. Verify log file exists:
   ```bash
   ls -la /var/log/osmocom/osmo-nitb.log
   ```

2. Check syslog as alternative:
   ```bash
   tail -f /var/log/syslog | grep osmo
   ```

3. Update `OSMOCOM_LOG_PATH` in `.env`

---

## Development

### Project Structure

```
2g-attack-lab/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration management
│   ├── models/
│   │   ├── schemas.py       # Pydantic request/response models
│   │   └── database.py      # Database models and queries
│   ├── services/
│   │   ├── vty_client.py    # Async VTY communication
│   │   ├── osmocom_service.py  # Osmocom business logic
│   │   ├── sms_service.py   # SMS injection service
│   │   └── log_monitor.py   # Real-time log monitoring
│   ├── api/
│   │   ├── routes.py        # REST API endpoints
│   │   └── websocket.py     # WebSocket endpoints
│   └── utils/
│       └── helpers.py       # Utility functions
├── requirements.txt
├── .env.example
└── README.md
```

### Adding New Features

1. **New API Endpoint**: Add to `app/api/routes.py`
2. **New Service Logic**: Create in `app/services/`
3. **New Data Model**: Define in `app/models/schemas.py`

---

## Security Considerations

1. **Access Control**: This application has NO authentication by default. Deploy behind a firewall or add authentication middleware.

2. **CORS**: Currently allows all origins (`*`). Update `app/main.py` for production:
   ```python
   allow_origins=["https://your-frontend-domain.com"]
   ```

3. **HTTPS**: Use a reverse proxy (nginx) with SSL/TLS for production.

4. **Database Access**: HLR database is read-only by default. Ensure file permissions are restricted.

---

## License

This software is provided for educational and authorized security research purposes only.

---

## Support

For issues related to:
- **Osmocom**: Visit [Osmocom Wiki](https://osmocom.org/projects/cellular-infrastructure/wiki)
- **PlutoSDR**: Visit [Analog Devices PlutoSDR](https://www.analog.com/en/design-center/evaluation-hardware-and-software/evaluation-boards-kits/adalm-pluto.html)
- **This Application**: Open an issue in the project repository

---

**Built with ❤️ for Security Research**
