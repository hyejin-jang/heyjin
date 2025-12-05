"""
FIO Job Generator
Converts abstract config.json to fio job files
"""
import json
from pathlib import Path
from typing import Dict, List


def load_config(config_path: str) -> Dict:
    """
    Load and validate configuration file
    
    Args:
        config_path: Path to config.json
        
    Returns:
        Parsed configuration dictionary
        
    Raises:
        ValueError: If config is invalid
    """
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Validate required fields
    required = ["profile_name", "io_patterns", "runtime_hours", "targets"]
    for field in required:
        if field not in config:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate percentages sum to 100
    total_pct = sum(p["percentage"] for p in config["io_patterns"])
    if total_pct != 100:
        raise ValueError(f"IO pattern percentages must sum to 100, got {total_pct}")
    
    return config


def generate_fio_section(job_name: str, pattern: Dict, device_path: str, runtime_hours: int) -> str:
    """
    Generate a single fio job section
    
    Args:
        job_name: Name for this job section
        pattern: IO pattern dict (type, block_size, percentage, queue_depth)
        device_path: Device path (e.g., /dev/nvme0n1)
        runtime_hours: Test runtime in hours
        
    Returns:
        Fio job section as string
    """
    # Convert type to fio rw parameter
    rw_map = {
        "read": "randread",
        "write": "randwrite",
        "mixed": "randrw"
    }
    
    rw = rw_map.get(pattern["type"], "randread")
    bs = pattern["block_size"]
    iodepth = pattern.get("queue_depth", 32)
    runtime_sec = runtime_hours * 3600
    
    section = f"""
[{job_name}]
rw={rw}
bs={bs}
iodepth={iodepth}
numjobs=1
filename={device_path}
runtime={runtime_sec}
time_based=1
"""
    return section


def generate_fio_job(config: Dict, output_path: str) -> None:
    """
    Generate complete fio job file from config
    
    Args:
        config: Configuration dictionary
        output_path: Where to save the .fio file
    """
    device_path = config.get("device", {}).get("path", "/dev/nvme0n1")
    runtime_hours = config["runtime_hours"]
    
    # Start with global section
    fio_content = f"""# Generated FIO job for {config['profile_name']}
# DO NOT EDIT - Generated from config.json

[global]
ioengine=libaio
direct=1
group_reporting=1
"""
    
    # Add job section for each IO pattern
    for idx, pattern in enumerate(config["io_patterns"]):
        job_name = f"job_{pattern['block_size']}_{pattern['type']}"
        section = generate_fio_section(job_name, pattern, device_path, runtime_hours)
        fio_content += section
    
    # Write to file
    with open(output_path, 'w') as f:
        f.write(fio_content)
    
    print(f"✅ Generated fio job: {output_path}")


if __name__ == "__main__":
    # Example usage
    config = load_config("config.json")
    generate_fio_job(config, "benchmark.fio")
