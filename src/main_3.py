"""
Working LangGraph DevOps Autocoder - Simplified Version
Fixed for Windows compatibility and syntax issues
"""

import asyncio
import json
import logging
import os
import time
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

# Try importing optional dependencies
try:
    import openai
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create directories
Path("logs").mkdir(exist_ok=True)
Path("reports").mkdir(exist_ok=True)
Path("generated_code").mkdir(exist_ok=True)

@dataclass
class Config:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    github_token: str = os.getenv("GITHUB_TOKEN", "test-github-token")
    github_repo: str = os.getenv("GITHUB_REPO", "test/repo")

config = Config()

def generate_trace_id() -> str:
    return str(uuid.uuid4())

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for Windows compatibility"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:200]  # Limit length

def write_generated_file(filename: str, content: str, trace_id: str) -> Dict[str, Any]:
    """Write generated file to disk"""
    try:
        # Create safe path
        safe_filename = sanitize_filename(filename)
        file_path = Path("generated_code") / safe_filename
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"✅ Generated file: {file_path}")
        
        return {
            "file": str(file_path),
            "action": "created",
            "lines": len(content.split('\n')),
            "success": True
        }
    except Exception as e:
        logger.error(f"❌ Failed to write {filename}: {e}")
        return {
            "file": filename,
            "action": "failed",
            "error": str(e),
            "success": False
        }

async def analyze_requirements_with_ai(issue_summary: str, issue_description: str) -> Dict[str, Any]:
    """Analyze requirements using AI if available"""
    if not LLM_AVAILABLE or not config.openai_api_key:
        logger.info("🤖 Using fallback analysis (no AI)")
        return analyze_requirements_fallback(issue_description)
    
    try:
        client = openai.AsyncOpenAI(api_key=config.openai_api_key)
        
        prompt = f"""
        Analyze this Jira ticket and return a JSON response:
        
        Title: {issue_summary}
        Description: {issue_description}
        
        Return JSON with:
        {{
            "components_to_create": ["ComponentName.jsx"],
            "files_to_modify": ["App.jsx", "App.css"],
            "functional_requirements": ["specific functionality"],
            "priority": "high|medium|low"
        }}
        """
        
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a software architect. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=800
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info("🤖 AI analysis completed")
        return result
        
    except Exception as e:
        logger.error(f"🤖 AI analysis failed: {e}")
        return analyze_requirements_fallback(issue_description)

def analyze_requirements_fallback(description: str) -> Dict[str, Any]:
    """Fallback requirements analysis"""
    desc_lower = description.lower()
    
    requirements = {
        "components_to_create": [],
        "files_to_modify": [],
        "functional_requirements": [],
        "priority": "medium"
    }
    
    if "export" in desc_lower or "download" in desc_lower or "csv" in desc_lower:
        requirements["components_to_create"].append("ExportButton.jsx")
        requirements["files_to_modify"].extend(["App.jsx", "App.css"])
        requirements["functional_requirements"].append("Add CSV export functionality")
    
    if "search" in desc_lower or "filter" in desc_lower:
        requirements["components_to_create"].append("SearchBar.jsx")
        requirements["files_to_modify"].extend(["App.jsx", "App.css"])
        requirements["functional_requirements"].append("Add search functionality")
    
    if "notification" in desc_lower or "alert" in desc_lower:
        requirements["components_to_create"].append("NotificationSystem.jsx")
        requirements["files_to_modify"].extend(["App.jsx", "App.css"])
        requirements["functional_requirements"].append("Add notification system")
    
    # Remove duplicates
    requirements["files_to_modify"] = list(set(requirements["files_to_modify"]))
    
    return requirements

async def generate_component_with_ai(component_name: str, issue_summary: str, issue_description: str) -> str:
    """Generate React component with AI"""
    if not LLM_AVAILABLE or not config.openai_api_key:
        return generate_component_template(component_name, issue_description)
    
    try:
        client = openai.AsyncOpenAI(api_key=config.openai_api_key)
        
        prompt = f"""
        Generate a React functional component: {component_name}
        
        Context: {issue_summary}
        Description: {issue_description}
        
        Requirements:
        - Use modern React hooks
        - Include proper error handling
        - Add accessibility features
        - Follow best practices
        
        Return only the component code.
        """
        
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert React developer. Generate clean, production-ready components."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"🤖 AI component generation failed: {e}")
        return generate_component_template(component_name, issue_description)

