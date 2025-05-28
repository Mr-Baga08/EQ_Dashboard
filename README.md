# README.md
# Multi-Client Trading Platform

A comprehensive trading platform built with FastAPI and Next.js, featuring real-time market data, multi-client order management, and Motilal Oswal API integration.

## 🚀 Features

### Core Functionality
- **Multi-Client Management**: Handle multiple trading accounts simultaneously
- **Real-time Market Data**: Live price feeds and portfolio updates via WebSocket
- **Order Management**: Place, modify, and cancel orders across multiple clients
- **Batch Operations**: Execute orders for multiple clients with a single click
- **Token-based Exits**: Exit all positions for a specific token across clients
- **Portfolio Tracking**: Real-time P&L calculations and margin monitoring

### Trading Features
- **Trade Types**: MTF, Intraday, and Delivery
- **Order Types**: Market and Limit orders
- **Execution Types**: Buy, Sell, and Exit operations
- **Margin Calculations**: Real-time margin requirements and availability
- **Position Management**: Track active and closed positions

### Technical Features
- **Motilal API Integration**: Complete integration with Motilal Oswal trading APIs
- **WebSocket Support**: Real-time updates for prices and portfolio changes
- **Token Management**: CSV-based token loading and management
- **Security**: JWT authentication and secure API communication
- **Scalability**: Microservices architecture with horizontal scaling
- **Monitoring**: Comprehensive logging and health checks

## 🏗️ Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for real-time data caching
- **Authentication**: JWT-based authentication
- **API Integration**: Motilal Oswal API client
- **WebSocket**: Real-time communication with frontend

### Frontend (Next.js)
- **Framework**: Next.js 13+ with TypeScript
- **Styling**: Tailwind CSS with responsive design
- **State Management**: Zustand for global state
- **Real-time**: Socket.IO client for WebSocket connections
- **Forms**: React Hook Form with Zod validation
- **UI Components**: Custom components with Heroicons

### Infrastructure
- **Containerization**: Docker and Docker Compose
- **Orchestration**: Kubernetes manifests
- **Reverse Proxy**: Nginx with load balancing
- **CI/CD**: GitHub Actions pipeline
- **Monitoring**: Health checks and logging

## 📦 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- Motilal Oswal API credentials

### Development Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd trading-platform
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start the development environment**
```bash
docker-compose up -d
```

4. **Load token data**
```bash
# Edit data/tokens.csv with your tokens
# Tokens will be automatically loaded on backend startup
```

5. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Production Deployment

1. **Build production images**
```bash
docker-compose -f infra/docker/docker-compose.prod.yml build
```

2. **Deploy with Kubernetes**
```bash
kubectl apply -f infra/k8s/
```

3. **Monitor deployment**
```bash
kubectl get pods -n trading-platform
kubectl logs -f deployment/backend -n trading-platform
```

## 📚 API Documentation

The API provides comprehensive endpoints for:

### Client Management
- `GET /api/v1/clients` - List all clients with portfolio data
- `GET /api/v1/clients/{id}` - Get client details
- `GET /api/v1/clients/{id}/portfolio` - Get detailed portfolio

### Order Management
- `POST /api/v1/orders/place` - Place single order
- `POST /api/v1/orders/execute-all` - Execute batch orders

### Trade Management
- `GET /api/v1/trades` - List trades with filters
- `POST /api/v1/trades/{id}/exit` - Exit specific trade
- `POST /api/v1/trades/exit-by-token/{token_id}` - Batch exit by token

### Token Management
- `GET /api/v1/tokens/search` - Search tokens
- `GET /api/v1/tokens/{id}/holders` - Get token holders

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `POSTGRES_SERVER` | PostgreSQL server host | `localhost` |
| `POSTGRES_USER` | Database user | `trading_user` |
| `POSTGRES_PASSWORD` | Database password | `trading_password` |
| `REDIS_HOST` | Redis server host | `localhost` |
| `MOTILAL_BASE_URL` | Motilal API base URL | UAT URL |
| `MOTILAL_API_KEY` | Your Motilal API key | Required |
| `SECRET_KEY` | JWT secret key | Generate secure key |

### Token Configuration

Edit `data/tokens.csv` to add your trading tokens:

```csv
symbol,token_id,exchange,instrument_type,lot_size,tick_size
RELIANCE,2885,NSE,EQ,1,0.05
TCS,11536,NSE,EQ,1,0.05
```

### Client Configuration

Add client details through the API or directly in the database:

```sql
INSERT INTO clients (name, motilal_client_id, api_key, encrypted_password, two_fa) 
VALUES ('Client Name', 'MOT_ID', 'api_key', 'encrypted_pwd', 'DD/MM/YYYY');
```

## 🚀 Usage

### Dashboard Operations

1. **Select Token**: Use the search interface to find and select tokens
2. **Configure Order**: Set trade type (MTF/Intraday/Delivery), order type (Market/Limit), and execution type (Buy/Sell/Exit)
3. **Set Quantities**: Enter quantities for each client (0 to skip)
4. **Execute Orders**: Click "Execute All Orders" to place orders for all clients

### Client Management

1. **View Details**: Click on any client to see detailed portfolio and active trades
2. **Monitor P&L**: Real-time profit/loss updates for all positions
3. **Manage Positions**: Exit individual trades or manage margins

### Batch Exit Operations

1. **Token Exit**: Navigate to `/exit/{token_id}` to exit all positions for a specific token
2. **Client Selection**: Choose which clients to include in the batch exit
3. **Confirm Exit**: Review and confirm the batch exit operation

