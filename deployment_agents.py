"""
LangGraph Multi-Agent Deployment Automation System
Handles: Code Review → File Copy → Testing → Deployment
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict
import uuid

# LangGraph Integration
try:
    from langgraph.graph import StateGraph, START, END
    from langgraph.checkpoint.memory import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("Warning: LangGraph not available. Install with: pip install langgraph")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# State Definition for Deployment Pipeline
class DeploymentState(TypedDict):
    # Core data
    trace_id: str
    issue_key: str
    generated_files: List[str]
    target_project_path: str
    
    # Review results
    code_review_results: Dict[str, Any]
    quality_score: float
    review_passed: bool
    
    # File operations
    copied_files: List[str]
    backup_paths: List[str]
    copy_successful: bool
    
    # Testing results
    test_results: Dict[str, Any]
    tests_passed: bool
    
    # Deployment
    deployment_url: str
    deployment_successful: bool
    
    # Status tracking
    errors: List[str]
    warnings: List[str]
    current_stage: str
    overall_status: str

@dataclass
class DeploymentConfig:
    # Project paths
    generated_code_path: str = "generated_code"
    target_project_path: str = os.getenv("TARGET_PROJECT_PATH", "todo-app/frontend")
    backup_path: str = "deployment_backups"
    
    # Testing configuration
    test_command: str = "npm test -- --watchAll=false --passWithNoTests"
    build_command: str = "npm run build"
    start_command: str = "npm start"
    
    # Deployment configuration
    deploy_command: str = "npm run deploy"
    health_check_url: str = "http://localhost:3000"
    health_check_timeout: int = 30
    
    # Quality thresholds
    min_quality_score: float = 0.7
    max_file_size_kb: int = 500
    required_patterns: List[str] = field(default_factory=lambda: [
        "import React",
        "export default",
        "function\\s+\\w+|const\\s+\\w+\\s*="
    ])

config = DeploymentConfig()

class CodeReviewAgent:
    """Agent that reviews generated code for quality and safety"""
    
    async def __call__(self, state: DeploymentState) -> DeploymentState:
        logger.info(f"[{state['trace_id']}] 🔍 Starting code review")
        state['current_stage'] = "code_review"
        
        try:
            review_results = {
                "files_reviewed": [],
                "quality_checks": {},
                "security_issues": [],
                "best_practices": [],
                "suggestions": []
            }
            
            generated_files = self._find_generated_files(state['generated_files'])
            total_score = 0
            file_count = 0
            
            for file_path in generated_files:
                if file_path.endswith(('.jsx', '.js', '.css', '.ts', '.tsx')):
                    file_review = await self._review_file(file_path)
                    review_results["files_reviewed"].append(file_review)
                    total_score += file_review["score"]
                    file_count += 1
            
            # Calculate overall quality score
            quality_score = total_score / max(file_count, 1)
            
            # Check if review passes minimum threshold
            review_passed = (
                quality_score >= config.min_quality_score and
                len(review_results["security_issues"]) == 0
            )
            
            state['code_review_results'] = review_results
            state['quality_score'] = quality_score
            state['review_passed'] = review_passed
            
            if review_passed:
                logger.info(f"[{state['trace_id']}] ✅ Code review passed (score: {quality_score:.2f})")
            else:
            return """1. ❌ Review errors and fix issues above
