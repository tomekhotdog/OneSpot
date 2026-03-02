BACKEND_PORT ?= 8001

.PHONY: dev dev-backend dev-frontend test test-backend test-frontend

# Run both backend and frontend together
dev:
	@echo "Starting OneSpot dev servers..."
	@echo "  Backend:  http://localhost:$(BACKEND_PORT)"
	@echo "  Frontend: http://localhost:5173"
	@echo ""
	@trap 'kill 0' EXIT; \
		PYTHONUNBUFFERED=1 EMAIL_MOCK=true uvicorn backend.main:app --reload --port $(BACKEND_PORT) 2>&1 | tee /tmp/onespot-backend.log | sed 's/^/[backend]  /' & \
		cd frontend && VITE_BACKEND_PORT=$(BACKEND_PORT) npm run dev 2>&1 | sed 's/^/[frontend] /' & \
		wait

# Run backend only
dev-backend:
	EMAIL_MOCK=true uvicorn backend.main:app --reload --port $(BACKEND_PORT)

# Run frontend only
dev-frontend:
	cd frontend && npm run dev

# Run all tests
test:
	pytest tests/

# Run backend tests only
test-backend:
	pytest tests/

# Run frontend tests only
test-frontend:
	cd frontend && npm test
