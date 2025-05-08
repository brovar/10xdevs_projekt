# SteamBay

SteamBay is an e-commerce platform for digital game sales, featuring a React frontend and FastAPI backend.

## Project Structure

- `frontend/` - React frontend application
- `src/` - FastAPI backend application
- `docker-compose.yml` - Docker Compose configuration
- `Dockerfile.backend` - Backend Dockerfile
- `Dockerfile.frontend` - Frontend Dockerfile

## Features

- User authentication with three roles: Admin, Seller, and Buyer
- Product listing and search
- Shopping cart and checkout
- Order management
- Admin dashboard
- Seller dashboard for managing offers

## Running Locally

### Prerequisites

- Python 3.10 or higher
- Node.js 18 or higher
- PostgreSQL 14 or higher

### Setup and Run

1. Make sure PostgreSQL is running
2. Run the local setup script:

```bash
./run_local.sh
```

3. Navigate to `frontend/` directory and run:

```bash
npm install
npm start
```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Running with Docker

### Prerequisites

- Docker and Docker Compose

### Setup and Run

1. Run the Docker setup script:

```bash
./run_docker.sh
```

2. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Test Users

The application is initialized with the following test users:

- Admin: admin@steambay.com / Admin123!
- Seller: seller@steambay.com / Seller123!
- Buyer: buyer@steambay.com / Buyer123!

## Development

### Backend

The backend is built with FastAPI and follows RESTful API design principles. The database schema is defined in `src/models.py` and the API routes are in the `src/routers/` directory.

### Frontend

The frontend is built with React and uses React Router for navigation. The API service integrations are in the `frontend/src/services/` directory.
