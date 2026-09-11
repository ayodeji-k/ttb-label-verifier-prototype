"""Tests for authentication module"""

import pytest
from unittest.mock import patch
import os


class TestAPIKeyAuth:
    """Test API key authentication"""
    
    def test_valid_api_key_config(self):
        """Test API keys are properly configured"""
        # Environment variable should contain demo key by default
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from app.auth import VALID_API_KEYS
        # Should have at least the demo key
        assert len(VALID_API_KEYS) > 0


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limiter_basic(self):
        """Test basic rate limiter"""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from app.rate_limit import RateLimiter
        
        limiter = RateLimiter(max_requests=3, time_window=60)
        
        # First 3 requests should pass
        for i in range(3):
            is_limited, remaining = limiter.is_rate_limited("test_client")
            assert not is_limited
            assert remaining == 2 - i
        
        # 4th request should be limited
        is_limited, remaining = limiter.is_rate_limited("test_client")
        assert is_limited
        assert remaining == 0
    
    def test_rate_limiter_multiple_clients(self):
        """Test rate limiter with multiple clients"""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from app.rate_limit import RateLimiter
        
        limiter = RateLimiter(max_requests=2, time_window=60)
        
        # Client 1
        is_limited1, _ = limiter.is_rate_limited("client1")
        assert not is_limited1
        
        # Client 2
        is_limited2, _ = limiter.is_rate_limited("client2")
        assert not is_limited2
        
        # Each client has independent limits
        is_limited1, _ = limiter.is_rate_limited("client1")
        assert not is_limited1
        
        is_limited2, _ = limiter.is_rate_limited("client2")
        assert not is_limited2
        
        # Both hit limit on 3rd request
        is_limited1, _ = limiter.is_rate_limited("client1")
        assert is_limited1
        
        is_limited2, _ = limiter.is_rate_limited("client2")
        assert is_limited2


class TestLogging:
    """Test logging configuration"""
    
    def test_logging_setup(self):
        """Test logging configuration"""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from app.logging_config import setup_logging
        import logging
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            
            # Should not raise
            setup_logging(level="INFO", log_file=log_file)
            
            # Log something
            logger = logging.getLogger(__name__)
            logger.info("Test message")
            
            # Check if file was created
            assert os.path.exists(log_file)
    
    def test_json_formatter(self):
        """Test JSON formatter"""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from app.logging_config import JSONFormatter
        import logging
        import json
        
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        formatted = formatter.format(record)
        
        # Should be valid JSON
        parsed = json.loads(formatted)
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed
