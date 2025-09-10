"""
Fixed FastAPI Server for LangGraph DevOps Autocoder
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from main import process_jira_webhook
    from utils.logger import setup_logger
    MAIN_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    MAIN_AVAILABLE = False
    
    def setup_logger(name):
        import logging
        return logging.getLogger(name)
    
    async def process_jira_webhook(payload):
        return {
            "trace_id": "mock-trace-id",
            "status": "success",
            "message": "Webhook processed (mock mode - main.py not available)",
            "file_changes": [],
            "errors": ["Main processor not available"]
        }

app = FastAPI(title="LangGraph DevOps Autocoder", version="1.0.0")
logger = setup_logger(__name__)

# Store active automations for monitoring
active_automations = {}
completed_automations = {}

@app.post("/webhook/jira")
async def jira_webhook(request: Request):
    """Handle Jira webhook events"""
    try:
        # Get raw body for signature verification
        body = await request.body()
        payload = json.loads(body)
        
        # Add signature to payload for verification
        signature = request.headers.get('X-Hub-Signature-256', '')
        payload['signature'] = signature
        
        logger.info(f"Received webhook for issue: {payload.get('issue', {}).get('key', 'unknown')}")
        
        # Process webhook
        result = await process_jira_webhook(payload)
        
        # Store result for monitoring
        trace_id = result.get('trace_id', 'unknown')
        completed_automations[trace_id] = result
        
        return JSONResponse({
            "status": "success" if not result.get('errors') else "completed_with_errors",
            "trace_id": trace_id,
            "message": "Webhook processed successfully",
            "files_generated": len(result.get('generated_code', {})),
            "files_written": len(result.get('file_changes', [])),
            "errors": len(result.get('errors', [])),
            "main_available": MAIN_AVAILABLE
        })
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{trace_id}")
async def get_automation_status(trace_id: str):
    """Get status of specific automation"""
    if trace_id in completed_automations:
        result = completed_automations[trace_id]
        return {
            "trace_id": trace_id,
            "status": "completed",
            "issue_key": result.get('issue_key', 'unknown'),
            "files_written": len(result.get('file_changes', [])),
            "errors": result.get('errors', []),
            "report_available": bool(result.get('report'))
        }
    else:
        raise HTTPException(status_code=404, detail="Automation not found")

@app.get("/logs")
async def get_recent_logs(lines: int = 50):
    """Get recent log entries"""
    try:
        log_file = Path("logs/devops_autocoder.log")
        if log_file.exists():
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                return {"logs": [line.strip() for line in recent_lines]}
        else:
            return {"logs": ["No log file found"]}
    except Exception as e:
        return {"logs": [f"Error reading logs: {e}"]}

@app.get("/files")
async def get_generated_files():
    """Get list of recently generated files"""
    try:
        files_info = []
        
        # Check todo-app directory for recent files
        todo_app_path = Path("todo-app")
        if todo_app_path.exists():
            for file_path in todo_app_path.rglob("*"):
                if file_path.is_file() and file_path.suffix in ['.jsx', '.js', '.css', '.json']:
                    files_info.append({
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "modified": file_path.stat().st_mtime
                    })
        
        # Sort by modification time (newest first)
        files_info.sort(key=lambda x: x['modified'], reverse=True)
        
        return {
            "files": files_info[:20],  # Return first 20
            "total": len(files_info)
        }
    except Exception as e:
        return {"files": [], "error": str(e)}

@app.get("/backups")
async def get_backup_info():
    """Get backup information"""
    try:
        backup_info = []
        backups_path = Path("backups")
        
        if backups_path.exists():
            for backup_dir in backups_path.iterdir():
                if backup_dir.is_dir():
                    files_count = len(list(backup_dir.rglob("*")))
                    backup_info.append({
                        "trace_id": backup_dir.name,
                        "files": files_count,
                        "created": backup_dir.stat().st_mtime
                    })
        
        return {
            "backups": backup_info,
            "total": len(backup_info)
        }
    except Exception as e:
        return {"backups": [], "error": str(e)}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "devops-autocoder",
        "main_available": MAIN_AVAILABLE,
        "components": {
            "webhook_processor": "✅" if MAIN_AVAILABLE else "❌",
            "file_system": "✅",
            "logging": "✅",
            "backup_system": "✅"
        }
    }

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "LangGraph DevOps Autocoder",
        "version": "1.0.0",
        "status": "operational" if MAIN_AVAILABLE else "limited",
        "endpoints": {
            "webhook": "/webhook/jira",
            "health": "/health",
            "status": "/status/{trace_id}",
            "logs": "/logs",
            "files": "/files",
            "backups": "/backups"
        },
        "documentation": "Send POST requests to /webhook/jira with Jira webhook payload"
    }

# Test endpoint for manual testing
@app.post("/test/export")
async def test_export_feature():
    """Test the export feature automation"""
    test_webhook = {
        "signature": "sha256=test",
        "issue": {
            "key": "TEST-EXPORT-001",
            "fields": {
                "summary": "Add CSV export functionality to todo app",
                "issuetype": {"name": "Story"},
                "description": "Add export button that allows users to download their todos as CSV file with all details including title, description, priority, category, completion status, and creation date."
            }
        }
    }
    
    logger.info("Processing test export automation")
    result = await process_jira_webhook(test_webhook)
    
    return {
        "message": "Test export automation completed",
        "result": result
    }

@app.post("/test/search")
async def test_search_feature():
    """Test the search feature automation"""
    test_webhook = {
        "signature": "sha256=test",
        "issue": {
            "key": "TEST-SEARCH-002",
            "fields": {
                "summary": "Implement real-time todo search functionality",
                "issuetype": {"name": "Feature"},
                "description": "Add search bar with real-time filtering of todos by title and description. Include clear button to reset search."
            }
        }
    }
    
    logger.info("Processing test search automation")
    result = await process_jira_webhook(test_webhook)
    
    return {
        "message": "Test search automation completed",
        "result": result
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting LangGraph DevOps Autocoder Server")
    print("=" * 50)
    print(f"✅ Main webhook processor available: {MAIN_AVAILABLE}")
    print("📡 Server will start on http://localhost:8000")
    print("🔗 Webhook endpoint: http://localhost:8000/webhook/jira")
    print("🏥 Health check: http://localhost:8000/health")
    print("🧪 Test endpoints:")
    print("   • Export test: POST http://localhost:8000/test/export")
    print("   • Search test: POST http://localhost:8000/test/search")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)