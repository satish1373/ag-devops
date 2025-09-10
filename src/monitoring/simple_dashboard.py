from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import json
from datetime import datetime, timedelta

class SimpleDashboard:
    """Simple monitoring dashboard you can add to your FastAPI app"""
    
    def __init__(self, app: FastAPI, persistence):
        self.app = app
        self.persistence = persistence
        self._add_routes()
    
    def _add_routes(self):
        @self.app.get("/dashboard", response_class=HTMLResponse)
        async def dashboard():
            return await self._generate_dashboard_html()
        
        @self.app.get("/api/stats")
        async def get_stats():
            return await self._get_system_stats()
    
    async def _generate_dashboard_html(self):
        """Generate simple HTML dashboard"""
        
        stats = await self._get_system_stats()
        recent_runs = await self.persistence.get_recent_executions(10)
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>LangGraph DevOps Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .card {{ background: white; padding: 20px; margin: 10px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .metric {{ display: inline-block; margin: 10px 20px; text-align: center; }}
                .metric-value {{ font-size: 2em; font-weight: bold; color: #2196F3; }}
                .metric-label {{ color: #666; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                .status-success {{ color: #4CAF50; font-weight: bold; }}
                .status-failed {{ color: #f44336; font-weight: bold; }}
                .refresh-btn {{ background: #2196F3; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }}
            </style>
            <script>
                setInterval(() => location.reload(), 30000); // Auto-refresh every 30 seconds
            </script>
        </head>
        <body>
            <div class="container">
                <h1>🚀 LangGraph DevOps Autocoder Dashboard</h1>
                
                <div class="card">
                    <h2>System Metrics</h2>
                    <div class="metric">
                        <div class="metric-value">{stats['total_runs']}</div>
                        <div class="metric-label">Total Automations</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{stats['success_rate']:.1f}%</div>
                        <div class="metric-label">Success Rate</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{stats['avg_files_generated']:.1f}</div>
                        <div class="metric-label">Avg Files Generated</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{stats['total_files']}</div>
                        <div class="metric-label">Total Files Created</div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>Recent Automation Runs</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Issue</th>
                                <th>Summary</th>
                                <th>Status</th>
                                <th>Files</th>
                                <th>Errors</th>
                            </tr>
                        </thead>
                        <tbody>
        '''
        
        for run in recent_runs:
            status_class = 'status-success' if run['status'] == 'completed' else 'status-failed'
            html += f'''
                            <tr>
                                <td>{run['created_at'].strftime('%H:%M:%S')}</td>
                                <td>{run['issue_key']}</td>
                                <td>{run['summary'][:50]}...</td>
                                <td class="{status_class}">{run['status']}</td>
                                <td>{run['files_generated']}</td>
                                <td>{run['errors_count']}</td>
                            </tr>
            '''
        
        html += '''
                        </tbody>
                    </table>
                </div>
                
                <div class="card">
                    <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
                    <p><strong>Last Updated:</strong> ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        return html
    
    async def _get_system_stats(self):
        """Get system statistics"""
        
        recent_runs = await self.persistence.get_recent_executions(100)
        
        if not recent_runs:
            return {
                'total_runs': 0,
                'success_rate': 0,
                'avg_files_generated': 0,
                'total_files': 0
            }
        
        successful_runs = [r for r in recent_runs if r['status'] == 'completed']
        
        return {
            'total_runs': len(recent_runs),
            'success_rate': (len(successful_runs) / len(recent_runs)) * 100,
            'avg_files_generated': sum(r['files_generated'] for r in recent_runs) / len(recent_runs),
            'total_files': sum(r['files_generated'] for r in recent_runs)
        }