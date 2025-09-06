from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import json
from src.main import process_jira_webhook
from src.utils.logger import setup_logger

app = FastAPI(title="LangGraph DevOps Autocoder", version="1.0.0")
logger = setup_logger(__name__)

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
        
        # Process webhook
        result = await process_jira_webhook(payload)
        
        return JSONResponse({
            "status": "success",
            "trace_id": result['trace_id'],
            "message": "Webhook processed successfully"
        })
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "devops-autocoder"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "LangGraph DevOps Autocoder",
        "version": "1.0.0",
        "endpoints": {
            "webhook": "/webhook/jira",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)