.PHONY: help build up down logs clean install-frontend dev-frontend dev-backend dev

help:
	@echo "Available commands:"
	@echo "  build              - Build the Docker image"
	@echo "  up                 - Start the service"
	@echo "  down               - Stop the service"
	@echo "  logs               - Show logs"
	@echo "  clean              - Clean up containers and images"
	@echo "  install-frontend   - Install frontend dependencies"
	@echo "  dev-frontend       - Start frontend development server"
	@echo "  dev-backend        - Start backend development server"
	@echo "  dev                - Start both frontend and backend for development"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	docker-compose down -v --rmi all

install-frontend:
	cd frontend && npm install

dev-frontend:
	cd frontend && npm start

dev-backend:
	cd backend && python main.py

dev:
	@echo "Starting development servers..."
	@echo "Backend will be available at http://localhost:8000"
	@echo "Frontend will be available at http://localhost:3000"
	@echo "Make sure to set OPENAI_API_KEY environment variable"