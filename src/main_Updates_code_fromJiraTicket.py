"""
Full LLM-Powered DevOps Automation System
This version actually generates and writes code files to modify your todo app
"""

import asyncio
import json
import logging
import os
import shutil
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

# LLM Integration
try:
    import openai
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
@dataclass
class Config:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    project_root: str = os.getenv("PROJECT_ROOT", "..")
    frontend_path: str = os.getenv("FRONTEND_PATH", "../todo-app/frontend")
    backend_path: str = os.getenv("BACKEND_PATH", "../todo-app/backend")

config = Config()

@dataclass
class FileChange:
    file: str
    action: str
    lines_added: int = 0
    backup_path: Optional[str] = None

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
    errors: List[str]

def generate_trace_id() -> str:
    return str(uuid.uuid4())

class FileManager:
    @staticmethod
    def create_backup(file_path: str, trace_id: str) -> str:
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

class RequirementsAnalyst:
    def __init__(self):
        if LLM_AVAILABLE and config.openai_api_key:
            self.client = openai.AsyncOpenAI(api_key=config.openai_api_key)
        else:
            self.client = None
    
    async def __call__(self, state: AgentState) -> AgentState:
        logger.info(f"[{state['trace_id']}] Analyzing requirements with AI")
        
        try:
            if self.client:
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
                
                state['requirements'] = {
                    "functional": llm_analysis.get("functional_requirements", []),
                    "technical": llm_analysis.get("technical_requirements", []),
                    "priority": llm_analysis.get("priority", "medium"),
                    "files_to_modify": [f"{config.frontend_path}/{f}" for f in llm_analysis.get("files_to_modify", [])],
                    "components_to_create": [f"{config.frontend_path}/src/components/{c}" for c in llm_analysis.get("components_to_create", [])],
                    "ai_analysis": True
                }
                
                logger.info(f"[{state['trace_id']}] AI identified {len(llm_analysis.get('components_to_create', []))} components")
            else:
                # Fallback analysis
                state['requirements'] = self._fallback_analysis(state)
                
        except Exception as e:
            logger.error(f"[{state['trace_id']}] AI analysis failed: {e}")
            state['requirements'] = self._fallback_analysis(state)
            state['errors'].append(f"AI analysis error: {str(e)}")
        
        return state
    
    def _fallback_analysis(self, state: AgentState):
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
        
        if "priority" in description or "color" in description:
            requirements["functional"].append("Add priority indicators")
            requirements["files_to_modify"].extend([
                f"{config.frontend_path}/src/App.jsx",
                f"{config.frontend_path}/src/App.css"
            ])
        
        if "due date" in description or "deadline" in description:
            requirements["functional"].append("Add due date functionality")
            requirements["files_to_modify"].extend([
                f"{config.frontend_path}/src/App.jsx",
                f"{config.frontend_path}/src/App.css"
            ])
            requirements["components_to_create"].append(f"{config.frontend_path}/src/components/DatePicker.jsx")
        
        return requirements

