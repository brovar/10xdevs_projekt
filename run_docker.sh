#!/bin/bash

# Build and start the Docker containers
echo "Building and starting Docker containers..."
docker-compose up --build -d

# Wait for the containers to be ready
echo "Waiting for services to start..."
sleep 10

# Display running containers
echo "Running containers:"
docker-compose ps

echo ""
echo "==================================================="
echo "SteamBay is now running!"
echo "==================================================="
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo ""
echo "Test users:"
echo "- Admin: admin@steambay.com / Admin123!"
echo "- Seller: seller@steambay.com / Seller123!"
echo "- Buyer: buyer@steambay.com / Buyer123!"
echo "==================================================="
echo ""
echo "To view logs, run: docker-compose logs -f"
echo "To stop the application, run: docker-compose down" 