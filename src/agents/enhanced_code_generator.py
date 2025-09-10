import openai
import json
from typing import Dict, List
import asyncio

class EnhancedCodeGenerator:
    """AI-powered code generator that replaces your current one"""
    
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
    async def __call__(self, state):
        """Drop-in replacement for your existing CodeGenerator.__call__"""
        logger.info(f"[{state['trace_id']}] AI-powered code generation")
        
        try:
            if self.client and os.getenv("OPENAI_API_KEY"):
                # Use AI for intelligent generation
                generated_code = await self._ai_generate_code(state)
            else:
                # Fallback to your existing template-based generation
                generated_code = self._fallback_generation(state)
            
            state['generated_code'] = generated_code
            
            # Add AI analysis metadata
            state['ai_enhanced'] = bool(self.client)
            state['generation_method'] = 'ai' if self.client else 'template'
            
            logger.info(f"[{state['trace_id']}] Generated {len(generated_code)} files using {'AI' if self.client else 'templates'}")
            
        except Exception as e:
            logger.error(f"[{state['trace_id']}] Enhanced code generation failed: {e}")
            # Fallback to original method
            state = await self._fallback_generation(state)
        
        return state
    
    async def _ai_generate_code(self, state):
        """Generate code using OpenAI GPT-4"""
        
        requirements = state.get('requirements', {})
        description = state['issue_description']
        
        # Analyze what components to create
        components_prompt = f"""
        Analyze this feature request and determine what React components to create:
        
        Title: {state['issue_summary']}
        Description: {description}
        
        Return JSON with:
        {{
            "components": [
                {{"name": "ComponentName", "purpose": "what it does", "file_path": "src/components/ComponentName.jsx"}}
            ],
            "updates": [
                {{"file": "App.jsx", "changes": "what to modify"}}
            ]
        }}
        """
        
        analysis_response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a React expert. Analyze requirements and return valid JSON."},
                {"role": "user", "content": components_prompt}
            ],
            temperature=0.1
        )
        
        analysis = json.loads(analysis_response.choices[0].message.content)
        generated_files = {}
        
        # Generate each component
        for component in analysis.get('components', []):
            code = await self._generate_single_component(component, state)
            generated_files[component['file_path']] = code
        
        # Update existing files
        for update in analysis.get('updates', []):
            if 'App.jsx' in update['file']:
                updated_code = await self._update_app_jsx(state, analysis)
                generated_files[f"{os.getenv('FRONTEND_PATH', 'todo-app/frontend')}/src/App.jsx"] = updated_code
        
        return generated_files
    
    async def _generate_single_component(self, component_info, state):
        """Generate a single React component using AI"""
        
        prompt = f"""
        Create a production-ready React component: {component_info['name']}
        
        Purpose: {component_info['purpose']}
        Context: {state['issue_description']}
        
        Requirements:
        - Modern React with hooks
        - TypeScript if possible, otherwise JavaScript
        - Proper error handling
        - Accessibility (ARIA labels)
        - Clean, professional styling
        
        Return only the component code, no explanations.
        """
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a senior React developer. Create clean, production-ready components."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=2000
        )
        
        return response.choices[0].message.content
    
    def _fallback_generation(self, state):
        """Your existing template-based generation as fallback"""
        # Use your existing code generation logic here
        # This ensures the system always works even if AI fails
        
        description = state['issue_description'].lower()
        generated_code = {}
        
        # Export functionality (your existing logic)
        if "export" in description or "download" in description:
            generated_code[f"{os.getenv('FRONTEND_PATH')}/src/components/ExportButton.jsx"] = '''
import React from 'react';

const ExportButton = ({ todos }) => {
  const exportToCSV = () => {
    if (!todos || todos.length === 0) {
      alert('No todos to export!');
      return;
    }

    const headers = ['Title', 'Description', 'Priority', 'Category', 'Completed', 'Created Date'];
    const csvContent = [
      headers.join(','),
      ...todos.map(todo => [
        `"${(todo.title || '').replace(/"/g, '""')}"`,
        `"${(todo.description || '').replace(/"/g, '""')}"`,
        todo.priority || 'medium',
        todo.category || 'general',
        todo.completed ? 'Yes' : 'No',
        new Date(todo.created_at).toLocaleDateString()
      ].join(','))
    ].join('\\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `todos-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    
    console.log(`Exported ${todos.length} todos to CSV`);
  };

  return (
    <button onClick={exportToCSV} className="export-btn" title="Export all todos to CSV file">
      📥 Export to CSV ({todos?.length || 0} todos)
    </button>
  );
};

export default ExportButton;'''
        
        return generated_code