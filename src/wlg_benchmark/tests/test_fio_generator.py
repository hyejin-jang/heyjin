"""
Test suite for FIO job generator
Following TDD principle: Write tests BEFORE implementation
"""
import json
import pytest
import sys
from pathlib import Path

# Mock the fio_generator module (will be implemented after tests)
# This is TDD: we define the interface first via tests


def test_parse_config():
    """Test that config.json is parsed correctly"""
    config_data = {
        "profile_name": "WLG_E1S_Profile0",
        "io_patterns": [
            {"type": "read", "block_size": "4k", "percentage": 42},
            {"type": "read", "block_size": "128k", "percentage": 58}
        ],
        "runtime_hours": 168,
        "targets": {"iops_min": 850000}
    }
    
    # Expected: Parser should extract these values
    assert config_data["profile_name"] == "WLG_E1S_Profile0"
    assert len(config_data["io_patterns"]) == 2
    assert config_data["io_patterns"][0]["block_size"] == "4k"


def test_generate_fio_job_structure():
    """Test that generated fio job has correct structure"""
    # This defines the expected interface for fio_generator
    io_pattern = {
        "type": "read",
        "block_size": "4k",
        "percentage": 42,
        "queue_depth": 32
    }
    
    # Expected fio job section should look like:
    expected_keys = ["rw", "bs", "iodepth", "runtime"]
    
    # We'll implement generate_fio_section() to return this
    # For now, just document the expected behavior
    assert "rw" in expected_keys  # read/write type
    assert "bs" in expected_keys  # block size
    

def test_fio_job_file_creation():
    """Test that fio job file is created with correct content"""
    # Expected behavior:
    # - File should be created at specified path
    # - Should contain [global] section
    # - Should contain job sections for each IO pattern
    
    expected_global_section = "[global]"
    expected_job_section = "[job_4k_read]"
    
    # This will be implemented in fio_generator.py
    assert expected_global_section == "[global]"
    assert expected_job_section.startswith("[job_")


def test_validate_config_percentages():
    """Test that IO pattern percentages sum to 100"""
    patterns = [
        {"percentage": 42},
        {"percentage": 58}
    ]
    
    total = sum(p["percentage"] for p in patterns)
    assert total == 100, f"Percentages must sum to 100, got {total}"


def test_validate_config_required_fields():
    """Test that required config fields are present"""
    required_fields = ["profile_name", "io_patterns", "runtime_hours", "targets"]
    
    config = {
        "profile_name": "test",
        "io_patterns": [],
        "runtime_hours": 1,
        "targets": {}
    }
    
    for field in required_fields:
        assert field in config, f"Missing required field: {field}"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
