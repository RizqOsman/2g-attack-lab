# GSM C2 Dashboard - Quick Reference

## Quick Start

```bash
# Start the application
./start.sh

# Or manually
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Configuration (.env)

```env
VTY_HOST=localhost
VTY_MSC_PORT=4242              # Osmo-MSC/NITB control port
VTY_BTS_PORT=4241              # Osmo-BTS configuration port
HLR_DATABASE_PATH=/var/lib/osmocom/hlr.sqlite3
OSMOCOM_LOG_PATH=/var/log/osmocom/osmo-nitb.log
APP_PORT=8000
DEBUG_MODE=False
```

## API Endpoints Cheat Sheet

### System Status
```bash
curl http://localhost:8000/api/status
```

### List Subscribers
```bash
curl http://localhost:8000/api/subscribers
```

### Set Encryption to A5/0 (Attack Mode)
```bash
curl -X POST http://localhost:8000/api/config/encryption \
  -H "Content-Type: application/json" \
  -d '{"mode": "A5/0"}'
```

### Set Encryption to A5/1 (Normal)
```bash
curl -X POST http://localhost:8000/api/config/encryption \
  -H "Content-Type: application/json" \
  -d '{"mode": "A5/1"}'
```

### Send Spoofed SMS
```bash
curl -X POST http://localhost:8000/api/attack/sms-spoof \
  -H "Content-Type: application/json" \
  -d '{
    "imsi": "001010000000001",
    "sender_id": "ALERT",
    "message": "Security test message"
  }'
```

## WebSocket Live Feed

### Python Client
```python
import asyncio
import websockets
import json

async def monitor():
    uri = "ws://localhost:8000/ws/live-feed"
    async with websockets.connect(uri) as ws:
        while True:
            event = json.loads(await ws.recv())
            print(f"[{event['timestamp']}] {event['event_type']}: {event.get('imsi', 'N/A')}")

asyncio.run(monitor())
```

### JavaScript/Browser
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/live-feed');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(`${data.event_type}: IMSI ${data.imsi || 'N/A'}`);
};
```

## Common VTY Commands

The application executes these VTY commands automatically, but here's what happens under the hood:

### Encryption Configuration (Port 4241 - BTS)
```
enable
configure terminal
network
bts 0
encryption a5 0    # or 'encryption a5 1'
end
write
```

### SMS Injection (Port 4242 - MSC)
```
enable
subscriber imsi <IMSI> sms sender <SENDER> send <MESSAGE>
```

### Manual VTY Access
```bash
# Connect to MSC
telnet localhost 4242

# Connect to BTS
telnet localhost 4241
```

## Event Types

WebSocket events you'll receive:

- `IMSI_ATTACH`: Phone connected to network
- `IMSI_DETACH`: Phone disconnected
- `LOCATION_UPDATE`: Phone changed location
- `AUTH_REQUEST`: Authentication attempt
- `SMS_DELIVERY`: SMS message sent/received
- `UNKNOWN`: Other relevant events

## Troubleshooting

### Connection Refused
```bash
# Check if Osmocom is running
systemctl status osmo-nitb
# or
ps aux | grep osmo

# Test VTY manually
telnet localhost 4242
```

### Database Not Found
```bash
# Check database exists
ls -la /var/lib/osmocom/hlr.sqlite3

# Update path in .env
HLR_DATABASE_PATH=/path/to/your/hlr.sqlite3
```

### No WebSocket Events
```bash
# Check log file
ls -la /var/log/osmocom/osmo-nitb.log

# Try syslog
tail -f /var/log/syslog | grep osmo
```

## URLs

- **Documentation**: http://localhost:8000/docs
- **API Root**: http://localhost:8000/
- **Alternative Docs**: http://localhost:8000/redoc
- **WebSocket**: ws://localhost:8000/ws/live-feed

## Project Structure

```
app/
├── main.py          → FastAPI app & lifespan
├── config.py        → Settings (loads .env)
├── models/
│   ├── schemas.py   → Pydantic models
│   └── database.py  → SQLAlchemy + SQLite
├── services/
│   ├── vty_client.py       → Telnet to Osmocom
│   ├── osmocom_service.py  → Business logic
│   ├── sms_service.py      → SMS injection
│   └── log_monitor.py      → Real-time monitoring
└── api/
    ├── routes.py    → REST endpoints
    └── websocket.py → WebSocket handler
```

## Security Notes

⚠️ **IMPORTANT**:
- This is for **authorized security research only**
- Default has **no authentication**
- CORS allows all origins (`*`)
- Deploy in **isolated lab network**
- Never use on production networks

## License & Legal

This application is for authorized security research in controlled laboratory environments. Unauthorized use may violate telecommunications laws. Use at your own risk.