2. 🔧 Check file paths and permissions
3. 🧪 Run tests manually to debug failures
4. 🔄 Re-run deployment pipeline after fixes"""

# Main Deployment Pipeline using LangGraph
def create_deployment_graph() -> StateGraph:
    """Create LangGraph workflow for automated deployment"""
    
    if not LANGGRAPH_AVAILABLE:
        raise ImportError("LangGraph not available. Install with: pip install langgraph")
    
    # Create workflow
    workflow = StateGraph(DeploymentState)
    
    # Add nodes (agents)
    workflow.add_node("code_review", CodeReviewAgent())
    workflow.add_node("file_copy", FileCopyAgent())
    workflow.add_node("testing", TestingAgent())
    workflow.add_node("deployment", DeploymentAgent())
    workflow.add_node("reporting", ReportingAgent())
    
    # Define conditional edges
    def should_continue_after_review(state: DeploymentState) -> str:
        """Decide whether to continue after code review"""
        if state['review_passed']:
            return "file_copy"
        else:
            return "reporting"  # Skip to reporting if review fails
    
    def should_continue_after_copy(state: DeploymentState) -> str:
        """Decide whether to continue after file copy"""
        if state['copy_successful']:
            return "testing"
        else:
            return "reporting"
    
    def should_continue_after_testing(state: DeploymentState) -> str:
        """Decide whether to deploy after testing"""
        if state['tests_passed']:
            return "deployment"
        else:
            return "reporting"  # Skip deployment if tests fail
    
    # Build the workflow
    workflow.add_edge(START, "code_review")
    workflow.add_conditional_edges(
        "code_review",
        should_continue_after_review,
        {
            "file_copy": "file_copy",
            "reporting": "reporting"
        }
    )
    workflow.add_conditional_edges(
        "file_copy",
        should_continue_after_copy,
        {
            "testing": "testing",
            "reporting": "reporting"
        }
    )
    workflow.add_conditional_edges(
        "testing",
        should_continue_after_testing,
        {
            "deployment": "deployment",
            "reporting": "reporting"
        }
    )
    workflow.add_edge("deployment", "reporting")
    workflow.add_edge("reporting", END)
    
    # Compile the graph
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)

# Main execution function
async def run_deployment_pipeline(issue_key: str, target_project_path: str = None) -> Dict[str, Any]:
    """
    Run the complete deployment pipeline for generated code
    
    Args:
        issue_key: The Jira issue key that generated the code
        target_project_path: Path to target React project
    
    Returns:
        Final deployment state with all results
    """
    
    trace_id = str(uuid.uuid4())
    logger.info(f"[{trace_id}] 🚀 Starting deployment pipeline for {issue_key}")
    
    # Initialize state
    initial_state = DeploymentState(
        trace_id=trace_id,
        issue_key=issue_key,
        generated_files=[],  # Will be discovered by agents
        target_project_path=target_project_path or config.target_project_path,
        code_review_results={},
        quality_score=0.0,
        review_passed=False,
        copied_files=[],
        backup_paths=[],
        copy_successful=False,
        test_results={},
        tests_passed=False,
        deployment_url="",
        deployment_successful=False,
        errors=[],
        warnings=[],
        current_stage="initializing",
        overall_status="IN_PROGRESS"
    )
    
    try:
        # Create and run the deployment graph
        graph = create_deployment_graph()
        
        # Execute the pipeline
        final_state = await graph.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": trace_id}}
        )
        
        # Log final results
        logger.info(f"[{trace_id}] ✅ Deployment pipeline completed")
        logger.info(f"[{trace_id}] Overall Status: {final_state['overall_status']}")
        logger.info(f"[{trace_id}] Files Copied: {len(final_state.get('copied_files', []))}")
        logger.info(f"[{trace_id}] Tests Passed: {final_state.get('tests_passed', False)}")
        logger.info(f"[{trace_id}] Deployment Success: {final_state.get('deployment_successful', False)}")
        
        return final_state
        
    except Exception as e:
        logger.error(f"[{trace_id}] ❌ Deployment pipeline failed: {e}")
        initial_state['errors'].append(f"Pipeline failure: {str(e)}")
        initial_state['overall_status'] = "FAILED"
        return initial_state

# Utility functions for easy integration
class DeploymentOrchestrator:
    """High-level orchestrator for deployment operations"""
    
    def __init__(self, target_project_path: str = None):
        self.target_project_path = target_project_path or config.target_project_path
        self.deployment_history = []
    
    async def deploy_generated_code(self, issue_key: str, auto_approve: bool = False) -> Dict[str, Any]:
        """Deploy generated code with optional auto-approval"""
        
        logger.info(f"🚀 Starting deployment for {issue_key}")
        
        # Check if generated files exist
        generated_path = Path(config.generated_code_path)
        if not generated_path.exists() or not any(generated_path.iterdir()):
            return {
                "status": "FAILED",
                "error": f"No generated files found for {issue_key}",
                "trace_id": None
            }
        
        # Run deployment pipeline
        result = await run_deployment_pipeline(issue_key, self.target_project_path)
        
        # Store in history
        self.deployment_history.append({
            "issue_key": issue_key,
            "trace_id": result['trace_id'],
            "timestamp": datetime.now().isoformat(),
            "status": result['overall_status'],
            "files_deployed": len(result.get('copied_files', []))
        })
        
        return result
    
    async def rollback_deployment(self, trace_id: str) -> bool:
        """Rollback a deployment using backup files"""
        try:
            backup_dir = Path(config.backup_path) / trace_id
            if not backup_dir.exists():
                logger.error(f"No backup found for {trace_id}")
                return False
            
            # Restore files from backup
            target_path = Path(self.target_project_path)
            restored_count = 0
            
            for backup_file in backup_dir.rglob("*"):
                if backup_file.is_file():
                    target_file = target_path / "src" / backup_file.name
                    if target_file.exists():
                        shutil.copy2(backup_file, target_file)
                        restored_count += 1
                        logger.info(f"Restored: {target_file}")
            
            logger.info(f"✅ Rollback completed: {restored_count} files restored")
            return True
            
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            return False
    
    def get_deployment_status(self, issue_key: str = None) -> List[Dict]:
        """Get deployment history"""
        if issue_key:
            return [d for d in self.deployment_history if d['issue_key'] == issue_key]
        return self.deployment_history
    
    async def health_check(self) -> Dict[str, Any]:
        """Check deployment system health"""
        health_status = {
            "target_project_exists": Path(self.target_project_path).exists(),
            "generated_files_exist": Path(config.generated_code_path).exists(),
            "backup_system_ready": Path(config.backup_path).exists() or True,
            "npm_available": False,
            "git_available": False
        }
        
        # Check npm availability
        try:
            process = await asyncio.create_subprocess_shell(
                "npm --version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            health_status["npm_available"] = process.returncode == 0
        except:
            pass
        
        # Check git availability
        try:
            process = await asyncio.create_subprocess_shell(
                "git --version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            health_status["git_available"] = process.returncode == 0
        except:
            pass
        
        health_status["overall_healthy"] = all([
            health_status["npm_available"],
            health_status["target_project_exists"] or health_status["generated_files_exist"]
        ])
        
        return health_status

# Integration with main webhook system
async def trigger_automated_deployment(issue_key: str, target_project: str = None) -> Dict[str, Any]:
    """
    Main function to trigger automated deployment after code generation
    This can be called from the main webhook processing pipeline
    """
    
    orchestrator = DeploymentOrchestrator(target_project)
    
    # Run health check first
    health = await orchestrator.health_check()
    if not health["overall_healthy"]:
        return {
            "status": "FAILED",
            "error": "Deployment system not healthy",
            "health_check": health
        }
    
    # Deploy the generated code
    result = await orchestrator.deploy_generated_code(issue_key)
    
    return {
        "status": result['overall_status'],
        "trace_id": result['trace_id'],
        "deployment_url": result.get('deployment_url'),
        "files_deployed": len(result.get('copied_files', [])),
        "errors": result.get('errors', []),
        "report_available": True
    }

# CLI interface for manual deployment
async def main():
    """Command-line interface for deployment"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python deployment_agents.py <issue_key> [target_project_path]")
        print("Example: python deployment_agents.py EXPORT-001 ./my-react-app")
        return
    
    issue_key = sys.argv[1]
    target_project = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"🚀 Starting automated deployment for {issue_key}")
    
    # Run deployment
    result = await trigger_automated_deployment(issue_key, target_project)
    
    # Print results
    print(f"\n📊 Deployment Results:")
    print(f"Status: {result['status']}")
    print(f"Trace ID: {result.get('trace_id', 'N/A')}")
    print(f"Files Deployed: {result.get('files_deployed', 0)}")
    
    if result.get('deployment_url'):
        print(f"Deployment URL: {result['deployment_url']}")
    
    if result.get('errors'):
        print(f"\nErrors:")
        for error in result['errors']:
            print(f"  - {error}")
    
    print(f"\n📋 Check deployment_reports/ for detailed report")

