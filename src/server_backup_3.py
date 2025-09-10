from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse, HTMLResponse
import json
import sys
from pathlib import Path
import logging
import traceback
import asyncio

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import main modules
try:
    from main import process_jira_webhook
    MAIN_AVAILABLE = True
    logger.info("✅ Main webhook processor available")
except Exception as e:
    MAIN_AVAILABLE = False
    logger.error(f"❌ Main processor not available: {e}")

try:
    from deployment_agents import trigger_automated_deployment, DeploymentOrchestrator
    DEPLOYMENT_AVAILABLE = True
    logger.info("✅ Deployment system available")
except Exception as e:
    DEPLOYMENT_AVAILABLE = False
    logger.error(f"❌ Deployment system not available: {e}")

app = FastAPI(title="LangGraph DevOps Autocoder + Deployment", version="2.0.0")

# Global storage
webhook_results = {}
deployment_orchestrator = DeploymentOrchestrator() if DEPLOYMENT_AVAILABLE else None

@app.post("/webhook/jira")
async def jira_webhook(request: Request, auto_deploy: bool = Query(default=True)):
    """Enhanced webhook handler with optional automated deployment"""
    try:
        body = await request.body()
        payload = json.loads(body)
        payload['signature'] = request.headers.get('X-Hub-Signature-256', 'sha256=test')
        
        if not MAIN_AVAILABLE:
            return JSONResponse({
                "status": "error",
                "message": "Main processing module not available"
            }, status_code=500)
        
        # Step 1: Generate code
        logger.info("🔧 Step 1: Code Generation")
        generation_result = await process_jira_webhook(payload)
        issue_key = generation_result.get('issue_key', 'UNKNOWN')
        
        # Step 2: Automated deployment (if enabled and successful)
        if (auto_deploy and DEPLOYMENT_AVAILABLE and 
            generation_result.get('overall_status') == 'SUCCESS'):
            
            logger.info("🚀 Step 2: Automated Deployment")
            deployment_result = await trigger_automated_deployment(issue_key)
            
            # Combine results
            generation_result['deployment'] = deployment_result
            generation_result['auto_deployed'] = deployment_result['status'] == 'SUCCESS'
            
            if deployment_result['status'] == 'SUCCESS':
                generation_result['final_status'] = 'FULLY_AUTOMATED'
                response_status = "fully_automated"
            else:
                generation_result['final_status'] = 'PARTIAL_SUCCESS'
                response_status = "generated_only"
        else:
            generation_result['auto_deployed'] = False
            generation_result['final_status'] = 'GENERATION_ONLY'
            response_status = "generated_only"
        
        # Store results
        webhook_results[issue_key] = generation_result
        
        # Response
        response_data = {
            "status": response_status,
            "trace_id": generation_result.get('trace_id'),
            "issue_key": issue_key,
            "generation": {
                "files_generated": len(generation_result.get('generated_code', {})),
                "files_written": len(generation_result.get('file_changes', [])),
                "success_rate": f"{generation_result.get('success_rate', 0):.0f}%"
            }
        }
        
        if generation_result.get('auto_deployed'):
            deployment = generation_result['deployment']
            response_data["deployment"] = {
                "status": deployment['status'],
                "files_deployed": deployment.get('files_deployed', 0),
                "deployment_url": deployment.get('deployment_url'),
                "trace_id": deployment.get('trace_id')
            }
        
        return JSONResponse(response_data)
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        return JSONResponse({
            "status": "error",
            "message": str(e),
            "trace_id": "error"
        }, status_code=500)

@app.post("/deploy/{issue_key}")
async def manual_deploy(issue_key: str, target_project: str = Query(default=None)):
    """Manually trigger deployment for a specific issue"""
    if not DEPLOYMENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Deployment system not available")
    
    try:
        result = await trigger_automated_deployment(issue_key, target_project)
        return result
    except Exception as e:
        logger.error(f"Manual deployment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rollback/{trace_id}")
async def rollback_deployment(trace_id: str):
    """Rollback a deployment using its trace ID"""
    if not DEPLOYMENT_AVAILABLE:
        raise HTTPException(status_code=503, detail="Deployment system not available")
    
    try:
        success = await deployment_orchestrator.rollback_deployment(trace_id)
        if success:
            return {"status": "success", "message": f"Rollback completed for {trace_id}"}
        else:
            return {"status": "failed", "message": f"Rollback failed for {trace_id}"}
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{issue_key}")
async def get_status(issue_key: str):
    """Get comprehensive status for an issue"""
    if issue_key in webhook_results:
        result = webhook_results[issue_key]
        return {
            "issue_key": issue_key,
            "generation_status": result.get('overall_status'),
            "auto_deployed": result.get('auto_deployed', False),
            "final_status": result.get('final_status'),
            "trace_id": result.get('trace_id'),
            "files_generated": len(result.get('generated_code', {})),
            "files_written": len(result.get('file_changes', [])),
            "deployment": result.get('deployment', {}),
            "errors": result.get('errors', [])
        }
    else:
        raise HTTPException(status_code=404, detail="Issue not found")

