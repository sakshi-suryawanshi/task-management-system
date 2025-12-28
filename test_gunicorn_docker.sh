#!/bin/bash
# Test script to verify Gunicorn configuration in Docker

set -e

echo "=========================================="
echo "Testing Gunicorn Configuration in Docker"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose not found${NC}"
    exit 1
fi

echo -e "${BLUE}[1/6] Checking container status...${NC}"
if docker-compose ps web | grep -q "Up"; then
    echo -e "${GREEN}✓ Web container is running${NC}"
else
    echo -e "${RED}✗ Web container is not running${NC}"
    echo "Starting web container..."
    docker-compose up -d web
    sleep 5
fi

echo ""
echo -e "${BLUE}[2/6] Verifying config file exists in container...${NC}"
if docker-compose exec -T web test -f /app/gunicorn_config.py; then
    echo -e "${GREEN}✓ gunicorn_config.py exists${NC}"
else
    echo -e "${RED}✗ gunicorn_config.py not found${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}[3/6] Testing config file syntax...${NC}"
if docker-compose exec -T web python3 -m py_compile gunicorn_config.py 2>/dev/null; then
    echo -e "${GREEN}✓ Config file syntax is valid${NC}"
else
    echo -e "${RED}✗ Config file has syntax errors${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}[4/6] Checking Gunicorn configuration values...${NC}"
CONFIG_OUTPUT=$(docker-compose exec -T web python3 << 'PYEOF'
import sys
sys.path.insert(0, '/app')
import gunicorn_config
print(f"bind={gunicorn_config.bind}")
print(f"workers={gunicorn_config.workers}")
print(f"worker_class={gunicorn_config.worker_class}")
print(f"timeout={gunicorn_config.timeout}")
PYEOF
)

echo "$CONFIG_OUTPUT"
if echo "$CONFIG_OUTPUT" | grep -q "bind=0.0.0.0:8000"; then
    echo -e "${GREEN}✓ Bind address is correct (0.0.0.0:8000)${NC}"
else
    echo -e "${YELLOW}⚠ Bind address check: ${CONFIG_OUTPUT}${NC}"
fi

if echo "$CONFIG_OUTPUT" | grep -q "workers=[0-9]"; then
    WORKERS=$(echo "$CONFIG_OUTPUT" | grep "workers=" | cut -d'=' -f2)
    echo -e "${GREEN}✓ Workers configured: ${WORKERS}${NC}"
else
    echo -e "${RED}✗ Workers configuration issue${NC}"
fi

echo ""
echo -e "${BLUE}[5/6] Testing Gunicorn --print-config...${NC}"
PRINT_CONFIG=$(docker-compose exec -T web sh -c "cd /app && gunicorn taskmanager.wsgi:application --config gunicorn_config.py --print-config 2>&1" | grep -E "^bind|^workers|^worker_class")
echo "$PRINT_CONFIG"

if echo "$PRINT_CONFIG" | grep -q "bind.*0.0.0.0:8000"; then
    echo -e "${GREEN}✓ Gunicorn reads bind address correctly${NC}"
else
    echo -e "${RED}✗ Gunicorn bind address issue${NC}"
fi

if echo "$PRINT_CONFIG" | grep -q "workers.*=.*3"; then
    echo -e "${GREEN}✓ Gunicorn reads workers correctly (3)${NC}"
else
    echo -e "${YELLOW}⚠ Workers check: ${PRINT_CONFIG}${NC}"
fi

echo ""
echo -e "${BLUE}[6/6] Testing health endpoint from inside container...${NC}"
HEALTH_RESPONSE=$(docker-compose exec -T web curl -s http://127.0.0.1:8000/health/ 2>&1 || echo "ERROR")
if echo "$HEALTH_RESPONSE" | grep -q '"status".*"healthy"'; then
    echo -e "${GREEN}✓ Health endpoint responding correctly${NC}"
    echo "Response: $HEALTH_RESPONSE"
else
    echo -e "${RED}✗ Health endpoint not responding${NC}"
    echo "Response: $HEALTH_RESPONSE"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}All tests completed!${NC}"
echo "=========================================="
echo ""
echo "To view Gunicorn logs:"
echo "  docker-compose logs web | grep -i gunicorn"
echo ""
echo "To check running processes:"
echo "  docker-compose exec web sh -c 'pgrep -a gunicorn || echo \"pgrep not available\"'"
echo ""
echo "To test from host:"
echo "  curl http://localhost:8000/health/"