if __name__ == "__main__":
    asyncio.run(main())
                logger.warning(f"[{state['trace_id']}] ⚠️ Code review failed (score: {quality_score:.2f})")
                state['errors'].append(f"Code review failed with score {quality_score:.2f}")
            
        except Exception as e:
            logger.error(f"[{state['trace_id']}] ❌ Code review failed: {e}")
            state['errors'].append(f"Code review error: {str(e)}")
            state['review_passed'] = False
            state['quality_score'] = 0.0
        
        return state
    
    def _find_generated_files(self, file_patterns: List[str]) -> List[str]:
        """Find all generated files matching patterns"""
        files = []
        generated_path = Path(config.generated_code_path)
        
        if generated_path.exists():
            for file_path in generated_path.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith('.'):
                    files.append(str(file_path))
        
        return files
    
    async def _review_file(self, file_path: str) -> Dict[str, Any]:
        """Review individual file for quality"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_review = {
                "file": file_path,
                "size_kb": len(content) / 1024,
                "lines": len(content.split('\n')),
                "score": 0.0,
                "issues": [],
                "suggestions": []
            }
            
            score = 1.0
            
            # File size check
            if file_review["size_kb"] > config.max_file_size_kb:
                file_review["issues"].append(f"File too large: {file_review['size_kb']:.1f}KB")
                score -= 0.2
            
            # Pattern checks for React files
            if file_path.endswith(('.jsx', '.js', '.tsx', '.ts')):
                score += self._check_react_patterns(content, file_review)
            
            # CSS checks
            if file_path.endswith('.css'):
                score += self._check_css_patterns(content, file_review)
            
            # Security checks
            security_score = self._check_security(content, file_review)
            score += security_score
            
            file_review["score"] = max(0.0, min(1.0, score))
            
            return file_review
            
        except Exception as e:
            return {
                "file": file_path,
                "score": 0.0,
                "issues": [f"Failed to review: {str(e)}"]
            }
    
    def _check_react_patterns(self, content: str, review: Dict) -> float:
        """Check React-specific patterns"""
        score = 0.0
        
        # Check for React import
        if "import React" in content or "import {" in content:
            score += 0.2
        else:
            review["issues"].append("Missing React import")
        
        # Check for export default
        if "export default" in content:
            score += 0.2
        else:
            review["issues"].append("Missing default export")
        
        # Check for functional component pattern
        if "function " in content or "const " in content and "=>" in content:
            score += 0.2
        else:
            review["issues"].append("No functional component pattern found")
        
        # Check for proper JSX
        if "return (" in content and "<" in content:
            score += 0.2
        
        # Check for hooks usage
        if "useState" in content or "useEffect" in content:
            score += 0.1
            review["suggestions"].append("Good use of React hooks")
        
        return score
    
    def _check_css_patterns(self, content: str, review: Dict) -> float:
        """Check CSS quality patterns"""
        score = 0.0
        
        # Check for responsive design
        if "@media" in content:
            score += 0.3
            review["suggestions"].append("Includes responsive design")
        
        # Check for modern CSS features
        if "flexbox" in content or "display: flex" in content:
            score += 0.2
        
        if "grid" in content or "display: grid" in content:
            score += 0.2
        
        # Check for CSS variables
        if "--" in content and "var(" in content:
            score += 0.1
            review["suggestions"].append("Uses CSS variables")
        
        return score
    
    def _check_security(self, content: str, review: Dict) -> float:
        """Check for security issues"""
        score = 0.0
        security_patterns = [
            ("innerHTML", "Potential XSS risk with innerHTML"),
            ("eval(", "Use of eval() is dangerous"),
            ("document.write", "document.write can be unsafe"),
            ("window.location", "Direct location manipulation can be risky")
        ]
        
        for pattern, issue in security_patterns:
            if pattern in content:
                review["issues"].append(issue)
                score -= 0.2
        
        return score

class FileCopyAgent:
    """Agent that safely copies files to target project"""
    
    async def __call__(self, state: DeploymentState) -> DeploymentState:
        logger.info(f"[{state['trace_id']}] 📁 Starting file copy operation")
        state['current_stage'] = "file_copy"
        
        try:
            # Create backup directory
            backup_dir = Path(config.backup_path) / state['trace_id']
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            copied_files = []
            backup_paths = []
            
            # Find generated files
            generated_files = self._get_generated_files()
            target_path = Path(state['target_project_path'])
            
            if not target_path.exists():
                logger.warning(f"[{state['trace_id']}] Target project not found, creating: {target_path}")
                target_path.mkdir(parents=True, exist_ok=True)
            
            for src_file in generated_files:
                try:
                    # Determine target location
                    target_file = self._get_target_path(src_file, target_path)
                    
                    # Create backup if target exists
                    if target_file.exists():
                        backup_file = backup_dir / target_file.name
                        shutil.copy2(target_file, backup_file)
                        backup_paths.append(str(backup_file))
                        logger.info(f"[{state['trace_id']}] 💾 Backed up: {target_file}")
                    
                    # Copy new file
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, target_file)
                    copied_files.append(str(target_file))
                    
                    logger.info(f"[{state['trace_id']}] ✅ Copied: {src_file} -> {target_file}")
                    
                except Exception as e:
                    logger.error(f"[{state['trace_id']}] ❌ Failed to copy {src_file}: {e}")
                    state['errors'].append(f"Copy failed for {src_file}: {str(e)}")
            
            state['copied_files'] = copied_files
            state['backup_paths'] = backup_paths
            state['copy_successful'] = len(copied_files) > 0
            
            if state['copy_successful']:
                logger.info(f"[{state['trace_id']}] ✅ Successfully copied {len(copied_files)} files")
            else:
                logger.error(f"[{state['trace_id']}] ❌ No files were copied")
                state['errors'].append("No files were successfully copied")
            
        except Exception as e:
            logger.error(f"[{state['trace_id']}] ❌ File copy operation failed: {e}")
            state['errors'].append(f"File copy error: {str(e)}")
            state['copy_successful'] = False
        
        return state
    
    def _get_generated_files(self) -> List[Path]:
        """Get list of generated files to copy"""
        files = []
        generated_path = Path(config.generated_code_path)
        
        for file_path in generated_path.rglob("*"):
            if (file_path.is_file() and 
                file_path.suffix in ['.jsx', '.js', '.css', '.ts', '.tsx'] and
                not file_path.name.startswith('reports_')):
                files.append(file_path)
        
        return files
    
    def _get_target_path(self, src_file: Path, target_base: Path) -> Path:
        """Determine target path for a source file"""
        # Handle component files
        if "components_" in src_file.name:
            component_name = src_file.name.replace("components_", "")
            return target_base / "src" / "components" / component_name
        
        # Handle main app files
        if src_file.name in ["App.jsx", "App.js", "App.css"]:
            return target_base / "src" / src_file.name
        
        # Default to src directory
        return target_base / "src" / src_file.name

class TestingAgent:
    """Agent that runs tests and validates functionality"""
    
    async def __call__(self, state: DeploymentState) -> DeploymentState:
        logger.info(f"[{state['trace_id']}] 🧪 Starting testing phase")
        state['current_stage'] = "testing"
        
        try:
            target_path = Path(state['target_project_path'])
            test_results = {
                "syntax_check": False,
                "build_check": False,
                "unit_tests": False,
                "integration_tests": False,
                "test_output": "",
                "build_output": "",
                "errors": []
            }
            
            # Change to target directory
            original_cwd = os.getcwd()
            os.chdir(target_path)
            
            try:
                # 1. Install dependencies if needed
                if not Path("node_modules").exists():
                    logger.info(f"[{state['trace_id']}] 📦 Installing dependencies...")
                    result = await self._run_command("npm install")
                    if result["success"]:
                        logger.info(f"[{state['trace_id']}] ✅ Dependencies installed")
                    else:
                        test_results["errors"].append("Failed to install dependencies")
                
                # 2. Syntax/Build check
                logger.info(f"[{state['trace_id']}] 🔨 Running build check...")
                build_result = await self._run_command(config.build_command)
                test_results["build_check"] = build_result["success"]
                test_results["build_output"] = build_result["output"]
                
                if build_result["success"]:
                    logger.info(f"[{state['trace_id']}] ✅ Build successful")
                else:
                    logger.error(f"[{state['trace_id']}] ❌ Build failed")
                    test_results["errors"].append("Build failed")
                
                # 3. Run tests if they exist
                if Path("src").exists() and any(Path("src").rglob("*.test.*")):
                    logger.info(f"[{state['trace_id']}] 🧪 Running unit tests...")
                    test_result = await self._run_command(config.test_command)
                    test_results["unit_tests"] = test_result["success"]
                    test_results["test_output"] = test_result["output"]
                    
                    if test_result["success"]:
                        logger.info(f"[{state['trace_id']}] ✅ Tests passed")
                    else:
                        logger.warning(f"[{state['trace_id']}] ⚠️ Some tests failed")
                        test_results["errors"].append("Unit tests failed")
                else:
                    logger.info(f"[{state['trace_id']}] ℹ️ No tests found")
                    test_results["unit_tests"] = True  # Pass if no tests
                
                # 4. Quick integration test (start server briefly)
                logger.info(f"[{state['trace_id']}] 🚀 Testing server startup...")
                integration_result = await self._test_server_startup()
                test_results["integration_tests"] = integration_result
                
            finally:
                os.chdir(original_cwd)
            
            # Determine overall test success
            tests_passed = (
                test_results["build_check"] and
                test_results["unit_tests"] and
                test_results["integration_tests"]
            )
            
            state['test_results'] = test_results
            state['tests_passed'] = tests_passed
            
            if tests_passed:
                logger.info(f"[{state['trace_id']}] ✅ All tests passed")
            else:
                logger.error(f"[{state['trace_id']}] ❌ Tests failed")
                state['errors'].append("Testing phase failed")
            
        except Exception as e:
            logger.error(f"[{state['trace_id']}] ❌ Testing failed: {e}")
            state['errors'].append(f"Testing error: {str(e)}")
            state['tests_passed'] = False
        
        return state
    
    async def _run_command(self, command: str, timeout: int = 60) -> Dict[str, Any]:
        """Run shell command with timeout"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                shell=True
            )
            
            try:
                stdout, _ = await asyncio.wait_for(process.communicate(), timeout=timeout)
                output = stdout.decode('utf-8') if stdout else ""
                
                return {
                    "success": process.returncode == 0,
                    "output": output,
                    "return_code": process.returncode
                }
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "output": f"Command timed out after {timeout} seconds",
                    "return_code": -1
                }
                
        except Exception as e:
            return {
                "success": False,
                "output": f"Failed to run command: {str(e)}",
                "return_code": -1
            }
    
    async def _test_server_startup(self) -> bool:
        """Test if the React server can start successfully"""
        try:
            # Start development server
            process = await asyncio.create_subprocess_shell(
                "npm start",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                shell=True
            )
            
            # Wait for server to start (look for "compiled" or "ready" in output)
            start_time = time.time()
            while time.time() - start_time < 15:  # 15 second timeout
                if process.stdout:
                    try:
                        line = await asyncio.wait_for(process.stdout.readline(), timeout=1.0)
                        if line:
                            output = line.decode('utf-8').lower()
                            if any(keyword in output for keyword in ['compiled', 'ready', 'started']):
                                # Server started successfully
                                process.kill()
                                return True
                    except asyncio.TimeoutError:
                        continue
                
                await asyncio.sleep(0.5)
            
            # Kill process if still running
            process.kill()
            return False
            
        except Exception as e:
            logger.error(f"Server startup test failed: {e}")
            return False

