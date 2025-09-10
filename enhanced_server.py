"""
Simple Enhanced FastAPI Server for LangGraph DevOps Autocoder
Windows-compatible version without encoding conflicts
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Project imports
try:
    from src.main import process_jira_webhook
    MAIN_AVAILABLE = True
    print("SUCCESS: Main automation module imported successfully")
except ImportError as e:
    print(f"WARNING: Could not import main module: {e}")
    MAIN_AVAILABLE = False

# Configure simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create necessary directories
Path("logs").mkdir(exist_ok=True)
Path("reports").mkdir(exist_ok=True)

# FastAPI app initialization
app = FastAPI(
    title="LangGraph DevOps Autocoder Server",
    description="Automated DevOps pipeline triggered by Jira webhooks",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
webhook_history = []
automation_results = {}

@app.get("/")
async def root():
    """Root endpoint with server information"""
    return {
        "service": "LangGraph DevOps Autocoder",
        "version": "2.0.0", 
        "status": "running",
        "main_module_available": MAIN_AVAILABLE,
        "endpoints": {
            "webhook": "/webhook/jira",
            "health": "/health",
            "status": "/status",
            "test_export": "/test/export"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "main_available": MAIN_AVAILABLE
    }

@app.get("/status")
async def get_status():
    """Get system status and recent activity"""
    return {
        "system_status": "operational",
        "webhooks_processed": len(webhook_history),
        "recent_activity": webhook_history[-5:] if webhook_history else [],
        "active_automations": len(automation_results)
    }

@app.post("/webhook/jira")
async def jira_webhook(request: Request, background_tasks: BackgroundTasks):
    """Main Jira webhook endpoint that triggers the DevOps automation pipeline"""
    try:
        # Parse JSON payload
        try:
            payload = await request.json()
        except json.JSONDecodeError:
            body = await request.body()
            payload = {"raw_body": body.decode('utf-8', errors='ignore')}
        
        # Log incoming webhook
        webhook_data = {
            "timestamp": datetime.now().isoformat(),
            "payload": payload,
            "source_ip": request.client.host if request.client else "unknown"
        }
        
        webhook_history.append(webhook_data)
        logger.info(f"Received Jira webhook from {request.client.host if request.client else 'unknown'}")
        
        if MAIN_AVAILABLE:
            # Process webhook asynchronously
            background_tasks.add_task(process_webhook_async, payload, webhook_data)
            
            return JSONResponse(
                content={
                    "status": "accepted",
                    "message": "Webhook received and processing started",
                    "timestamp": datetime.now().isoformat()
                },
                status_code=202
            )
        else:
            # Mock response when main module not available
            return JSONResponse(
                content={
                    "status": "simulated",
                    "message": "Webhook received (main module not available - using simulation)",
                    "timestamp": datetime.now().isoformat(),
                    "mock_result": {
                        "trace_id": "mock-123-456",
                        "issue_key": payload.get("issue", {}).get("key", "UNKNOWN"),
                        "status": "simulated_success"
                    }
                },
                status_code=200
            )
            
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")

async def process_webhook_async(payload: Dict[str, Any], webhook_data: Dict[str, Any]):
    """Process webhook asynchronously"""
    try:
        logger.info("Starting async webhook processing")
        
        if MAIN_AVAILABLE:
            # Call the main automation pipeline
            result = await process_jira_webhook(payload)
            
            # Store result
            trace_id = result.get('trace_id', 'unknown')
            automation_results[trace_id] = {
                "result": result,
                "webhook_data": webhook_data,
                "completed_at": datetime.now().isoformat()
            }
            
            logger.info(f"Automation completed for trace_id: {trace_id}")
        else:
            logger.warning("Main module not available, skipping automation")
            
    except Exception as e:
        logger.error(f"Async webhook processing failed: {str(e)}")

@app.get("/results/{trace_id}")
async def get_automation_result(trace_id: str):
    """Get automation results by trace ID"""
    if trace_id in automation_results:
        return automation_results[trace_id]
    else:
        raise HTTPException(status_code=404, detail="Trace ID not found")

@app.get("/test/export")
async def test_export_automation():
    """Test endpoint for export functionality automation"""
    
    test_payload = {
        "issue": {
            "key": "TEST-EXPORT-001",
            "fields": {
                "summary": "Add CSV export functionality to todo app",
                "issuetype": {"name": "Story"},
                "description": "Users need to be able to export their todos to CSV format for external analysis. The export should include all todo fields: title, description, priority, category, completion status, and creation date."
            }
        }
    }
    
    try:
        if MAIN_AVAILABLE:
            logger.info("Testing export automation...")
            result = await process_jira_webhook(test_payload)
            
            return {
                "test_status": "completed",
                "automation_result": result,
                "message": "Export automation test completed successfully"
            }
        else:
            return {
                "test_status": "simulated",
                "message": "Main module not available - returning mock result",
                "mock_result": {
                    "trace_id": "test-export-123",
                    "issue_key": "TEST-EXPORT-001",
                    "files_generated": 2,
                    "success_rate": 100.0,
                    "status": "SUCCESS"
                }
            }
            
    except Exception as e:
        logger.error(f"Test automation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

# Simple startup without fancy logging
@app.on_event("startup")
async def startup_event():
    """Server startup event"""
    logger.info("Enhanced LangGraph DevOps Autocoder Server started")
    logger.info(f"Main automation module available: {MAIN_AVAILABLE}")
    logger.info("Ready to process Jira webhooks and automate DevOps tasks!")

if __name__ == "__main__":
    print("Starting Enhanced LangGraph DevOps Autocoder Server...")
    print(f"Main module available: {MAIN_AVAILABLE}")
    
    uvicorn.run(
        "enhanced_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )