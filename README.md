# Smart Inventory Management System

A full-stack SaaS application designed for small businesses to track products, scan barcodes, predict stock depletion using machine learning, and automate restocking decisions.

## Features

- **Product Management**: Add, edit, delete, and track products with SKU, category, and stock levels
- **Barcode Scanning**: Use webcam to scan product barcodes for quick inventory updates
- **ML-Powered Predictions**: Forecast stock depletion dates using Prophet time series analysis
- **Vendor Management**: Compare vendor prices and get restocking recommendations
- **Smart Alerts**: Receive notifications for low stock and predicted depletion
- **Real-time Dashboard**: Monitor inventory status with color-coded indicators and charts
- **RESTful API**: Comprehensive API with JWT authentication and OpenAPI documentation

## Technology Stack

### Frontend
- React 18 with TypeScript
- Vite for build tooling
- Tailwind CSS for styling
- Recharts for data visualization
- React Query for API state management
- Zustand for client state management
- react-zxing for barcode scanning

### Backend
- FastAPI (Python 3.11+)
- SQLAlchemy 2.0 for ORM
- Alembic for database migrations
- Pydantic for data validation
- Celery for background tasks
- Redis for task queue and caching

### Machine Learning
- Prophet for time series forecasting
- scikit-learn for data preprocessing
- pandas for data manipulation

### Database
- PostgreSQL 15+

### DevOps
- Docker & Docker Compose
- GitHub Actions for CI/CD

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine + Docker Compose (Linux)
- Git
- (Optional) Node.js 18+ and Python 3.11+ for local development without Docker

## Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd smart-inventory-system
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   ```

   This will start:
   - PostgreSQL database on port 5432
   - Redis on port 6379
   - FastAPI backend on port 8000
   - React frontend on port 3000
   - Celery worker for background tasks
   - Celery beat for scheduled tasks

   **Optional: Seed with sample data** (first time setup)
   
   Edit `docker-compose.yml` and set `SEED_DATABASE: "true"` in the backend service, then:
   ```bash
   docker-compose up --build
   ```
   
   This will populate the database with:
   - 4 sample users (admin, manager, user roles)
   - 26 products across 6 categories
   - 6 vendors with pricing
   - 90 days of transaction history
   - Sample alerts
   
   See `backend/SEED_DATA_QUICK_START.md` for login credentials and details.

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Alternative API Docs: http://localhost:8000/redoc

4. **Stop all services**
   ```bash
   docker-compose down
   ```

5. **Stop and remove all data**
   ```bash
   docker-compose down -v
   ```

## Local Development Setup

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the backend directory:
   ```env
   DATABASE_URL=postgresql://inventory_user:inventory_pass@localhost:5432/inventory
   REDIS_URL=redis://localhost:6379/0
   JWT_SECRET=your-secret-key-change-in-production
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=15
   ENVIRONMENT=development
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **(Optional) Seed database with sample data**
   ```bash
   python seed_data.py
   ```
   See `backend/SEED_DATA_README.md` for details.

7. **Start the development server**
   ```bash
   uvicorn app.main:app --reload
   ```

8. **Start Celery worker (in separate terminal)**
   ```bash
   celery -A app.celery_app worker --loglevel=info
   ```

9. **Start Celery beat (in separate terminal)**
   ```bash
   celery -A app.celery_app beat --loglevel=info
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   Create a `.env` file in the frontend directory:
   ```env
   VITE_API_URL=http://localhost:8000
   ```

4. **Start the development server**
   ```bash
   npm run dev
   ```

## Project Structure

```
smart-inventory-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/          # API endpoint definitions
│   │   ├── core/                # Configuration and utilities
│   │   ├── models/              # SQLAlchemy database models
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── services/            # Business logic layer
│   │   ├── ml/                  # Machine learning services
│   │   └── main.py              # FastAPI application entry point
│   ├── alembic/                 # Database migrations
│   ├── tests/                   # Backend tests
│   ├── requirements.txt         # Python dependencies
│   └── Dockerfile               # Backend container configuration
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── pages/               # Page components
│   │   ├── services/            # API integration
│   │   ├── hooks/               # Custom React hooks
│   │   ├── store/               # State management
│   │   ├── types/               # TypeScript type definitions
│   │   └── utils/               # Utility functions
│   ├── public/                  # Static assets
│   ├── package.json             # Node.js dependencies
│   └── Dockerfile               # Frontend container configuration
├── docker-compose.yml           # Multi-container orchestration
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key API Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `POST /api/v1/auth/refresh` - Refresh JWT token
- `GET /api/v1/auth/me` - Get current user info