@app.get("/deployments")
async def list_deployments():
    """List all deployment history"""
    if not DEPLOYMENT_AVAILABLE:
        return {"deployments": [], "message": "Deployment system not available"}
    
    history = deployment_orchestrator.get_deployment_status()
    return {"deployments": history, "total": len(history)}

@app.get("/health/deployment")
async def deployment_health():
    """Check deployment system health"""
    if not DEPLOYMENT_AVAILABLE:
        return {"healthy": False, "message": "Deployment system not available"}
    
    health = await deployment_orchestrator.health_check()
    return health

@app.get("/demo")
async def demo_page():
    """Demo page showing the automation in action"""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>LangGraph DevOps Autocoder Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
            .button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
            .button:hover { background: #0056b3; }
            .result { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .success { border-left: 4px solid #28a745; }
            .error { border-left: 4px solid #dc3545; }
            .warning { border-left: 4px solid #ffc107; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 LangGraph DevOps Autocoder</h1>
            <h2>Automated Code Generation + Deployment</h2>
            
            <h3>🎯 Test Automation</h3>
            <button class="button" onclick="testExport()">Test Export Feature</button>
            <button class="button" onclick="testSearch()">Test Search Feature</button>
            <button class="button" onclick="testCombo()">Test Combined Features</button>
            
            <h3>📊 System Status</h3>
            <button class="button" onclick="checkHealth()">Check Health</button>
            <button class="button" onclick="listDeployments()">View Deployments</button>
            
            <div id="results"></div>
        </div>
        
        <script>
            async function testExport() {
                showLoading();
                try {
                    const response = await fetch('/webhook/jira?auto_deploy=true', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            issue: {
                                key: 'DEMO-EXPORT',
                                fields: {
                                    summary: 'Add CSV export functionality',
                                    issuetype: { name: 'Story' },
                                    description: 'Add export button for downloading todos as CSV file'
                                }
                            }
                        })
                    });
                    const result = await response.json();
                    showResult(result, 'Export Feature Test');
                } catch (error) {
                    showError(error.message);
                }
            }
            
            async function testSearch() {
                showLoading();
                try {
                    const response = await fetch('/webhook/jira?auto_deploy=true', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            issue: {
                                key: 'DEMO-SEARCH',
                                fields: {
                                    summary: 'Add real-time search functionality',
                                    issuetype: { name: 'Story' },
                                    description: 'Add search bar for filtering todos in real-time'
                                }
                            }
                        })
                    });
                    const result = await response.json();
                    showResult(result, 'Search Feature Test');
                } catch (error) {
                    showError(error.message);
                }
            }
            
            async function testCombo() {
                showLoading();
                try {
                    const response = await fetch('/webhook/jira?auto_deploy=true', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            issue: {
                                key: 'DEMO-COMBO',
                                fields: {
                                    summary: 'Add search and export features together',
                                    issuetype: { name: 'Epic' },
                                    description: 'Implement both search functionality and CSV export capability for comprehensive todo management'
                                }
                            }
                        })
                    });
                    const result = await response.json();
                    showResult(result, 'Combined Features Test');
                } catch (error) {
                    showError(error.message);
                }
            }
            
            async function checkHealth() {
                try {
                    const response = await fetch('/health/deployment');
                    const health = await response.json();
                    showResult(health, 'System Health Check');
                } catch (error) {
                    showError(error.message);
                }
            }
            
            async function listDeployments() {
                try {
                    const response = await fetch('/deployments');
                    const deployments = await response.json();
                    showResult(deployments, 'Deployment History');
                } catch (error) {
                    showError(error.message);
                }
            }
            
            function showLoading() {
                document.getElementById('results').innerHTML = '<div class="result">⏳ Processing automation pipeline...</div>';
            }
            
            function showResult(result, title) {
                const resultDiv = document.getElementById('results');
                const status = result.status || result.overall_healthy ? 'success' : 'warning';
                resultDiv.innerHTML = `
                    <div class="result ${status}">
                        <h4>${title}</h4>
                        <pre>${JSON.stringify(result, null, 2)}</pre>
                    </div>
                `;
            }
            
            function showError(message) {
                document.getElementById('results').innerHTML = `
                    <div class="result error">
                        <h4>Error</h4>
                        <p>${message}</p>
                    </div>
                `;
            }
        </script>
    </body>
    </html>
    """)

# Keep all existing endpoints
@app.get("/health")
async def health_check():
    """Overall system health check"""
    health_status = {
        "status": "healthy",
        "service": "devops-autocoder-enhanced",
        "main_module": "available" if MAIN_AVAILABLE else "error",
    }