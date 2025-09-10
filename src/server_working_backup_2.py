from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import json
import sys
from pathlib import Path
import logging
import traceback

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import main function with error handling
try:
    from main import process_jira_webhook
    MAIN_AVAILABLE = True
    logger.info("✅ Successfully imported main module")
except Exception as e:
    MAIN_AVAILABLE = False
    logger.error(f"❌ Failed to import main module: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    # Fallback function
    async def process_jira_webhook(payload):
        return {
            "trace_id": "fallback-trace-id",
            "status": "error",
            "message": "Main module not available",
            "error": str(e)
        }

app = FastAPI(title="LangGraph DevOps Autocoder", version="1.0.0")

# Store webhook processing results for status endpoint
webhook_results = {}

@app.post("/webhook/jira")
async def jira_webhook(request: Request):
    """Handle Jira webhook events"""
    try:
        # Get raw body
        body = await request.body()
        payload = json.loads(body)
        
        # Add signature to payload for verification
        signature = request.headers.get('X-Hub-Signature-256', 'sha256=test')
        payload['signature'] = signature
        
        # Process webhook
        if MAIN_AVAILABLE:
            result = await process_jira_webhook(payload)
            
            # Store result for status endpoint
            issue_key = result.get('issue_key', 'UNKNOWN')
            webhook_results[issue_key] = result
            
            return JSONResponse({
                "status": "accepted" if result.get('overall_status') == 'SUCCESS' else "failed",
                "trace_id": result.get('trace_id', 'unknown'),
                "message": "Webhook processed",
                "issue_key": issue_key,
                "files_generated": len(result.get('generated_code', {})),
                "files_written": len(result.get('file_changes', [])),
                "success_rate": f"{result.get('success_rate', 0):.0f}%"
            })
        else:
            return JSONResponse({
                "status": "error",
                "message": "Main processing module not available",
                "suggestion": "Check main.py for syntax errors"
            }, status_code=500)
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse({
            "status": "error", 
            "message": str(e),
            "trace_id": "error-trace"
        }, status_code=500)

@app.get("/status/{issue_key}")
async def get_status(issue_key: str):
    """Get processing status for an issue"""
    if issue_key in webhook_results:
        result = webhook_results[issue_key]
        return {
            "issue_key": issue_key,
            "status": result.get('overall_status', 'UNKNOWN'),
            "trace_id": result.get('trace_id'),
            "files_generated": len(result.get('generated_code', {})),
            "files_written": len(result.get('file_changes', [])),
            "success_rate": result.get('success_rate', 0),
            "errors": result.get('errors', [])
        }
    else:
        raise HTTPException(status_code=404, detail="Issue not found")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "devops-autocoder",
        "main_module": "available" if MAIN_AVAILABLE else "error",
        "version": "1.0.0"
    }

@app.get("/logs")
async def get_logs(lines: int = 50):
    """Get recent log entries"""
    try:
        log_file = Path("logs/devops_autocoder.log")
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                return {"logs": [line.strip() for line in recent_lines]}
        else:
            return {"logs": ["No log file found"]}
    except Exception as e:
        return {"logs": [f"Error reading logs: {e}"]}

@app.get("/files")
async def get_generated_files():
    """Get list of generated files"""
    try:
        generated_dir = Path("generated_code")
        if generated_dir.exists():
            files = []
            for file_path in generated_dir.rglob("*"):
                if file_path.is_file():
                    files.append({
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "modified": file_path.stat().st_mtime
                    })
            return {"files": files, "total": len(files)}
        else:
            return {"files": [], "total": 0}
    except Exception as e:
        return {"files": [], "error": str(e)}

@app.get("/backups")
async def get_backups():
    """Get backup information"""
    try:
        backups_dir = Path("backups")
        if backups_dir.exists():
            backups = []
            for backup_dir in backups_dir.iterdir():
                if backup_dir.is_dir():
                    files = list(backup_dir.rglob("*"))
                    backups.append({
                        "trace_id": backup_dir.name,
                        "files": len([f for f in files if f.is_file()]),
                        "created": backup_dir.stat().st_ctime
                    })
            return {"backups": backups, "total": len(backups)}
        else:
            return {"backups": [], "total": 0}
    except Exception as e:
        return {"backups": [], "error": str(e)}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "LangGraph DevOps Autocoder",
        "version": "1.0.0",
        "status": "running",
        "main_module": "available" if MAIN_AVAILABLE else "error",
        "endpoints": {
            "webhook": "/webhook/jira",
            "health": "/health",
            "status": "/status/{issue_key}",
            "logs": "/logs",
            "files": "/files",
            "backups": "/backups"
        },
        "documentation": {
            "test_webhook": "POST to /webhook/jira with Jira issue payload",
            "check_status": "GET /status/{issue_key} to see processing results",
            "view_logs": "GET /logs to see recent activity",
            "generated_files": "GET /files to see generated code files"
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting LangGraph DevOps Autocoder Server")
    print(f"Main module available: {MAIN_AVAILABLE}")
    
    if not MAIN_AVAILABLE:
        print("⚠️  Warning: Main processing module has errors")
        print("💡 Check src/main.py for syntax issues")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)