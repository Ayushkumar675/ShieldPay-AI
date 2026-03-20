# ShieldPay AI — Deployment Guide

## Quick Start (Development)

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB (local or Atlas)
- Redis (optional for caching)

### 1. Backend Setup

```bash
cd "c:\ShieldPay AI\backend"

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate synthetic data
python data\generate_dataset.py

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: http://localhost:8000/docs

### 2. Frontend Setup

```bash
cd "c:\ShieldPay AI\frontend"

# Install dependencies
npm install

# Start dev server
npm run dev
```

Dashboard available at: http://localhost:5173

### 3. Environment Variables (.env)

Create `backend/.env`:
```
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=shieldpay
JWT_SECRET_KEY=your-super-secret-key-change-me
WEATHER_API_KEY=your-openweathermap-key
TRAFFIC_API_KEY=your-tomtom-key
```

## Production Deployment (Docker)

### docker-compose.yml
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - MONGODB_URL=mongodb://mongo:27017
    depends_on: [mongo, redis]

  frontend:
    build: ./frontend
    ports: ["3000:80"]

  mongo:
    image: mongo:7
    volumes: ["mongo_data:/data/db"]
    ports: ["27017:27017"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

volumes:
  mongo_data:
```

## Scaling Strategy

| Component | Strategy |
|-----------|---------|
| Backend | Horizontal pod autoscaling (K8s) behind load balancer |
| MongoDB | Atlas managed cluster with read replicas |
| Redis | Cluster mode for trigger state distribution |
| AI Models | GPU inference pods for fraud detection at scale |
| Scheduler | Leader-election pattern for single active scheduler |

## Liquidity Protection

1. **Reserve ratio**: 30% minimum premium reserve maintained
2. **Payout throttle**: Auto-activates when claim spike or liquidity drop detected
3. **Reinsurance**: Integration point for reinsurance partner API
4. **Circuit breaker**: Halts all payouts if reserve < 10%
