# SteamBay

SteamBay is an e-commerce platform for digital game sales, featuring a React frontend and FastAPI backend.

## Project Background

In the development process of SteamBay, not a single line of code in the repository was created or modified manually by a human. The entire codebase is AI-generated.

The Steambay project will be used by the startup cp.center as an application for automated testing of web application pentester skills. For this reason, certain technical simplifications were made, such as encapsulating the entire application in a single container.

The choice of application type - e-commerce - was primarily due to the large variety of functionalities that can appear in such an application. The goal was to provide a realistic experience for individuals whose skills will be tested through interaction with this platform in the future.

## Project Structure

- `frontend/` - React frontend application
- `src/` - FastAPI backend application
- `docker-compose.yml` - Docker Compose configuration
- `Dockerfile` - Main Dockerfile for the application
- `tests/` - Backend unit tests

## Features

- User authentication with three roles: Admin, Seller, and Buyer
- Product listing and search
- Shopping cart and checkout
- Order management
- Admin dashboard
- Seller dashboard for managing offers

## Running with Docker

### Prerequisites

- Docker and Docker Compose

### Setup and Run

1. Build and start the application:

```bash
docker compose up -d --build
```

2. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

The application runs in a single container that includes:
- PostgreSQL database
- FastAPI backend
- React frontend

All data is stored within the container and will be removed when the container is stopped.

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

### Shared Architecture

The application uses a shared service architecture where business logic services are located in `frontend/src/services/` but are used by both the frontend and backend components. When running tests, the Python path is configured to include both directories.

For more details, see the [Services Module README](frontend/src/services/README.md).

## Continuous Integration

The project uses GitHub Actions for continuous integration. The workflow is defined in `.github/workflows/simple-build.yml` and includes:

### Linting
- Python code linting using flake8
- JavaScript/TypeScript linting using ESLint
- Runs on every push and pull request

### Testing
- Python unit tests with pytest
- Code coverage reporting
- Uploads coverage reports to Codecov (optional)
- Runs after successful linting

### Pull Request Comments
- Automatically posts build status comments on pull requests
- Shows success/failure status for linting and tests
- Includes links to the workflow run

To run the CI checks locally:
```bash
# Python linting
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# JavaScript linting
cd frontend && npx eslint src --ext .js,.jsx,.ts,.tsx

# Python tests
pytest --cov=. --cov-report=term
```
