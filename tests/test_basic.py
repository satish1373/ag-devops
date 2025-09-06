import pytest
import asyncio
from src.main import process_jira_webhook

@pytest.mark.asyncio
async def test_webhook_processing():
    """Test basic webhook processing"""
    sample_webhook = {
        "signature": "sha256=test",
        "issue": {
            "key": "TEST-123",
            "fields": {
                "summary": "Test issue",
                "issuetype": {"name": "Story"},
                "description": "Test description"
            }
        }
    }
    
    result = await process_jira_webhook(sample_webhook)
    
    assert result['trace_id'] is not None
    assert result['issue_key'] == "TEST-123"
    assert isinstance(result['errors'], list)

def test_config_loading():
    """Test configuration loading"""
    from src.config import config
    
    assert config is not None
    # Add more specific tests based on your configuration