def generate_component_template(component_name: str, description: str) -> str:
    """Generate component template"""
    name_clean = component_name.replace('.jsx', '')
    
    if "export" in name_clean.lower():
        return '''import React from 'react';

const ExportButton = ({ todos }) => {
  const exportToCSV = () => {
    if (!todos || todos.length === 0) {
      alert('No todos to export!');
      return;
    }

    const headers = ['Title', 'Description', 'Priority', 'Completed', 'Created Date'];
    const csvContent = [
      headers.join(','),
      ...todos.map(todo => [
        `"${(todo.title || '').replace(/"/g, '""')}"`,
        `"${(todo.description || '').replace(/"/g, '""')}"`,
        todo.priority || 'medium',
        todo.completed ? 'Yes' : 'No',
        new Date(todo.created_at).toLocaleDateString()
      ].join(','))
    ].join('\\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `todos-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  return (
    <button onClick={exportToCSV} className="export-btn">
      📥 Export to CSV ({todos?.length || 0} todos)
    </button>
  );
};

export default ExportButton;'''
    
    elif "search" in name_clean.lower():
        return '''import React from 'react';

const SearchBar = ({ searchTerm, onSearchChange }) => {
  return (
    <div className="search-bar">
      <input
        type="text"
        placeholder="🔍 Search todos..."
        value={searchTerm}
        onChange={(e) => onSearchChange(e.target.value)}
        className="search-input"
      />
      {searchTerm && (
        <button 
          onClick={() => onSearchChange('')}
          className="search-clear"
        >
          ✕
        </button>
      )}
    </div>
  );
};

export default SearchBar;'''
    
    else:
        return f'''import React from 'react';

const {name_clean} = () => {{
  return (
    <div className="{name_clean.lower()}">
      <h3>{name_clean}</h3>
      <p>Generated component for: {description[:50]}...</p>
    </div>
  );
}};

export default {name_clean};'''

def generate_app_jsx(requirements: Dict[str, Any]) -> str:
    """Generate App.jsx based on requirements"""
    has_export = any("export" in comp.lower() for comp in requirements.get("components_to_create", []))
    has_search = any("search" in comp.lower() for comp in requirements.get("components_to_create", []))
    
    imports = ["import { useState, useEffect } from 'react';"]
    if has_export:
        imports.append("import ExportButton from './components/ExportButton';")
    if has_search:
        imports.append("import SearchBar from './components/SearchBar';")
    imports.append("import './App.css';")
    
    state_vars = [
        "const [todos, setTodos] = useState([]);",
        "const [loading, setLoading] = useState(true);",
        "const [newTodo, setNewTodo] = useState('');"
    ]
    if has_search:
        state_vars.append("const [searchTerm, setSearchTerm] = useState('');")
    
    search_filter = """
  const filteredTodos = todos.filter(todo => 
    todo.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (todo.description && todo.description.toLowerCase().includes(searchTerm.toLowerCase()))
  );""" if has_search else "\n  const filteredTodos = todos;"
    
    search_component = """
        <div className="search-section">
          <SearchBar 
            searchTerm={searchTerm}
            onSearchChange={setSearchTerm}
          />
        </div>""" if has_search else ""
    
    export_component = """
        <div className="export-section">
          <ExportButton todos={filteredTodos} />
        </div>""" if has_export else ""
    
    return f"""{chr(10).join(imports)}

function App() {{
  {chr(10).join('  ' + var for var in state_vars)}

  useEffect(() => {{
    fetchTodos();
  }}, []);

  const fetchTodos = async () => {{
    try {{
      const response = await fetch('http://localhost:3001/api/todos');
      const data = await response.json();
      setTodos(data);
    }} catch (error) {{
      console.error('Failed to fetch todos:', error);
    }} finally {{
      setLoading(false);
    }}
  }};

  const addTodo = async () => {{
    if (!newTodo.trim()) return;
    
    try {{
      const response = await fetch('http://localhost:3001/api/todos', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ title: newTodo, priority: 'medium' }})
      }});
      
      if (response.ok) {{
        const todo = await response.json();
        setTodos([todo, ...todos]);
        setNewTodo('');
      }}
    }} catch (error) {{
      console.error('Failed to add todo:', error);
    }}
  }};

  const toggleTodo = async (id, completed) => {{
    try {{
      const response = await fetch(`http://localhost:3001/api/todos/${{id}}`, {{
        method: 'PUT',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ completed }})
      }});
      
      if (response.ok) {{
        const updatedTodo = await response.json();
        setTodos(todos.map(todo => todo.id === id ? updatedTodo : todo));
      }}
    }} catch (error) {{
      console.error('Failed to update todo:', error);
    }}
  }};

  const deleteTodo = async (id) => {{
    if (!window.confirm('Delete this todo?')) return;
    
    try {{
      const response = await fetch(`http://localhost:3001/api/todos/${{id}}`, {{
        method: 'DELETE'
      }});
      
      if (response.ok) {{
        setTodos(todos.filter(todo => todo.id !== id));
      }}
    }} catch (error) {{
      console.error('Failed to delete todo:', error);
    }}
  }};

  if (loading) return <div className="loading">Loading todos...</div>;{search_filter}

  return (
    <div className="app">
      <header className="header">
        <h1>🚀 Todo App</h1>
        <p>Powered by LangGraph DevOps Automation</p>
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
        </div>{search_component}{export_component}
        
        <div className="filter-info">
          <p>Showing: {{filteredTodos.length}} of {{todos.length}} todos</p>
        </div>
        
        <div className="todos">
          {{filteredTodos.map(todo => (
            <div key={{todo.id}} className={{`todo-item ${{todo.completed ? 'completed' : ''}} priority-${{todo.priority}}`}}>
              <input
                type="checkbox"
                checked={{todo.completed}}
                onChange={{(e) => toggleTodo(todo.id, e.target.checked)}}
              />
              <div className="todo-content">
                <span className="todo-title">{{todo.title}}</span>
                {{todo.description && <span className="todo-description">{{todo.description}}</span>}}
                <div className="todo-meta">
                  <span className="priority">{{todo.priority}}</span>
                  <span className="date">{{new Date(todo.created_at).toLocaleDateString()}}</span>
                </div>
              </div>
              <button onClick={{() => deleteTodo(todo.id)}} className="delete-btn">🗑️</button>
            </div>
          ))}}
        </div>
        
        {{filteredTodos.length === 0 && todos.length > 0 && (
          <div className="empty-state">
            <p>No todos match your search</p>
          </div>
        )}}
        
        {{todos.length === 0 && (
          <div className="empty-state">
            <p>No todos yet. Add one above!</p>
          </div>
        )}}
      </main>
    </div>
  );
}}

export default App;"""

