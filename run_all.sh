#!/bin/bash
# Start both API (port 8002) and Web UI (port 5000)

# Kill any existing processes
lsof -t -i:8002 | xargs -r kill -9 2>/dev/null
lsof -t -i:5000 | xargs -r kill -9 2>/dev/null
sleep 1

# Start API in background
python -c "import uvicorn; uvicorn.run('gehenna_api.app:app', host='0.0.0.0', port=8002)" &
API_PID=$!
echo "API starting (PID: $API_PID) on port 8002..."

# Wait for API to be ready (max 10 seconds)
for i in $(seq 1 10); do
    if curl -s -o /dev/null http://localhost:8002/ 2>/dev/null; then
        echo "API ready!"
        break
    fi
    sleep 1
done

# Start Web UI in background
python -m flask --app gehenna_web.app run --port 5000 --debug &
WEB_PID=$!
echo "Web UI starting (PID: $WEB_PID) on port 5000..."

# Wait for Web UI to be ready (max 10 seconds)
for i in $(seq 1 10); do
    if curl -s -o /dev/null http://localhost:5000/ 2>/dev/null; then
        echo "Web UI ready!"
        break
    fi
    sleep 1
done

echo ""
echo "API:  http://localhost:8002"
echo "Web:  http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop both"

# Trap to kill both on exit
trap "kill $API_PID $WEB_PID 2>/dev/null; exit" INT TERM

# Wait for either process to exit
wait $API_PID $WEB_PID
