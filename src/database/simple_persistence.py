import asyncpg
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class SimplePersistence:
    """Simple database persistence you can add immediately"""
    
    def __init__(self):
        self.db_url = os.getenv("DATABASE_URL", "postgresql://localhost:5432/langgraph")
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection and tables"""
        try:
            self.pool = await asyncpg.create_pool(self.db_url)
            await self._create_tables()
            logger.info("Database persistence initialized")
        except Exception as e:
            logger.warning(f"Database not available, using memory only: {e}")
            self.pool = None
    
    async def _create_tables(self):
        """Create necessary tables"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS automation_runs (
                    id SERIAL PRIMARY KEY,
                    trace_id VARCHAR(255) UNIQUE,
                    issue_key VARCHAR(100),
                    summary TEXT,
                    status VARCHAR(50),
                    files_generated INTEGER DEFAULT 0,
                    errors_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW(),
                    completed_at TIMESTAMP,
                    metadata JSONB
                )
            ''')
    
    async def save_execution(self, state):
        """Save execution state to database"""
        if not self.pool:
            return  # Skip if no database
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute('''
                    INSERT INTO automation_runs 
                    (trace_id, issue_key, summary, status, files_generated, errors_count, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (trace_id) DO UPDATE SET
                    status = $4, files_generated = $5, errors_count = $6, 
                    completed_at = NOW(), metadata = $7
                ''', 
                state['trace_id'],
                state.get('issue_key', ''),
                state.get('issue_summary', ''),
                'completed' if state.get('deployment_successful') else 'failed',
                len(state.get('generated_code', {})),
                len(state.get('errors', [])),
                json.dumps({
                    'requirements': state.get('requirements', {}),
                    'file_changes': [{'file': fc.file, 'action': fc.action} for fc in state.get('file_changes', [])]
                })
                )
            logger.info(f"Saved execution {state['trace_id']} to database")
        except Exception as e:
            logger.error(f"Failed to save to database: {e}")
    
    async def get_recent_executions(self, limit: int = 10) -> List[Dict]:
        """Get recent automation executions"""
        if not self.pool:
            return []
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch('''
                    SELECT trace_id, issue_key, summary, status, files_generated, 
                           errors_count, created_at, completed_at
                    FROM automation_runs 
                    ORDER BY created_at DESC 
                    LIMIT $1
                ''', limit)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get executions: {e}")
            return []