def generate_app_css() -> str:
    """Generate App.css"""
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
}

/* Search Bar */
.search-section {
  margin-bottom: 20px;
}

.search-bar {
  position: relative;
}

.search-input {
  width: 100%;
  padding: 12px 40px 12px 12px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  font-size: 16px;
}

.search-clear {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
}

/* Export Button */
.export-section {
  margin-bottom: 20px;
  text-align: center;
}

.export-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}

.export-btn:hover {
  background: #218838;
}

.filter-info {
  text-align: center;
  margin-bottom: 20px;
  color: #666;
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

.todo-item.completed {
  opacity: 0.7;
  background: #f8f9fa;
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

.todo-item.completed .todo-title {
  text-decoration: line-through;
}

.todo-meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: #666;
}

.delete-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
}

.delete-btn:hover {
  background: #fed7d7;
  border-radius: 4px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
}

.loading {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 50vh;
  font-size: 18px;
}

@media (max-width: 768px) {
  .app { padding: 10px; }
  .main-content { padding: 20px; }
  .add-todo { flex-direction: column; }
}'''

async def create_github_branch(branch_name: str) -> bool:
    """Create GitHub branch"""
    if not REQUESTS_AVAILABLE or config.github_token == "test-github-token":
        logger.info(f"🔗 GitHub simulation: would create branch {branch_name}")
        return True
    
    try:
        headers = {
            "Authorization": f"Bearer {config.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Get main branch SHA
        url = f"https://api.github.com/repos/{config.github_repo}/git/refs/heads/main"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to get main branch: {response.text}")
            return False
        
        main_sha = response.json()["object"]["sha"]
        
        # Create branch
        url = f"https://api.github.com/repos/{config.github_repo}/git/refs"
        data = {"ref": f"refs/heads/{branch_name}", "sha": main_sha}
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 201:
            logger.info(f"✅ Created GitHub branch: {branch_name}")
            return True
        else:
            logger.error(f"Failed to create branch: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"GitHub branch creation failed: {e}")
        return False

def generate_report(issue_key: str, summary: str, file_changes: List[Dict], errors: List[str]) -> str:
    """Generate markdown report"""
    status = "✅ SUCCESS" if file_changes and not errors else "❌ FAILED"
    
    return f"""# 🤖 LangGraph DevOps Autocoder Report

## {status} Automation Summary
- **Issue**: {issue_key} - {summary}
- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Files Created**: {len(file_changes)}

## 📁 Generated Files
{chr(10).join(f'- {change["file"]} ({change["lines"]} lines)' for change in file_changes if change["success"])}

## ⚠️ Issues
{chr(10).join(f'- {error}' for error in errors) if errors else '✅ No issues encountered'}

## 🎯 Next Steps
1. Review generated files in `generated_code/` directory
2. Copy files to your React project
3. Test the new functionality
4. Deploy when ready

---
*Generated by LangGraph DevOps Autocoder*
"""

# MAIN PROCESSING FUNCTION - This is what server.py imports
async def process_jira_webhook(webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main webhook processing function
    """
    trace_id = generate_trace_id()
    
    logger.info(f"[{trace_id}] 🚀 Starting automation pipeline")
    
    try:
        # Extract issue data
        issue = webhook_payload.get('issue', {})
        issue_key = issue.get('key', 'UNKNOWN')
        issue_summary = issue.get('fields', {}).get('summary', 'No summary')
        issue_type = issue.get('fields', {}).get('issuetype', {}).get('name', 'Unknown')
        issue_description = issue.get('fields', {}).get('description', issue_summary)
        
        logger.info(f"[{trace_id}] Processing: {issue_key} - {issue_summary}")
        
        errors = []
        file_changes = []
        generated_code = {}
        
        # 1. Requirements Analysis
        logger.info(f"[{trace_id}] 📋 Analyzing requirements...")
        requirements = await analyze_requirements_with_ai(issue_summary, issue_description)
        
        # 2. Code Generation
        logger.info(f"[{trace_id}] 🔧 Generating code...")
        
        # Generate components
        for component in requirements.get('components_to_create', []):
            logger.info(f"[{trace_id}] Creating component: {component}")
            code = await generate_component_with_ai(component, issue_summary, issue_description)
            safe_path = f"components/{component}"
            generated_code[safe_path] = code
        
        # Generate App.jsx if needed
        if 'App.jsx' in requirements.get('files_to_modify', []):
            logger.info(f"[{trace_id}] Updating App.jsx...")
            app_code = generate_app_jsx(requirements)
            generated_code['App.jsx'] = app_code
        
        # Generate App.css if needed
        if 'App.css' in requirements.get('files_to_modify', []):
            logger.info(f"[{trace_id}] Updating App.css...")
            css_code = generate_app_css()
            generated_code['App.css'] = css_code
        
        # 3. Write files to disk
        logger.info(f"[{trace_id}] 💾 Writing {len(generated_code)} files...")
        for filename, content in generated_code.items():
            result = write_generated_file(filename, content, trace_id)
            file_changes.append(result)
            if not result['success']:
                errors.append(f"Failed to write {filename}")
        
        # 4. GitHub Integration
        branch_name = f"feature/{issue_key.lower()}-{int(time.time())}"
        logger.info(f"[{trace_id}] 🔗 Creating GitHub branch...")
        github_success = await create_github_branch(branch_name)
        
        # 5. Generate Report
        logger.info(f"[{trace_id}] 📊 Generating report...")
        report_content = generate_report(issue_key, issue_summary, file_changes, errors)
        report_result = write_generated_file(f"reports/{issue_key}.md", report_content, trace_id)
        
        # Calculate success metrics
        successful_files = [f for f in file_changes if f['success']]
        success_rate = (len(successful_files) / max(len(generated_code), 1)) * 100
        overall_status = "SUCCESS" if success_rate >= 75 and not errors else "FAILED"
        
        # Final result
        result = {
            "trace_id": trace_id,
            "issue_key": issue_key,
            "issue_summary": issue_summary,
            "issue_type": issue_type,
            "overall_status": overall_status,
            "success_rate": success_rate,
            "generated_code": generated_code,
            "file_changes": successful_files,
            "errors": errors,
            "requirements": requirements,
            "branch_name": branch_name if github_success else "",
            "report_generated": report_result['success'],
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"[{trace_id}] ✅ Pipeline completed!")
        logger.info(f"[{trace_id}] Status: {overall_status}")
        logger.info(f"[{trace_id}] Files generated: {len(generated_code)}")
        logger.info(f"[{trace_id}] Files written: {len(successful_files)}")
        logger.info(f"[{trace_id}] Success rate: {success_rate:.0f}%")
        
        return result
        
    except Exception as e:
        logger.error(f"[{trace_id}] ❌ Pipeline failed: {e}")
        return {
            "trace_id": trace_id,
            "overall_status": "FAILED",
            "success_rate": 0,
            "errors": [str(e)],
            "generated_code": {},
            "file_changes": [],
            "timestamp": datetime.now().isoformat()
        }

# Test function for direct execution
if __name__ == "__main__":
    async def test():
        test_payload = {
            "issue": {
                "key": "TEST-001",
                "fields": {
                    "summary": "Add CSV export functionality",
                    "issuetype": {"name": "Story"},
                    "description": "Add export button for downloading todos as CSV"
                }
            }
        }
        
        result = await process_jira_webhook(test_payload)
        print(f"✅ Test completed: {result['overall_status']}")
        print(f"📁 Files generated: {len(result['generated_code'])}")
    
    asyncio.run(test())