## 🔒 Security

### API Security
- JWT-based authentication for all API endpoints
- Rate limiting on critical endpoints
- CORS protection with configurable origins
- Input validation and sanitization

### Data Security
- Encrypted password storage for client credentials
- Secure API key management
- Database connection encryption
- SSL/TLS for all external communications

### Trading Security
- Order validation and risk checks
- Margin requirement validation
- Position limit enforcement
- Audit logging for all trading operations

## 📊 Monitoring & Logging

### Application Monitoring
- Health check endpoints for all services
- Real-time performance metrics
- Error tracking and alerting
- Database connection monitoring

### Trading Monitoring
- Order execution tracking
- P&L monitoring and alerts
- Position risk monitoring
- API usage analytics

### Logging
- Structured logging with JSON format
- Centralized log aggregation
- Error and exception tracking
- Trading activity audit logs

## 🧪 Testing

### Backend Testing
```bash
cd backend
pytest tests/ -v --cov=app
```

### Frontend Testing
```bash
cd frontend
npm test -- --coverage
```

### Integration Testing
```bash
docker-compose -f docker-compose.test.yml up --build
```

## 🔄 CI/CD Pipeline

### Continuous Integration
- Automated testing on all pull requests
- Code quality checks and linting
- Security vulnerability scanning
- Docker image building and scanning

### Continuous Deployment
- Automated deployment to staging environment
- Production deployment with approval gates
- Blue-green deployment strategy
- Automatic rollback on failure

## 📈 Performance Optimization

### Backend Optimization
- Database query optimization with indexes
- Redis caching for frequently accessed data
- Async/await for non-blocking operations
- Connection pooling for database and Redis

### Frontend Optimization
- Code splitting and lazy loading
- Image optimization and caching
- Bundle size optimization
- Service worker for offline functionality

### Infrastructure Optimization
- Horizontal scaling with load balancing
- CDN for static asset delivery
- Database read replicas for scaling
- Kubernetes auto-scaling

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database connectivity
docker-compose exec backend python -c "from app.core.database import engine; print('DB Connected')"

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

#### API Authentication Issues
```bash
# Check JWT token validity
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/v1/clients

# Reset authentication
# Restart backend service
docker-compose restart backend
```

#### Motilal API Issues
```bash
# Check API connectivity
curl -X POST https://openapi.motilaloswaluat.com/rest/login/v4/authdirectapi \
  -H "Content-Type: application/json" \
  -d '{"userid":"TEST","password":"test","2FA":"test"}'

# Verify API credentials in .env file
```

#### WebSocket Connection Issues
```bash
# Check WebSocket endpoint
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: test" \
  http://localhost:8000/ws/test
```

### Performance Issues

#### Slow Database Queries
```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Add indexes for commonly queried columns
CREATE INDEX CONCURRENTLY idx_trades_client_id ON trades(client_id);
CREATE INDEX CONCURRENTLY idx_trades_token_id ON trades(token_id);
CREATE INDEX CONCURRENTLY idx_trades_status ON trades(status);
```

#### High Memory Usage
```bash
# Monitor memory usage
docker stats

# Optimize Redis memory
redis-cli CONFIG SET maxmemory 512mb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make changes and test thoroughly
4. Submit a pull request with detailed description

### Code Standards
- Follow PEP 8 for Python code
- Use TypeScript strict mode for frontend
- Write comprehensive tests for new features
- Document all API endpoints

### Pull Request Guidelines
- Include tests for new functionality
- Update documentation as needed
- Ensure CI pipeline passes
- Request review from maintainers

## 🆘 Support

### Documentation
- API Documentation: http://localhost:8000/docs
- Architecture Diagrams: See `/docs/diagrams/`
- Deployment Guide: See `/docs/DEPLOYMENT.md`

### Community
- GitHub Issues: Report bugs and feature requests
- Discussions: Community discussions and Q&A
- Wiki: Additional documentation and guides

### Professional Support
For enterprise support and custom development:
- Email: support@tradingplatform.com
- Documentation: https://docs.tradingplatform.com
- Enterprise Plans: Contact sales team

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Motilal Oswal**: API integration and trading infrastructure
- **FastAPI Community**: Excellent documentation and support
- **Next.js Team**: Modern React framework and tools
- **Open Source Contributors**: All the amazing libraries used

---

## 🏁 Getting Started Checklist

- [ ] Clone the repository
- [ ] Set up environment variables
- [ ] Configure Motilal API credentials
- [ ] Load token data from CSV
- [ ] Add client information
- [ ] Start development environment
- [ ] Access dashboard at http://localhost:3000
- [ ] Test order placement with small quantities
- [ ] Monitor logs for any issues
- [ ] Set up production environment

## 📋 Project Status

### Current Version: v1.0.0

#### ✅ Completed Features
- Multi-client order management
- Real-time portfolio tracking
- Motilal API integration
- WebSocket real-time updates
- Batch order execution
- Token-based position exits
- Responsive web interface
- Docker containerization
- Kubernetes deployment
- CI/CD pipeline

#### 🔄 In Progress
- Advanced analytics dashboard
- Mobile application
- Email/SMS notifications
- Advanced order types
- Risk management tools

#### 📋 Planned Features
- Options trading support
- Algo trading integration
- Portfolio optimization
- Reporting and compliance
- Mobile push notifications
- Advanced charting

---

**Ready to start trading? Follow the Quick Start guide above and you'll be executing orders in minutes!**