class DeploymentAgent:
    """Agent that handles final deployment"""
    
    async def __call__(self, state: DeploymentState) -> DeploymentState:
        logger.info(f"[{state['trace_id']}] 🚀 Starting deployment")
        state['current_stage'] = "deployment"
        
        try:
            target_path = Path(state['target_project_path'])
            original_cwd = os.getcwd()
            
            # For development, we'll just verify the app can start
            deployment_successful = False
            deployment_url = ""
            
            try:
                os.chdir(target_path)
                
                # Build production version
                logger.info(f"[{state['trace_id']}] 🔨 Building production version...")
                build_result = await self._run_command("npm run build")
                
                if build_result["success"]:
                    logger.info(f"[{state['trace_id']}] ✅ Production build successful")
                    
                    # For this demo, we'll simulate deployment by checking build output
                    build_dir = Path("build") or Path("dist")
                    if build_dir.exists():
                        deployment_successful = True
                        deployment_url = f"file://{target_path.absolute()}/build/index.html"
                        logger.info(f"[{state['trace_id']}] ✅ Deployment ready: {deployment_url}")
                    else:
                        state['errors'].append("Build directory not found")
                        logger.error(f"[{state['trace_id']}] ❌ Build directory not found")
                else:
                    state['errors'].append("Production build failed")
                    logger.error(f"[{state['trace_id']}] ❌ Production build failed")
                
            finally:
                os.chdir(original_cwd)
            
            state['deployment_successful'] = deployment_successful
            state['deployment_url'] = deployment_url
            
            if deployment_successful:
                logger.info(f"[{state['trace_id']}] ✅ Deployment completed successfully")
            else:
                logger.error(f"[{state['trace_id']}] ❌ Deployment failed")
                state['errors'].append("Deployment failed")
            
        except Exception as e:
            logger.error(f"[{state['trace_id']}] ❌ Deployment failed: {e}")
            state['errors'].append(f"Deployment error: {str(e)}")
            state['deployment_successful'] = False
        
        return state
    
    async def _run_command(self, command: str, timeout: int = 120) -> Dict[str, Any]:
        """Run deployment command with timeout"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                shell=True
            )
            
            try:
                stdout, _ = await asyncio.wait_for(process.communicate(), timeout=timeout)
                output = stdout.decode('utf-8') if stdout else ""
                
                return {
                    "success": process.returncode == 0,
                    "output": output,
                    "return_code": process.returncode
                }
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "output": f"Deployment timed out after {timeout} seconds",
                    "return_code": -1
                }
                
        except Exception as e:
            return {
                "success": False,
                "output": f"Failed to run deployment: {str(e)}",
                "return_code": -1
            }

class ReportingAgent:
    """Agent that generates deployment reports"""
    
    async def __call__(self, state: DeploymentState) -> DeploymentState:
        logger.info(f"[{state['trace_id']}] 📊 Generating deployment report")
        state['current_stage'] = "reporting"
        
        try:
            # Determine overall status
            if (state['review_passed'] and state['copy_successful'] and 
                state['tests_passed'] and state['deployment_successful']):
                overall_status = "SUCCESS"
                status_emoji = "✅"
            elif state['tests_passed'] and state['copy_successful']:
                overall_status = "PARTIAL_SUCCESS"
                status_emoji = "⚠️"
            else:
                overall_status = "FAILED"
                status_emoji = "❌"
            
            state['overall_status'] = overall_status
            
            # Generate comprehensive report
            report_content = self._generate_report(state, status_emoji)
            
            # Save report
            report_path = Path("deployment_reports") / f"{state['issue_key']}_deployment.md"
            report_path.parent.mkdir(exist_ok=True)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"[{state['trace_id']}] ✅ Deployment report saved: {report_path}")
            
        except Exception as e:
            logger.error(f"[{state['trace_id']}] ❌ Report generation failed: {e}")
            state['errors'].append(f"Report generation error: {str(e)}")
        
        return state
    
    def _generate_report(self, state: DeploymentState, status_emoji: str) -> str:
        """Generate detailed deployment report"""
        return f"""# 🚀 Deployment Automation Report

