"""
Production-Ready LLM-Powered DevOps Automation System
With Complete Jira and GitHub Integration
"""

import asyncio
import base64
import json
import logging
import os
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

# External integrations
import requests
try:
    import openai
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    
# Manual .env file loader (add this after your existing imports)
import os
from pathlib import Path

def load_env_file():
    """Manually load environment variables from .env file"""
    env_file = Path('../.env')
    if env_file.exists():
        print(f"Loading environment variables from {env_file.absolute()}")
        with open(env_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    try:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        os.environ[key] = value
                        print(f"  Loaded: {key}")
                    except ValueError:
                        print(f"  Skipped malformed line {line_num}: {line}")
        print("Environment variables loaded successfully")
    else:
        print(f"No .env file found at {env_file.absolute()}")
        print("Please create a .env file in the project root with your credentials")

# Load environment variables
load_env_file()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
@dataclass
class Config:
    # LLM Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Jira Configuration
    jira_url: str = os.getenv("JIRA_URL", "")  # https://your-instance.atlassian.net
    jira_username: str = os.getenv("JIRA_USERNAME", "")  # your-email@company.com
    jira_api_token: str = os.getenv("JIRA_API_TOKEN", "")  # From Jira user settings
    jira_webhook_secret: str = os.getenv("JIRA_WEBHOOK_SECRET", "")
    
    # GitHub Configuration
    github_token: str = os.getenv("GITHUB_TOKEN", "")  # Personal access token
    github_repo: str = os.getenv("GITHUB_REPO", "")  # username/repository-name
    github_base_branch: str = os.getenv("GITHUB_BASE_BRANCH", "main")
    
    # Project Configuration
    project_root: str = os.getenv("PROJECT_ROOT", "..")
    frontend_path: str = os.getenv("FRONTEND_PATH", "../todo-app/frontend")
    backend_path: str = os.getenv("BACKEND_PATH", "../todo-app/backend")

config = Config()

# Data classes
@dataclass
class FileChange:
    file: str
    action: str
    lines_added: int = 0
    backup_path: Optional[str] = None

@dataclass
class JiraTransition:
    status: str
    comment: str
    attachments: List[str] = field(default_factory=list)

class AgentState(TypedDict):
    trace_id: str
    webhook_payload: Dict[str, Any]
    issue_key: str
    issue_summary: str
    issue_type: str
    issue_description: str
    requirements: Dict[str, Any]
    generated_code: Dict[str, str]
    file_changes: List[FileChange]
    branch_name: str
    commit_hash: str
    pr_url: str
    jira_updates: List[JiraTransition]
    errors: List[str]

def generate_trace_id() -> str:
    return str(uuid.uuid4())

class JiraClient:
    """Production Jira API client"""
    
    def __init__(self):
        if not all([config.jira_url, config.jira_username, config.jira_api_token]):
            logger.warning("Jira credentials not fully configured")
            self.enabled = False
        else:
            self.enabled = True
            self.auth = base64.b64encode(
                f"{config.jira_username}:{config.jira_api_token}".encode()
            ).decode()
    
    async def update_issue_status(self, issue_key: str, status: str, comment: str) -> bool:
        """Update Jira issue status and add comment"""
        if not self.enabled:
            logger.info(f"Jira disabled - would update {issue_key} to {status}")
            return True
        
        try:
            # Get available transitions
            transitions_url = f"{config.jira_url}/rest/api/2/issue/{issue_key}/transitions"
            headers = {
                "Authorization": f"Basic {self.auth}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(transitions_url, headers=headers)
            if response.status_code != 200:
                logger.error(f"Failed to get transitions: {response.text}")
                return False
            
            transitions = response.json()["transitions"]
            target_transition = None
            
            # Find transition to target status
            for transition in transitions:
                if transition["to"]["name"].lower() == status.lower():
                    target_transition = transition["id"]
                    break
            
            if not target_transition:
                logger.warning(f"No transition found to status: {status}")
                # Just add comment without status change
                return await self.add_comment(issue_key, comment)
            
            # Execute transition with comment
            transition_payload = {
                "transition": {"id": target_transition},
                "update": {
                    "comment": [{"add": {"body": comment}}]
                }
            }
            
            response = requests.post(transitions_url, json=transition_payload, headers=headers)
            
            if response.status_code == 204:
                logger.info(f"Successfully updated {issue_key} to {status}")
                return True
            else:
                logger.error(f"Failed to transition issue: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Jira API error: {e}")
            return False
    
    async def add_comment(self, issue_key: str, comment: str) -> bool:
        """Add comment to Jira issue"""
        if not self.enabled:
            logger.info(f"Jira disabled - would comment on {issue_key}")
            return True
        
        try:
            comment_url = f"{config.jira_url}/rest/api/2/issue/{issue_key}/comment"
            headers = {
                "Authorization": f"Basic {self.auth}",
                "Content-Type": "application/json"
            }
            
            payload = {"body": comment}
            response = requests.post(comment_url, json=payload, headers=headers)
            
            if response.status_code == 201:
                logger.info(f"Comment added to {issue_key}")
                return True
            else:
                logger.error(f"Failed to add comment: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to add Jira comment: {e}")
            return False

class GitHubClient:
    """Production GitHub API client"""
    
    def __init__(self):
        if not all([config.github_token, config.github_repo]):
            logger.warning("GitHub credentials not configured")
            self.enabled = False
        else:
            self.enabled = True
            self.headers = {
                "Authorization": f"token {config.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
    
    async def create_branch(self, branch_name: str, base_branch: str = None) -> bool:
        """Create new branch on GitHub"""
        if not self.enabled:
            logger.info(f"GitHub disabled - would create branch {branch_name}")
            return True
        
        try:
            base_branch = base_branch or config.github_base_branch
            
            # Get base branch SHA
            ref_url = f"https://api.github.com/repos/{config.github_repo}/git/ref/heads/{base_branch}"
            response = requests.get(ref_url, headers=self.headers)
            
            if response.status_code != 200:
                logger.error(f"Failed to get base branch: {response.text}")
                return False
            
            base_sha = response.json()["object"]["sha"]
            
            # Create new branch
            create_ref_url = f"https://api.github.com/repos/{config.github_repo}/git/refs"
            payload = {
                "ref": f"refs/heads/{branch_name}",
                "sha": base_sha
            }
            
            response = requests.post(create_ref_url, json=payload, headers=self.headers)
            
            if response.status_code == 201:
                logger.info(f"Created GitHub branch: {branch_name}")
                return True
            else:
                logger.error(f"Failed to create branch: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"GitHub branch creation error: {e}")
            return False
    
    async def create_pull_request(self, branch_name: str, title: str, description: str) -> Optional[str]:
        """Create pull request and return URL"""
        if not self.enabled:
            logger.info(f"GitHub disabled - would create PR for {branch_name}")
            return f"https://github.com/{config.github_repo}/pulls"
        
        try:
            pr_url = f"https://api.github.com/repos/{config.github_repo}/pulls"
            payload = {
                "title": title,
                "head": branch_name,
                "base": config.github_base_branch,
                "body": description
            }
            
            response = requests.post(pr_url, json=payload, headers=self.headers)
            
            if response.status_code == 201:
                pr_data = response.json()
                logger.info(f"Created PR: {pr_data['html_url']}")
                return pr_data["html_url"]
            else:
                logger.error(f"Failed to create PR: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"GitHub PR creation error: {e}")
            return None

class GitOperations:
    """Local Git operations"""
    
    @staticmethod
    def run_git_command(command: List[str], cwd: str = None) -> tuple[bool, str]:
        """Run git command and return success status and output"""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or config.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            return False, e.stderr.strip()
    
    @staticmethod
    async def create_and_checkout_branch(branch_name: str) -> bool:
        """Create and checkout new local branch"""
        success, output = GitOperations.run_git_command(['git', 'checkout', '-b', branch_name])
        if success:
            logger.info(f"Created and checked out branch: {branch_name}")
        else:
            logger.error(f"Failed to create branch: {output}")
        return success
    
    @staticmethod
    async def commit_changes(message: str, author_email: str = None) -> tuple[bool, str]:
        """Stage and commit all changes"""
        # Stage all changes
        success, output = GitOperations.run_git_command(['git', 'add', '.'])
        if not success:
            return False, f"Failed to stage changes: {output}"
        
        # Set author if provided
        commit_cmd = ['git', 'commit', '-m', message]
        if author_email:
            commit_cmd.extend(['--author', f"DevOps Automation <{author_email}>"])
        
        success, output = GitOperations.run_git_command(commit_cmd)
        if success:
            # Get commit hash
            success_hash, commit_hash = GitOperations.run_git_command(['git', 'rev-parse', 'HEAD'])
            return True, commit_hash if success_hash else "unknown"
        else:
            return False, f"Failed to commit: {output}"
    
    @staticmethod
    async def push_branch(branch_name: str) -> bool:
        """Push branch to origin"""
        success, output = GitOperations.run_git_command(['git', 'push', 'origin', branch_name])
        if success:
            logger.info(f"Pushed branch: {branch_name}")
        else:
            logger.error(f"Failed to push branch: {output}")
        return success

class FileManager:
    """Enhanced file manager with Git integration"""
    
    @staticmethod
    def create_backup(file_path: str, trace_id: str) -> str:
        """Create backup of existing file"""
        if not os.path.exists(file_path):
            return ""
            
        backup_dir = Path(f"../backups/{trace_id}")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        relative_path = Path(file_path).relative_to(Path(".."))
        backup_path = backup_dir / relative_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(file_path, backup_path)
        logger.info(f"Backup created: {file_path} -> {backup_path}")
        return str(backup_path)
    
    @staticmethod
    def write_file(file_path: str, content: str, trace_id: str) -> FileChange:
        """Write file with backup"""
        file_path_obj = Path(file_path)
        action = "modified" if file_path_obj.exists() else "created"
        
        backup_path = ""
        if action == "modified":
            backup_path = FileManager.create_backup(file_path, trace_id)
        
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path_obj, 'w', encoding='utf-8') as f:
            f.write(content)
        
        lines_added = len(content.split('\n'))
        logger.info(f"File {action}: {file_path} ({lines_added} lines)")
        
        return FileChange(
            file=file_path,
            action=action,
            lines_added=lines_added,
            backup_path=backup_path
        )

# Agent implementations (using previous code generation logic)
class RequirementsAnalyst:
    """AI-powered requirements analysis"""
    
    def __init__(self):
        if LLM_AVAILABLE and config.openai_api_key:
            self.client = openai.AsyncOpenAI(api_key=config.openai_api_key)
        else:
            self.client = None
    
    async def __call__(self, state: AgentState) -> AgentState:
        logger.info(f"[{state['trace_id']}] Analyzing requirements")
        
        try:
            if self.client:
                # Use previous LLM analysis logic
                state['requirements'] = await self._llm_analysis(state)
            else:
                # Use template-based analysis
                state['requirements'] = self._template_analysis(state)
                
        except Exception as e:
            logger.error(f"Requirements analysis failed: {e}")
            state['errors'].append(f"Requirements analysis error: {str(e)}")
            state['requirements'] = self._template_analysis(state)
        
        return state
    
    async def _llm_analysis(self, state: AgentState):
        """LLM-powered analysis (previous implementation)"""
        analysis_prompt = f"""
        Analyze this Jira ticket and extract technical requirements for a React todo application:
        
        Title: {state['issue_summary']}
        Description: {state['issue_description']}
        Type: {state['issue_type']}
        
        Return JSON with:
        {{
            "components_to_create": ["ComponentName.jsx"],
            "files_to_modify": ["src/App.jsx", "src/App.css"],
            "functional_requirements": ["specific functionality"],
            "technical_requirements": ["implementation details"],
            "priority": "high|medium|low"
        }}
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a software architect. Return only valid JSON."},
                {"role": "user", "content": analysis_prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        llm_analysis = json.loads(response.choices[0].message.content)
        
        return {
            "functional": llm_analysis.get("functional_requirements", []),
            "technical": llm_analysis.get("technical_requirements", []),
            "priority": llm_analysis.get("priority", "medium"),
            "files_to_modify": [f"{config.frontend_path}/{f}" for f in llm_analysis.get("files_to_modify", [])],
            "components_to_create": [f"{config.frontend_path}/src/components/{c}" for c in llm_analysis.get("components_to_create", [])],
            "ai_analysis": True
        }
    
    def _template_analysis(self, state: AgentState):
        """Template-based analysis fallback"""
        description = state['issue_description'].lower()
        
        requirements = {
            "functional": [],
            "technical": [],
            "files_to_modify": [],
            "components_to_create": [],
            "priority": "medium",
            "ai_analysis": False
        }
        
        if "search" in description or "filter" in description:
            requirements["functional"].append("Add search functionality")
            requirements["files_to_modify"].extend([
                f"{config.frontend_path}/src/App.jsx",
                f"{config.frontend_path}/src/App.css"
            ])
            requirements["components_to_create"].append(f"{config.frontend_path}/src/components/SearchBar.jsx")
        
        if "category" in description or "tag" in description:
            requirements["functional"].append("Add category functionality")
            requirements["files_to_modify"].extend([
                f"{config.frontend_path}/src/App.jsx",
                f"{config.frontend_path}/src/App.css"
            ])
            requirements["components_to_create"].append(f"{config.frontend_path}/src/components/CategorySelect.jsx")
        
        return requirements

class CodeGenerator:
    """Code generation with LLM/template hybrid approach"""
    
    def __init__(self):
        if LLM_AVAILABLE and config.openai_api_key:
            self.client = openai.AsyncOpenAI(api_key=config.openai_api_key)
        else:
            self.client = None
    
    async def __call__(self, state: AgentState) -> AgentState:
        logger.info(f"[{state['trace_id']}] Generating code")
        
        try:
            requirements = state['requirements']
            generated_code = {}
            
            # Generate components (using previous implementation)
            for component_path in requirements.get('components_to_create', []):
                component_name = component_path.split('/')[-1].replace('.jsx', '')
                
                if self.client:
                    code = await self._generate_component_with_llm(component_name, state)
                else:
                    code = self._generate_component_template(component_name, state['issue_description'])
                
                generated_code[component_path] = code
            
            # Update existing files
            for file_path in requirements.get('files_to_modify', []):
                if "App.jsx" in file_path:
                    updated_code = await self._update_app_file(file_path, state)
                    generated_code[file_path] = updated_code
                elif "App.css" in file_path:
                    updated_css = await self._update_css_file(state)
                    generated_code[file_path] = updated_css
            
            state['generated_code'] = generated_code
            logger.info(f"[{state['trace_id']}] Generated {len(generated_code)} files")
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            state['errors'].append(f"Code generation error: {str(e)}")
        
        return state
    
    async def _generate_component_with_llm(self, component_name: str, state: AgentState) -> str:
            """Generate React component using LLM"""
            prompt = f"""
            Generate a React functional component for: {component_name}
            
            "CRITICAL: Only use React built-in functionality. Do not import external libraries like react-datepicker, react-notification-system, date-fns, etc. Use standard HTML elements and built-in React hooks only."
            "Use modern React 18 compatible libraries only. For notifications, use react-hot-toast instead of react-notification-system. Prefer built-in HTML elements when possible."
            # In your code generation prompts, add these constraints:
            
            CRITICAL CONSTRAINTS:
            1. Use ONLY React built-in hooks (useState, useEffect)
            2. Use ONLY standard HTML elements (input, button, div, etc.)
            3. Do NOT import external libraries
            4. Do NOT use date pickers, notification systems, or complex UI libraries
            5. Keep all functionality simple and self-contained
            6. Preserve existing working code structure
            
            
            Context:
            - Feature: {state['issue_summary']}
            - Description: {state['issue_description']}
            
            IMPORTANT: Return ONLY the JavaScript/JSX code, no explanations, no markdown formatting.
            Start directly with 'import' and end with 'export default ComponentName;'
            
            Create a production-ready React component that:
            1. Uses modern React hooks (useState, useEffect as needed)
            2. Includes proper event handling
            3. Has accessible design
            4. Follows React best practices
            """
            
            try:
                response = await self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are an expert React developer. Return ONLY clean JavaScript code with no explanations or markdown."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=2000
                )
                
                # Clean the response to remove any markdown or explanations
                code = response.choices[0].message.content.strip()
                
                # Remove markdown code blocks if present
                if code.startswith('```'):
                    lines = code.split('\n')
                    start_idx = 0
                    for i, line in enumerate(lines):
                        if not line.strip().startswith('```') and not line.strip() in ['jsx', 'javascript', 'js']:
                            start_idx = i
                            break
                    
                    end_idx = len(lines)
                    for i in range(len(lines) - 1, -1, -1):
                        if not lines[i].strip().startswith('```'):
                            end_idx = i + 1
                            break
                    
                    code = '\n'.join(lines[start_idx:end_idx])
                
                # Remove any explanatory text before import statements
                lines = code.split('\n')
                code_start = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('import ') or line.strip().startswith('const ') or line.strip().startswith('function '):
                        code_start = i
                        break
                
                code = '\n'.join(lines[code_start:])
                return code.strip()
                
            except Exception as e:
                logger.error(f"LLM component generation failed: {e}")
                return self._generate_component_template(component_name, state['issue_description'])
    
    def _generate_component_template(self, component_name: str, description: str) -> str:
        """Generate component using templates (previous implementation)"""
        # Implementation from previous version
        pass
    
    async def _update_app_file(self, file_path: str, state: AgentState) -> str:
        """Update App.jsx file"""
        # Read existing App.jsx content
        existing_content = ""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
        except:
            pass
        
        if self.client:
            return await self._update_app_with_llm(file_path, state, existing_content)
        else:
            return self._generate_updated_app_template(state)
    
    async def _update_css_file(self, state: AgentState) -> str:
        """Update CSS file (previous implementation)"""
        # Implementation from previous version
        pass
      
    async def _update_app_with_llm(self, file_path: str, state: AgentState, existing_content: str) -> str:
        """Update App.jsx using LLM"""
        prompt = f"""
        Update this React App component to implement: {state['issue_summary']}
        
        Description: {state['issue_description']}
        Components available: {[c.split('/')[-1].replace('.jsx', '') for c in state['requirements'].get('components_to_create', [])]}
        
        Current App.jsx:
        {existing_content[:2000] if existing_content else "No existing content"}
        
        IMPORTANT: Return ONLY the complete JavaScript/JSX code, no explanations, no markdown formatting.
        Start directly with 'import' statements and end with 'export default App'
        
        Please:
        1. Add the new functionality while preserving existing features
        2. Import any new components needed
        3. Add necessary state management
        4. Include proper error handling
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert React developer. Return ONLY clean JavaScript code with no explanations or markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=3000
            )
            
            # Clean the response
            code = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if code.startswith('```') or '```jsx' in code or '```javascript' in code:
                lines = code.split('\n')
                clean_lines = []
                in_code_block = False
                
                for line in lines:
                    if line.strip().startswith('```'):
                        in_code_block = not in_code_block
                        continue
                    
                    if in_code_block or (not line.strip().startswith('Here') and not line.strip().startswith('This')):
                        clean_lines.append(line)
                
                code = '\n'.join(clean_lines)
            
            # Remove explanatory text
            lines = code.split('\n')
            code_start = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('import ') or line.strip().startswith('const ') or line.strip().startswith('function '):
                    code_start = i
                    break
            
            code = '\n'.join(lines[code_start:])
            return code.strip()
            
        except Exception as e:
            logger.error(f"LLM App update failed: {e}")
            return self._generate_updated_app_template(state)
    
    async def _update_css_file(self, state: AgentState) -> str:
        """Update CSS file"""
        if self.client:
            return await self._update_css_with_llm(state)
        else:
            return self._generate_updated_styles_template(state)

    async def _update_css_with_llm(self, state: AgentState) -> str:
        """Update CSS using LLM"""
        prompt = f"""
        Generate CSS styles for a React todo application with this new feature: {state['issue_summary']}
        
        Description: {state['issue_description']}
        New Components: {[c.split('/')[-1].replace('.jsx', '') for c in state['requirements'].get('components_to_create', [])]}
        
        IMPORTANT: Return ONLY the CSS code, no explanations, no markdown formatting, no code blocks.
        Start directly with CSS selectors and rules.
        
        Create modern, responsive CSS that includes:
        1. Base styles for the todo application
        2. Styles for the new functionality
        3. Responsive design
        4. Accessibility improvements
        5. Modern visual design
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert CSS developer. Return ONLY clean CSS code with no explanations or markdown."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            # Clean the response
            code = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if code.startswith('```') or '```css' in code:
                lines = code.split('\n')
                clean_lines = []
                in_code_block = False
                
                for line in lines:
                    if line.strip().startswith('```'):
                        in_code_block = not in_code_block
                        continue
                    
                    if in_code_block or (not line.strip().startswith('This') and not line.strip().startswith('Here')):
                        clean_lines.append(line)
                
                code = '\n'.join(clean_lines)
            
            # Remove explanatory text
            lines = code.split('\n')
            code_start = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('.') or line.strip().startswith('*') or line.strip().startswith('body') or line.strip().startswith('@'):
                    code_start = i
                    break
            
            code = '\n'.join(lines[code_start:])
            return code.strip()
            
        except Exception as e:
            logger.error(f"LLM CSS update failed: {e}")
            return self._generate_updated_styles_template(state)
    
    def _generate_component_template(self, component_name: str, description: str):
        """Fallback template generation"""
        if "search" in component_name.lower() or "advanced" in component_name.lower():
            return '''import React, { useState } from 'react';

const AdvancedSearch = ({ onSearch, onFilterChange }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    category: 'all',
    priority: 'all',
    status: 'all'
  });

  const handleSearchChange = (value) => {
    setSearchTerm(value);
    onSearch(value, filters);
  };

  const handleFilterChange = (filterType, value) => {
    const newFilters = { ...filters, [filterType]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  return (
    <div className="advanced-search">
      <div className="search-input-container">
        <input
          type="text"
          placeholder="Search todos..."
          value={searchTerm}
          onChange={(e) => handleSearchChange(e.target.value)}
          className="search-input"
        />
      </div>
      <div className="filters">
        <select
          value={filters.category}
          onChange={(e) => handleFilterChange('category', e.target.value)}
          className="filter-select"
        >
          <option value="all">All Categories</option>
          <option value="work">Work</option>
          <option value="personal">Personal</option>
          <option value="shopping">Shopping</option>
        </select>
        <select
          value={filters.priority}
          onChange={(e) => handleFilterChange('priority', e.target.value)}
          className="filter-select"
        >
          <option value="all">All Priorities</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>
    </div>
  );
};

export default AdvancedSearch;'''
        
        elif "category" in component_name.lower():
            return '''import React from 'react';

const CategoryFilter = ({ selectedCategory, onCategoryChange }) => {
  const categories = ['all', 'work', 'personal', 'shopping', 'health'];
  
  return (
    <div className="category-filter">
      <label htmlFor="category-select">Filter by Category:</label>
      <select 
        id="category-select"
        value={selectedCategory}
        onChange={(e) => onCategoryChange(e.target.value)}
        className="category-select"
      >
        {categories.map(category => (
          <option key={category} value={category}>
            {category.charAt(0).toUpperCase() + category.slice(1)}
          </option>
        ))}
      </select>
    </div>
  );
};

export default CategoryFilter;'''
        
        else:
            return f'''import React from 'react';

const {component_name} = () => {{
  return (
    <div className="{component_name.lower().replace('_', '-')}">
      <h3>{component_name}</h3>
      <p>Generated component for: {description[:100]}...</p>
    </div>
  );
}};

export default {component_name};'''
    
    def _generate_updated_app_template(self, state: AgentState) -> str:
        """Generate updated App.jsx using templates"""
        description = state['issue_description'].lower()
        requirements = state['requirements']
        
        # Determine what components to include
        components_to_import = []
        component_usage = []
        state_additions = []
        
        for component_path in requirements.get('components_to_create', []):
            component_name = component_path.split('/')[-1].replace('.jsx', '')
            components_to_import.append(f"import {component_name} from './components/{component_name}'")
            
            if 'search' in component_name.lower() or 'advanced' in component_name.lower():
                state_additions.append("  const [searchFilters, setSearchFilters] = useState({ category: 'all', priority: 'all' })")
                component_usage.append('''        <div className="search-section">
          <AdvancedSearch 
            onSearch={(term, filters) => console.log('Search:', term, filters)}
            onFilterChange={setSearchFilters}
          />
        </div>''')
        
        import_statements = '\n'.join(components_to_import)
        additional_state = '\n'.join(state_additions)
        component_sections = '\n'.join(component_usage)
        
        return f'''import {{ useState, useEffect }} from 'react'
{import_statements}
import './App.css'

function App() {{
  const [todos, setTodos] = useState([])
  const [loading, setLoading] = useState(true)
  const [newTodo, setNewTodo] = useState('')
{additional_state}

  useEffect(() => {{
    fetchTodos()
  }}, [])

  const fetchTodos = async () => {{
    try {{
      const response = await fetch('http://localhost:3001/api/todos')
      const data = await response.json()
      setTodos(data)
    }} catch (error) {{
      console.error('Failed to fetch todos:', error)
    }} finally {{
      setLoading(false)
    }}
  }}

  const addTodo = async () => {{
    if (!newTodo.trim()) return
    
    try {{
      const response = await fetch('http://localhost:3001/api/todos', {{
        method: 'POST',
        headers: {{
          'Content-Type': 'application/json',
        }},
        body: JSON.stringify({{ title: newTodo, priority: 'medium' }}),
      }})
      
      if (response.ok) {{
        const todo = await response.json()
        setTodos([todo, ...todos])
        setNewTodo('')
      }}
    }} catch (error) {{
      console.error('Failed to add todo:', error)
    }}
  }}

  const toggleTodo = async (id, completed) => {{
    try {{
      const response = await fetch(`http://localhost:3001/api/todos/${{id}}`, {{
        method: 'PUT',
        headers: {{
          'Content-Type': 'application/json',
        }},
        body: JSON.stringify({{ completed }}),
      }})
      
      if (response.ok) {{
        const updatedTodo = await response.json()
        setTodos(todos.map(todo => 
          todo.id === id ? updatedTodo : todo
        ))
      }}
    }} catch (error) {{
      console.error('Failed to update todo:', error)
    }}
  }}

  if (loading) {{
    return <div className="loading">Loading todos...</div>
  }}

  return (
    <div className="app">
      <header className="header">
        <h1>Todo App</h1>
        <p>Enhanced with automation</p>
      </header>
      
      <main className="main-content">
        <div className="add-todo">
          <input
            type="text"
            value={{newTodo}}
            onChange={{(e) => setNewTodo(e.target.value)}}
            placeholder="What needs to be done?"
            onKeyPress={{(e) => e.key === 'Enter' && addTodo()}}
          />
          <button onClick={{addTodo}}>Add Todo</button>
        </div>
{component_sections}
        
        <div className="todos">
          {{todos.map(todo => (
            <div key={{todo.id}} className={{`todo-item ${{todo.completed ? 'completed' : ''}} priority-${{todo.priority}}`}}>
              <input
                type="checkbox"
                checked={{todo.completed}}
                onChange={{(e) => toggleTodo(todo.id, e.target.checked)}}
              />
              <div className="todo-content">
                <span className="todo-title">{{todo.title}}</span>
                <div className="todo-meta">
                  <span className="priority">{{todo.priority}}</span>
                  <span className="date">{{new Date(todo.created_at).toLocaleDateString()}}</span>
                </div>
              </div>
            </div>
          ))}}
        </div>
        
        {{todos.length === 0 && (
          <div className="empty-state">
            <p>No todos yet. Add one above!</p>
          </div>
        )}}
      </main>
    </div>
  )
}}

export default App'''
    
    def _generate_updated_styles_template(self, state: AgentState) -> str:
        """Generate updated CSS using templates"""
        return '''* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  color: #333;
}

.app {
  min-height: 100vh;
  padding: 20px;
}

.header {
  text-align: center;
  color: white;
  margin-bottom: 30px;
}

.header h1 {
  font-size: 2.5rem;
  margin-bottom: 10px;
  text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.main-content {
  max-width: 800px;
  margin: 0 auto;
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.2);
}

.add-todo {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.add-todo input {
  flex: 1;
  padding: 12px;
  border: 2px solid #e9ecef;
  border-radius: 6px;
  font-size: 16px;
}

.add-todo button {
  padding: 12px 24px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}

.search-section, .advanced-search {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.search-input {
  width: 100%;
  padding: 12px;
  border: 2px solid #e9ecef;
  border-radius: 6px;
  font-size: 16px;
  margin-bottom: 10px;
}

.filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-select, .category-select {
  padding: 8px 12px;
  border: 2px solid #e9ecef;
  border-radius: 6px;
  font-size: 14px;
  background: white;
}

.todos {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.todo-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  background: white;
}

.todo-item.priority-high {
  border-left: 6px solid #dc3545;
}

.todo-item.priority-medium {
  border-left: 6px solid #ffc107;
}

.todo-item.priority-low {
  border-left: 6px solid #28a745;
}

.todo-content {
  flex: 1;
}

.todo-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.todo-meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
}

.priority, .date {
  padding: 2px 6px;
  border-radius: 10px;
  background: #e2e8f0;
  color: #4a5568;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #718096;
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  font-size: 18px;
  color: white;
}'''




class ProductionGitIntegrator:
    """Production Git integration with GitHub sync"""
    
    def __init__(self):
        self.github_client = GitHubClient()
        self.jira_client = JiraClient()
    
    async def __call__(self, state: AgentState) -> AgentState:
        logger.info(f"[{state['trace_id']}] Starting production Git integration")
        
        try:
            # Generate branch name
            timestamp = int(time.time())
            state['branch_name'] = f"feature/{state['issue_key'].lower()}-{timestamp}"
            
            # Update Jira: Starting development
            await self.jira_client.update_issue_status(
                state['issue_key'],
                "In Progress",
                f"🤖 Automation started\\n\\nBranch: `{state['branch_name']}`\\nTrace ID: `{state['trace_id']}`"
            )
            
            # Create GitHub branch first
            await self.github_client.create_branch(state['branch_name'])
            
            # Create and checkout local branch
            await GitOperations.create_and_checkout_branch(state['branch_name'])
            
            # Write generated files
            file_changes = []
            generated_files = state.get('generated_code', {})
            
            for file_path, content in generated_files.items():
                try:
                    file_change = FileManager.write_file(file_path, content, state['trace_id'])
                    file_changes.append(file_change)
                except Exception as e:
                    logger.error(f"Failed to write {file_path}: {e}")
                    state['errors'].append(f"File write error: {str(e)}")
            
            state['file_changes'] = file_changes
            
            if file_changes:
                # Commit changes
                commit_message = f"{state['issue_key']}: {state['issue_summary']}\n\nAutomated implementation:\n"
                commit_message += "\n".join([f"- {req}" for req in state['requirements'].get('functional', [])])
                commit_message += f"\n\nGenerated by DevOps Automation\nTrace ID: {state['trace_id']}"
                
                success, commit_hash = await GitOperations.commit_changes(
                    commit_message,
                    config.jira_username
                )
                
                if success:
                    state['commit_hash'] = commit_hash
                    
                    # Push to GitHub
                    if await GitOperations.push_branch(state['branch_name']):
                        # Create pull request
                        pr_title = f"{state['issue_key']}: {state['issue_summary']}"
                        pr_description = self._generate_pr_description(state)
                        
                        pr_url = await self.github_client.create_pull_request(
                            state['branch_name'],
                            pr_title,
                            pr_description
                        )
                        
                        if pr_url:
                            state['pr_url'] = pr_url
                            
                            # Update Jira with PR link
                            jira_comment = f"🚀 Pull Request Created\\n\\n"
                            jira_comment += f"[View Pull Request|{pr_url}]\\n\\n"
                            jira_comment += f"**Files Modified:**\\n"
                            for change in file_changes:
                                jira_comment += f"• {change.file} ({change.action})\\n"
                            jira_comment += f"\\n**Commit:** `{commit_hash[:8]}`"
                            
                            await self.jira_client.update_issue_status(
                                state['issue_key'],
                                "Code Review",
                                jira_comment
                            )
                
            logger.info(f"[{state['trace_id']}] Git integration completed")
            
        except Exception as e:
            logger.error(f"Git integration failed: {e}")
            state['errors'].append(f"Git integration error: {str(e)}")
            
            # Update Jira about failure
            await self.jira_client.add_comment(
                state['issue_key'],
                f"❌ Automation failed\\n\\nError: {str(e)}\\nTrace ID: `{state['trace_id']}`"
            )
        
        return state
    
    def _generate_pr_description(self, state: AgentState) -> str:
        """Generate detailed PR description"""
        description = f"## {state['issue_key']}: {state['issue_summary']}\n\n"
        description += f"**Issue Type:** {state['issue_type']}\n\n"
        description += f"### Description\n{state['issue_description']}\n\n"
        
        requirements = state['requirements']
        if requirements.get('functional'):
            description += "### Implemented Features\n"
            for req in requirements['functional']:
                description += f"- {req}\n"
            description += "\n"
        
        if state['file_changes']:
            description += "### Files Changed\n"
            for change in state['file_changes']:
                description += f"- `{change.file}` ({change.action}, {change.lines_added} lines)\n"
            description += "\n"
        
        ai_powered = requirements.get('ai_analysis', False)
        description += f"### Generation Method\n"
        description += f"{'🧠 AI-powered analysis' if ai_powered else '📋 Template-based generation'}\n\n"
        
        description += f"### Automation Details\n"
        description += f"- **Trace ID:** `{state['trace_id']}`\n"
        description += f"- **Generated:** {datetime.now().isoformat()}\n"
        description += f"- **Commit:** `{state.get('commit_hash', 'N/A')}`\n\n"
        
        description += "### Testing Checklist\n"
        description += "- [ ] Feature works as expected\n"
        description += "- [ ] No existing functionality broken\n"
        description += "- [ ] UI/UX is consistent\n"
        description += "- [ ] No console errors\n"
        description += "- [ ] Mobile responsive (if applicable)\n\n"
        
        description += "*This pull request was automatically generated by the DevOps Automation System*"
        
        return description

# Main processing function
async def process_jira_webhook(webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Production webhook processing with full Jira and GitHub integration
    """
    
    trace_id = generate_trace_id()
    initial_state = AgentState(
        trace_id=trace_id,
        webhook_payload=webhook_payload,
        issue_key="",
        issue_summary="",
        issue_type="",
        issue_description="",
        requirements={},
        generated_code={},
        file_changes=[],
        branch_name="",
        commit_hash="",
        pr_url="",
        jira_updates=[],
        errors=[]
    )
    
    logger.info(f"[{trace_id}] Starting production automation pipeline")
    logger.info(f"[{trace_id}] LLM Available: {LLM_AVAILABLE and bool(config.openai_api_key)}")
    logger.info(f"[{trace_id}] Jira Integration: {bool(config.jira_api_token)}")
    logger.info(f"[{trace_id}] GitHub Integration: {bool(config.github_token)}")
    
    try:
        # Extract issue information
        issue_data = webhook_payload.get('issue', {})
        initial_state['issue_key'] = issue_data.get('key', '')
        initial_state['issue_summary'] = issue_data.get('fields', {}).get('summary', '')
        initial_state['issue_type'] = issue_data.get('fields', {}).get('issuetype', {}).get('name', '')
        initial_state['issue_description'] = issue_data.get('fields', {}).get('description', '')
        
        logger.info(f"[{trace_id}] Processing: {initial_state['issue_key']} - {initial_state['issue_summary']}")
        
        # Execute production pipeline
        agents = [
            ("Requirements Analysis", RequirementsAnalyst()),
            ("Code Generation", CodeGenerator()),
            ("Git & GitHub Integration", ProductionGitIntegrator())
        ]
        
        state = initial_state
        for agent_name, agent in agents:
            try:
                logger.info(f"[{trace_id}] Executing: {agent_name}")
                state = await agent(state)
            except Exception as e:
                error_msg = f"{agent_name} failed: {str(e)}"
                logger.error(f"[{trace_id}] {error_msg}")
                state['errors'].append(error_msg)
                continue
        
        # Calculate final metrics
        files_generated = len(state.get('generated_code', {}))
        files_written = len(state.get('file_changes', []))
        errors_count = len(state.get('errors', []))
        success_rate = max(0, 100 - (errors_count * 20))
        
        status = "SUCCESS" if errors_count == 0 else ("PARTIAL_SUCCESS" if files_written > 0 else "FAILED")
        
        logger.info(f"[{trace_id}] Pipeline completed!")
        logger.info(f"[{trace_id}] Status: {status}")
        logger.info(f"[{trace_id}] Files generated: {files_generated}")
        logger.info(f"[{trace_id}] Files written: {files_written}")
        logger.info(f"[{trace_id}] Success rate: {success_rate}%")
        
        return {
            'trace_id': trace_id,
            'issue_key': state['issue_key'],
            'issue_summary': state['issue_summary'],
            'status': status,
            'files_generated': files_generated,
            'files_written': files_written,
            'success_rate': success_rate,
            'branch_name': state.get('branch_name', ''),
            'commit_hash': state.get('commit_hash', ''),
            'pr_url': state.get('pr_url', ''),
            'ai_analysis': state.get('requirements', {}).get('ai_analysis', False),
            'errors': state['errors'],
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[{trace_id}] Pipeline failed: {e}")
        
        # Update Jira about complete failure
        jira_client = JiraClient()
        await jira_client.add_comment(
            initial_state.get('issue_key', 'UNKNOWN'),
            f"❌ Automation Pipeline Failed\\n\\nError: {str(e)}\\nTrace ID: `{trace_id}`"
        )
        
        return {
            'trace_id': trace_id,
            'issue_key': initial_state.get('issue_key', 'UNKNOWN'),
            'status': 'FAILED',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

# Configuration validation
def validate_production_config() -> Dict[str, bool]:
    """Validate production configuration"""
    checks = {
        'openai_api_key': bool(config.openai_api_key),
        'jira_url': bool(config.jira_url),
        'jira_username': bool(config.jira_username), 
        'jira_api_token': bool(config.jira_api_token),
        'github_token': bool(config.github_token),
        'github_repo': bool(config.github_repo),
        'project_paths': all([
            os.path.exists(config.project_root),
            os.path.exists(config.frontend_path)
        ])
    }
    
    return checks

# Example usage and testing
if __name__ == "__main__":
    async def test_production_automation():
        print("Testing production automation with full integration...")
        
        # Validate configuration
        config_status = validate_production_config()
        print("Configuration Status:")
        for key, status in config_status.items():
            print(f"  {key}: {'✅' if status else '❌'}")
        
        print(f"\nLLM Available: {LLM_AVAILABLE}")
        print(f"Jira Integration: {bool(config.jira_api_token)}")
        print(f"GitHub Integration: {bool(config.github_token)}")
        
        # Test webhook
        test_webhook = {
            "issue": {
                "key": "PROD-TEST-001",
                "fields": {
                    "summary": "Add advanced search with filters",
                    "issuetype": {"name": "Story"},
                    "description": "Implement search functionality with category filters, priority sorting, and date range selection for better todo management"
                }
            }
        }
        
        result = await process_jira_webhook(test_webhook)
        print(f"\nTest completed:")
        print(f"  Trace ID: {result['trace_id']}")
        print(f"  Status: {result['status']}")
        print(f"  Files generated: {result.get('files_generated', 0)}")
        print(f"  Branch: {result.get('branch_name', 'N/A')}")
        print(f"  PR URL: {result.get('pr_url', 'N/A')}")
        print(f"  Commit: {result.get('commit_hash', 'N/A')[:8] if result.get('commit_hash') else 'N/A'}")
        
        if result['status'] == 'SUCCESS':
            print("\n🎉 Production automation completed successfully!")
            print("Check Jira for status updates and GitHub for the new pull request.")
        else:
            print(f"\n⚠️ Automation completed with issues: {result.get('errors', [])}")
    
    asyncio.run(test_production_automation())