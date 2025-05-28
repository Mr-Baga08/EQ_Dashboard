# File Locations for Generated Code

This document shows where to paste each piece of generated code:

## Backend Files

### Core Application
- `backend/app/main.py` - Main FastAPI application
- `backend/app/core/config.py` - Configuration settings
- `backend/app/core/database.py` - Database setup

### Models
- `backend/app/models/client.py` - Client model
- `backend/app/models/token.py` - Token model  
- `backend/app/models/trade.py` - Trade model
- `backend/app/models/order.py` - Order model

### Schemas
- `backend/app/schemas/client.py` - Client schemas
- `backend/app/schemas/token.py` - Token schemas
- `backend/app/schemas/trade.py` - Trade schemas
- `backend/app/schemas/order.py` - Order schemas

### Services
- `backend/app/services/motilal_service.py` - Motilal API integration
- `backend/app/services/websocket_manager.py` - WebSocket management
- `backend/app/utils/csv_loader.py` - CSV token loader

### API Endpoints
- `backend/app/api/v1/endpoints/clients.py` - Client endpoints
- `backend/app/api/v1/endpoints/trades.py` - Trade endpoints
- `backend/app/api/v1/endpoints/orders.py` - Order endpoints
- `backend/app/api/v1/endpoints/tokens.py` - Token endpoints
- `backend/app/api/v1/api.py` - API router

## Frontend Files

### Core Files
- `frontend/src/types/index.ts` - TypeScript definitions
- `frontend/src/services/api.ts` - API service functions
- `frontend/src/services/websocket.ts` - WebSocket service
- `frontend/src/store/index.ts` - Zustand store

### Components
- `frontend/src/components/common/Layout.tsx` - Main layout
- `frontend/src/components/common/Header.tsx` - Header component
- `frontend/src/components/common/Sidebar.tsx` - Sidebar component
- `frontend/src/components/dashboard/OrderForm.tsx` - Order form
- `frontend/src/components/dashboard/ClientTable.tsx` - Client table
- `frontend/src/components/dashboard/TokenSelector.tsx` - Token selector
- `frontend/src/components/client/ClientPortfolio.tsx` - Client portfolio
- `frontend/src/components/client/ActiveTrades.tsx` - Active trades
- `frontend/src/components/client/TradeRow.tsx` - Trade row component
- `frontend/src/components/exit/TokenExitTable.tsx` - Token exit table

### Pages
- `frontend/src/pages/index.tsx` - Dashboard page
- `frontend/src/pages/client/[id].tsx` - Client detail page
- `frontend/src/pages/exit/[token].tsx` - Token exit page

## Infrastructure Files

### Docker
- `infra/docker/docker-compose.yml` - Development Docker setup
- `infra/docker/docker-compose.prod.yml` - Production Docker setup
- `infra/docker/nginx.conf` - Nginx configuration

### Kubernetes
- `infra/k8s/namespace.yaml` - Kubernetes namespace
- `infra/k8s/postgres.yaml` - PostgreSQL deployment
- `infra/k8s/redis.yaml` - Redis deployment
- `infra/k8s/backend.yaml` - Backend deployment
- `infra/k8s/frontend.yaml` - Frontend deployment
- `infra/k8s/ingress.yaml` - Ingress configuration

### CI/CD
- `.github/workflows/ci.yml` - GitHub Actions workflow

## Data Files
- `data/tokens.csv` - Token data (already created)
- `data/sample_clients.sql` - Sample client data

## Documentation
- `README.md` - Main documentation (already created)
- `docs/ARCHITECTURE.md` - Architecture documentation
- `docs/DEPLOYMENT.md` - Deployment guide

## Notes
- All empty files have been created with basic structure
- Copy and paste the generated code into the corresponding files
- Make sure to configure the .env file with your API credentials
- Run the setup as described in the README.md