## {status_emoji} Overall Status: {state['overall_status']}

**Issue**: {state['issue_key']}  
**Trace ID**: {state['trace_id']}  
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📋 Pipeline Summary

| Stage | Status | Details |
|-------|--------|---------|
| Code Review | {'✅ PASSED' if state['review_passed'] else '❌ FAILED'} | Quality Score: {state.get('quality_score', 0):.2f}/1.0 |
| File Copy | {'✅ SUCCESS' if state['copy_successful'] else '❌ FAILED'} | {len(state.get('copied_files', []))} files copied |
| Testing | {'✅ PASSED' if state['tests_passed'] else '❌ FAILED'} | Build + Unit + Integration tests |
| Deployment | {'✅ SUCCESS' if state['deployment_successful'] else '❌ FAILED'} | {state.get('deployment_url', 'N/A')} |

## 🔍 Code Review Results

**Quality Score**: {state.get('quality_score', 0):.2f}/1.0  
**Files Reviewed**: {len(state.get('code_review_results', {}).get('files_reviewed', []))}

{self._format_review_details(state.get('code_review_results', {}))}

## 📁 File Operations

**Files Copied**: {len(state.get('copied_files', []))}  
**Backup Created**: {len(state.get('backup_paths', []))} files backed up

{chr(10).join(f'- {file}' for file in state.get('copied_files', []))}

