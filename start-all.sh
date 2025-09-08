#!/bin/bash
echo "🚀 Starting LangGraph DevOps System"

# Start backend
cd todo-app/backend
npm install &>/dev/null
node server.js &
BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"
cd ../..

# Start frontend  
cd todo-app/frontend
npm install &>/dev/null
npm start &
FRONTEND_PID=$!
echo "✅ Frontend started (PID: $FRONTEND_PID)"
cd ../..

# Start LangGraph server
conda run -n langgraph-devops python enhanced_server.py &
LANGGRAPH_PID=$!
echo "✅ LangGraph started (PID: $LANGGRAPH_PID)"

echo ""
echo "🎉 All services started!"
echo "Frontend:  http://localhost:3000"
echo "Backend:   http://localhost:3001"
echo "LangGraph: http://localhost:8000"
echo ""
echo "Test: curl -X POST http://localhost:8000/test/export"

trap 'kill $BACKEND_PID $FRONTEND_PID $LANGGRAPH_PID 2>/dev/null; exit' INT
wait