class CodeGenerator:
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
            
            # Generate components
            for component_path in requirements.get('components_to_create', []):
                component_name = component_path.split('/')[-1].replace('.jsx', '')
                
                if self.client:
                    code = await self._generate_component_with_llm(
                        component_name, 
                        state['issue_summary'],
                        state['issue_description']
                    )
                else:
                    code = self._generate_component_template(component_name, state['issue_description'])
                
                generated_code[component_path] = code
            
            # Update existing files
            for file_path in requirements.get('files_to_modify', []):
                if "App.jsx" in file_path:
                    if self.client:
                        updated_code = await self._update_app_with_llm(file_path, state)
                    else:
                        updated_code = self._generate_updated_app(state['issue_description'])
                    generated_code[file_path] = updated_code
                elif "App.css" in file_path:
                    if self.client:
                        updated_css = await self._update_css_with_llm(state)
                    else:
                        updated_css = self._generate_updated_styles(state['issue_description'])
                    generated_code[file_path] = updated_css
            
            state['generated_code'] = generated_code
            logger.info(f"[{state['trace_id']}] Generated {len(generated_code)} files")
            
        except Exception as e:
            logger.error(f"[{state['trace_id']}] Code generation failed: {e}")
            state['errors'].append(f"Code generation error: {str(e)}")
        
        return state
    
    async def _generate_component_with_llm(self, component_name: str, summary: str, description: str) -> str:
        prompt = f"""
        Generate a React functional component for: {component_name}
        
        Context:
        - Feature: {summary}
        - Description: {description}
        
        IMPORTANT: Return ONLY the JavaScript/JSX code, no explanations, no markdown formatting, no code blocks.
        Start directly with 'import' and end with 'export default ComponentName;'
        
        Create a production-ready React component that:
        1. Uses modern React hooks
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
                # Find first line that doesn't start with ``` or contain language name
                start_idx = 0
                for i, line in enumerate(lines):
                    if not line.strip().startswith('```') and not line.strip() in ['jsx', 'javascript', 'js']:
                        start_idx = i
                        break
                
                # Find last line that doesn't start with ```
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
            return self._generate_component_template(component_name, description)
    
    async def _update_app_with_llm(self, file_path: str, state: AgentState) -> str:
        # Read existing App.jsx
        existing_content = ""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
        except:
            pass
        
        prompt = f"""
        Update this React App component to implement: {state['issue_summary']}
        
        Description: {state['issue_description']}
        
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
                    {"role": "system", "content": "You are an expert React developer. Return ONLY clean JavaScript code with no explanations or markdown. Do not include 'Here is the updated code:' or similar phrases."},
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
            return self._generate_updated_app(state['issue_description'])
    
    async def _update_css_with_llm(self, state: AgentState) -> str:
        prompt = f"""
        Generate CSS styles for a React todo application with this new feature: {state['issue_summary']}
        
        Description: {state['issue_description']}
        
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
            return self._generate_updated_styles(state['issue_description'])
    
    def _generate_component_template(self, component_name: str, description: str):
        if "search" in component_name.lower():
            return '''import React from 'react';

const SearchBar = ({ searchTerm, onSearchChange, placeholder = "Search todos..." }) => {
  return (
    <div className="search-bar">
      <input
        type="text"
        placeholder={placeholder}
        value={searchTerm}
        onChange={(e) => onSearchChange(e.target.value)}
        className="search-input"
      />
      {searchTerm && (
        <button 
          onClick={() => onSearchChange('')}
          className="search-clear"
          title="Clear search"
        >
          ✕
        </button>
      )}
    </div>
  );
};

export default SearchBar;'''
        
        elif "category" in component_name.lower():
            return '''import React from 'react';

const CategorySelect = ({ category, onCategoryChange }) => {
  const categories = ['All', 'Work', 'Personal', 'Shopping', 'Health', 'Other'];
  
  return (
    <div className="category-select">
      <label htmlFor="category">Category:</label>
      <select 
        id="category"
        value={category}
        onChange={(e) => onCategoryChange(e.target.value)}
        className="category-dropdown"
      >
        {categories.map(cat => (
          <option key={cat} value={cat}>{cat}</option>
        ))}
      </select>
    </div>
  );
};

export default CategorySelect;'''
        
        else:
            return f'''import React from 'react';

const {component_name} = () => {{
  return (
    <div className="{component_name.lower()}">
      <h3>{component_name}</h3>
      <p>New feature: {description[:100]}...</p>
    </div>
  );
}};

export default {component_name};'''
    
    def _generate_updated_app(self, description: str) -> str:
        include_search = "search" in description.lower() or "filter" in description.lower()
        include_category = "category" in description.lower() or "tag" in description.lower()
        
        imports = []
        if include_search:
            imports.append("import SearchBar from './components/SearchBar'")
        if include_category:
            imports.append("import CategorySelect from './components/CategorySelect'")
        
        import_statements = '\n'.join(imports)
        
        search_state = ""
        category_state = ""
        if include_search:
            search_state = "  const [searchTerm, setSearchTerm] = useState('')"
        if include_category:
            category_state = "  const [selectedCategory, setSelectedCategory] = useState('All')"
        
        filter_logic = "const filteredTodos = todos"
        if include_search and include_category:
            filter_logic = '''const filteredTodos = todos.filter(todo => {
    const matchesSearch = todo.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (todo.description && todo.description.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesCategory = selectedCategory === 'All' || todo.category === selectedCategory;
    return matchesSearch && matchesCategory;
  })'''
        elif include_search:
            filter_logic = '''const filteredTodos = todos.filter(todo => 
    todo.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (todo.description && todo.description.toLowerCase().includes(searchTerm.toLowerCase()))
  )'''
        elif include_category:
            filter_logic = '''const filteredTodos = todos.filter(todo => 
    selectedCategory === 'All' || todo.category === selectedCategory
  )'''
        
        search_section = ""
        if include_search:
            search_section = '''
        <div className="search-section">
          <SearchBar 
            searchTerm={searchTerm}
            onSearchChange={setSearchTerm}
          />
        </div>'''
        
        category_section = ""
        if include_category:
            category_section = '''
        <div className="category-section">
          <CategorySelect 
            category={selectedCategory}
            onCategoryChange={setSelectedCategory}
          />
        </div>'''
        
        return f'''import {{ useState, useEffect }} from 'react'
{import_statements}
import './App.css'

function App() {{
  const [todos, setTodos] = useState([])
  const [loading, setLoading] = useState(true)
  const [newTodo, setNewTodo] = useState('')
{search_state}
{category_state}

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
        body: JSON.stringify({{ 
          title: newTodo, 
          priority: 'medium',
          category: selectedCategory !== 'All' ? selectedCategory : 'Personal'
        }}),
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

  {filter_logic}

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
{search_section}
{category_section}
        
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
                  {{todo.category && <span className="category">{{todo.category}}</span>}}
                  <span className="date">{{new Date(todo.created_at).toLocaleDateString()}}</span>
                </div>
              </div>
            </div>
          ))}}
        </div>
        
        {{filteredTodos.length === 0 && todos.length > 0 && (
          <div className="empty-state">
            <p>No todos match your filters</p>
          </div>
        )}}
        
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
    
    def _generate_updated_styles(self, description: str) -> str:
        base_styles = '''* {
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

.search-section, .category-section {
  margin-bottom: 20px;
}

.search-bar {
  position: relative;
  display: flex;
  align-items: center;
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
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  font-size: 16px;
  padding: 4px;
  border-radius: 50%;
}

.category-select {
  display: flex;
  align-items: center;
  gap: 10px;
}

.category-dropdown {
  padding: 8px 12px;
  border: 2px solid #e9ecef;
  border-radius: 6px;
  font-size: 14px;
}

.filter-info {
  text-align: center;
  margin-bottom: 20px;
  color: #666;
  font-size: 14px;
}

.todos {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.todo-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  background: white;
  transition: all 0.2s;
}

.todo-item:hover {
  border-color: #dee2e6;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.todo-item.completed {
  opacity: 0.7;
  background: #f8f9fa;
}

.todo-item.priority-high {
  border-left: 6px solid #dc3545;
  background: linear-gradient(90deg, #fff5f5 0%, #ffffff 10%);
}

.todo-item.priority-medium {
  border-left: 6px solid #ffc107;
  background: linear-gradient(90deg, #fffdf0 0%, #ffffff 10%);
}

.todo-item.priority-low {
  border-left: 6px solid #28a745;
  background: linear-gradient(90deg, #f0fff4 0%, #ffffff 10%);
}

.todo-content {
  flex: 1;
}

.todo-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
  display: block;
  color: #2d3748;
}

.todo-item.completed .todo-title {
  text-decoration: line-through;
  color: #718096;
}

.todo-description {
  font-size: 14px;
  color: #4a5568;
  margin-bottom: 8px;
  display: block;
}

.todo-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 12px;
}

.priority, .category, .date {
  padding: 2px 6px;
  border-radius: 10px;
  background: #e2e8f0;
  color: #4a5568;
}

.category {
  background: #bee3f8;
  color: #2b6cb0;
}

.priority {
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
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
}

@media (max-width: 768px) {
  .app {
    padding: 10px;
  }
  
  .main-content {
    padding: 20px;
  }
  
  .add-todo {
    flex-direction: column;
  }
  
  .todo-meta {
    gap: 4px;
  }
}'''
        
        return base_styles

class FileWriter:
    async def __call__(self, state: AgentState) -> AgentState:
        logger.info(f"[{state['trace_id']}] Writing generated files")
        
        try:
            file_changes = []
            generated_files = state.get('generated_code', {})
            
            if not generated_files:
                logger.warning(f"[{state['trace_id']}] No files to write")
                return state
            
            logger.info(f"[{state['trace_id']}] Writing {len(generated_files)} files")
            
            for file_path, content in generated_files.items():
                try:
                    file_change = FileManager.write_file(file_path, content, state['trace_id'])
                    file_changes.append(file_change)
                    
                except Exception as e:
                    logger.error(f"[{state['trace_id']}] Failed to write {file_path}: {e}")
                    state['errors'].append(f"File write error for {file_path}: {str(e)}")
            
            state['file_changes'] = file_changes
            
            logger.info(f"[{state['trace_id']}] Successfully wrote {len(file_changes)} files")
            
        except Exception as e:
            logger.error(f"[{state['trace_id']}] File writing failed: {e}")
            state['errors'].append(f"File writing error: {str(e)}")
        
        return state

async def process_jira_webhook(webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function to process Jira webhook with full automation pipeline
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
        errors=[]
    )
    
    logger.info(f"[{trace_id}] Starting full automation pipeline")
    logger.info(f"[{trace_id}] LLM Available: {LLM_AVAILABLE and bool(config.openai_api_key)}")
    
    try:
        # Extract issue information
        issue_data = webhook_payload.get('issue', {})
        initial_state['issue_key'] = issue_data.get('key', '')
        initial_state['issue_summary'] = issue_data.get('fields', {}).get('summary', '')
        initial_state['issue_type'] = issue_data.get('fields', {}).get('issuetype', {}).get('name', '')
        initial_state['issue_description'] = issue_data.get('fields', {}).get('description', '')
        
        logger.info(f"[{trace_id}] Processing issue: {initial_state['issue_key']} - {initial_state['issue_summary']}")
        
        # Execute automation pipeline
        agents = [
            ("Requirements Analysis", RequirementsAnalyst()),
            ("Code Generation", CodeGenerator()),
            ("File Writing", FileWriter())
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
        
        # Calculate success metrics
        files_generated = len(state.get('generated_code', {}))
        files_written = len(state.get('file_changes', []))
        errors_count = len(state.get('errors', []))
        success_rate = max(0, 100 - (errors_count * 20))  # Rough calculation
        
        ai_powered = state.get('requirements', {}).get('ai_analysis', False)
        
        logger.info(f"[{trace_id}] Automation completed!")
        logger.info(f"[{trace_id}] Files generated: {files_generated}")
        logger.info(f"[{trace_id}] Files written: {files_written}")
        logger.info(f"[{trace_id}] AI Analysis: {'Enabled' if ai_powered else 'Template-based'}")
        logger.info(f"[{trace_id}] Success rate: {success_rate}%")
        
        return {
            'trace_id': trace_id,
            'issue_key': state['issue_key'],
            'issue_summary': state['issue_summary'],
            'status': 'SUCCESS' if errors_count == 0 else 'PARTIAL_SUCCESS',
            'files_generated': files_generated,
            'files_written': files_written,
            'success_rate': success_rate,
            'ai_analysis': ai_powered,
            'errors': state['errors'],
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[{trace_id}] Pipeline failed: {e}")
        return {
            'trace_id': trace_id,
            'issue_key': initial_state.get('issue_key', 'UNKNOWN'),
            'status': 'FAILED',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

# Example usage and testing
if __name__ == "__main__":
    async def test_automation():
        print("Testing full automation pipeline...")
        print(f"LLM Available: {LLM_AVAILABLE}")
        print(f"API Key Configured: {'Yes' if config.openai_api_key else 'No'}")
        
        test_webhook = {
            "issue": {
                "key": "AUTO-TEST-001",
                "fields": {
                    "summary": "Add search functionality to todo app",
                    "issuetype": {"name": "Story"},
                    "description": "Add a search bar that allows users to filter todos by title and description. Include a clear button to reset the search."
                }
            }
        }
        
        result = await process_jira_webhook(test_webhook)
        print(f"Test completed - Trace ID: {result['trace_id']}")
        print(f"Status: {result['status']}")
        print(f"Files generated: {result.get('files_generated', 0)}")
        print(f"Files written: {result.get('files_written', 0)}")
        print(f"AI Analysis: {result.get('ai_analysis', False)}")
        print("Check your todo app for changes!")
    
    asyncio.run(test_automation())