#### Products
- `GET /api/v1/products` - List all products
- `POST /api/v1/products` - Create new product
- `GET /api/v1/products/{id}` - Get product details
- `PUT /api/v1/products/{id}` - Update product
- `DELETE /api/v1/products/{id}` - Delete product

#### Inventory
- `POST /api/v1/inventory/adjust` - Adjust stock level
- `GET /api/v1/inventory/movements` - Get stock movements

#### Barcode
- `POST /api/v1/barcode/scan` - Process scanned barcode
- `GET /api/v1/barcode/lookup/{code}` - Lookup product by barcode

#### Predictions
- `GET /api/v1/predictions/{product_id}` - Get depletion prediction
- `POST /api/v1/predictions/train` - Trigger model training

#### Alerts
- `GET /api/v1/alerts` - Get active alerts
- `POST /api/v1/alerts/{id}/acknowledge` - Acknowledge alert

## Testing

### Backend Tests
```bash
cd backend
pytest
pytest --cov=app tests/  # With coverage
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage  # With coverage
```

### E2E Tests
```bash
cd frontend
npm run test:e2e
```

## Database Migrations

### Create a new migration
```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback migration
```bash
alembic downgrade -1
```

## Environment Variables

### Backend (.env)
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `JWT_SECRET` - Secret key for JWT token signing
- `JWT_ALGORITHM` - JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time
- `ENVIRONMENT` - Environment name (development/production)

### Frontend (.env)
- `VITE_API_URL` - Backend API base URL

## Deployment

### Quick Deployment (30 minutes)

Deploy to production using Railway (backend) and Vercel (frontend):

📖 **[Quick Start Deployment Guide](DEPLOYMENT_QUICKSTART.md)** - Get deployed in under 30 minutes

### Comprehensive Deployment

For detailed deployment instructions, configuration, and best practices:

📖 **[Full Deployment Guide](DEPLOYMENT.md)** - Complete deployment documentation

Includes:
- Railway backend deployment
- Vercel frontend deployment
- Database setup and migrations
- Environment variable configuration
- CI/CD pipeline setup with GitHub Actions
- Monitoring and maintenance
- Troubleshooting guide

### Database Migrations

For production database migration strategy:

📖 **[Database Migration Strategy](DATABASE_MIGRATION_STRATEGY.md)** - Migration best practices

### Self-Hosted Deployment

For self-hosted production deployment using Docker:

```bash
# Copy and configure environment variables
cp .env.production.example .env.production
# Edit .env.production with your values

# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Deployment Options

| Platform | Component | Cost | Difficulty | Recommended For |
|----------|-----------|------|------------|-----------------|
| Railway | Backend + DB | $5-20/mo | Easy | Production |
| Vercel | Frontend | Free-$20/mo | Easy | Production |
| Docker | Full Stack | Server cost | Medium | Self-hosted |
| AWS/GCP | Full Stack | Variable | Hard | Enterprise |

## Troubleshooting

### Docker Issues
- **Port already in use**: Change port mappings in docker-compose.yml
- **Container won't start**: Check logs with `docker-compose logs <service-name>`
- **Database connection failed**: Ensure PostgreSQL is healthy with `docker-compose ps`

### Backend Issues
- **Import errors**: Ensure virtual environment is activated
- **Database errors**: Check DATABASE_URL and run migrations
- **Celery not processing tasks**: Verify Redis connection

### Frontend Issues
- **API connection failed**: Check VITE_API_URL in .env
- **Build errors**: Clear node_modules and reinstall: `rm -rf node_modules && npm install`

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
- Open an issue on GitHub
- Check the API documentation at http://localhost:8000/docs
- Review the design document in `.kiro/specs/smart-inventory-system/design.md`

## Roadmap

- [ ] Mobile app (React Native)
- [ ] Multi-location support
- [ ] Advanced analytics dashboard
- [ ] Supplier API integration
- [ ] Automated purchase orders
- [ ] Batch import/export (CSV)
- [ ] Multi-tenancy support
