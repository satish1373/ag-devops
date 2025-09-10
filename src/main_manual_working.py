import asyncio
from typing import Dict, Any
import uuid
from datetime import datetime

async def process_jira_webhook(webhook_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Simple test version of the automation function"""
    
    # Extract basic info
    issue_data = webhook_payload.get('issue', {})
    issue_key = issue_data.get('key', 'UNKNOWN')
    issue_summary = issue_data.get('fields', {}).get('summary', 'No summary')
    
    # Simulate processing
    await asyncio.sleep(1)
    
    return {
        'trace_id': str(uuid.uuid4()),
        'issue_key': issue_key,
        'issue_summary': issue_summary,
        'status': 'SUCCESS',
        'files_generated': 2,
        'success_rate': 100.0,
        'timestamp': datetime.now().isoformat()
    }
