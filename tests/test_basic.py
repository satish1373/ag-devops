import pytest
import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

def test_environment_setup():
    """Test that the environment is properly set up"""
    # Check if required directories exist
    required_dirs = ['logs', 'reports', 'src', 'tests']
    
    for dir_name in required_dirs:
        assert Path(dir_name).exists(), f"Directory {dir_name} should exist"

def test_config_loading():
    """Test configuration loading"""
    try:
        from config import config
        
        assert config is not None
        # Basic configuration validation
        assert hasattr(config, 'jira_url')
        assert hasattr(config, 'github_token')
        assert hasattr(config, 'app_name')
        
    except ImportError as e:
        pytest.skip(f"Skipping test due to import error: {e}")

def test_basic_imports():
    """Test that basic Python imports work"""
    try:
        import asyncio
        import json
        import logging
        import os
        from pathlib import Path
        
        # Test that we can import the modules we need
        assert asyncio is not None
        assert json is not None
        assert logging is not None
        
    except ImportError as e:
        pytest.fail(f"Failed to import basic modules: {e}")

@pytest.mark.asyncio
async def test_basic_async():
    """Test that async functionality works"""
    async def dummy_async():
        await asyncio.sleep(0.001)
        return "success"
    
    result = await dummy_async()
    assert result == "success"