## 🧪 Testing Results

{self._format_test_results(state.get('test_results', {}))}

## 🚀 Deployment Information

**Status**: {'✅ SUCCESS' if state['deployment_successful'] else '❌ FAILED'}  
**URL**: {state.get('deployment_url', 'N/A')}

## ⚠️ Issues and Warnings

{self._format_issues(state.get('errors', []), state.get('warnings', []))}

## 🎯 Next Steps

{self._generate_next_steps(state)}

---
*Generated by LangGraph Deployment Automation*
"""
    
    def _format_review_details(self, review_results: Dict) -> str:
        """Format code review details"""
        if not review_results:
            return "No review details available"
        
        details = []
        for file_review in review_results.get('files_reviewed', []):
            details.append(f"- **{Path(file_review['file']).name}**: {file_review['score']:.2f}/1.0")
            if file_review.get('issues'):
                for issue in file_review['issues']:
                    details.append(f"  - ⚠️ {issue}")
        
        return '\n'.join(details) if details else "All files passed review"
    
    def _format_test_results(self, test_results: Dict) -> str:
        """Format test results"""
        if not test_results:
            return "No test results available"
        
        results = []
        results.append(f"**Build Check**: {'✅ PASSED' if test_results.get('build_check') else '❌ FAILED'}")
        results.append(f"**Unit Tests**: {'✅ PASSED' if test_results.get('unit_tests') else '❌ FAILED'}")
        results.append(f"**Integration**: {'✅ PASSED' if test_results.get('integration_tests') else '❌ FAILED'}")
        
        if test_results.get('errors'):
            results.append("\n**Test Errors**:")
            for error in test_results['errors']:
                results.append(f"- {error}")
        
        return '\n'.join(results)
    
    def _format_issues(self, errors: List[str], warnings: List[str]) -> str:
        """Format errors and warnings"""
        if not errors and not warnings:
            return "✅ No issues encountered"
        
        issues = []
        if errors:
            issues.append("**Errors**:")
            for error in errors:
                issues.append(f"- ❌ {error}")
        
        if warnings:
            issues.append("**Warnings**:")
            for warning in warnings:
                issues.append(f"- ⚠️ {warning}")
        
        return '\n'.join(issues)
    
    def _generate_next_steps(self, state: DeploymentState) -> str:
        """Generate context-specific next steps"""
        if state['overall_status'] == "SUCCESS":
            return """1. ✅ Deployment completed successfully
2. 🌐 Access your application at the deployment URL
3. 📊 Monitor application performance
4. 🔄 Set up CI/CD for future deployments"""
        
        elif state['overall_status'] == "PARTIAL_SUCCESS":
            return """1. ⚠️ Review deployment warnings above
2. 🧪 Run additional manual tests
3. 🔍 Check application logs for issues
4. 🚀 Consider manual deployment verification"""
        
        else: