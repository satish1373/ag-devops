#!/bin/bash
echo "🧪 Testing system..."
curl -s http://localhost:8000/health && echo "✅ Health OK"
curl -s -X POST http://localhost:8000/test/export && echo "✅ Export test OK"
curl -s -X POST http://localhost:8000/test/search && echo "✅ Search test OK"
