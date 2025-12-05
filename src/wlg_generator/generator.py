"""
WLG Profile FIO Job Generator
Generates individual FIO job files for each block size pattern
"""
import json
import os
from pathlib import Path
from typing import Dict, List


class WLGJobGenerator:
    """Generate FIO jobs for WLG profiles"""
    
    def __init__(self, config_path: str):
        """Load profile configuration"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.profile_id = self.config['profile_id']
        self.profile_name = self.config['profile_name']
    
    def calculate_throughput(self, capacity: str, pattern_type: str, block_size: str, percentage: float) -> int:
        """
        Calculate target throughput for specific pattern
        
        Args:
            capacity: "16TB", "32TB", or "64TB"
            pattern_type: "read" or "write"
            block_size: e.g., "4k", "8k", "256k", "40k"
            percentage: percentage of total I/O for this block size
            
        Returns:
            Target throughput in MB/s
        """
        targets = self.config['throughput_targets'][capacity]
        
        if pattern_type == "read":
            # Read total을 percentage로 분배
            read_total = targets['read_total_mbps']
            return int(read_total * (percentage / 100))
        else:  # write
            # Write는 스펙에 명시된 값 사용
            if block_size == "4k":
                return targets['write_4k_mbps']
            elif block_size == "40k":
                return targets['write_40k_mbps']
            else:
                raise ValueError(f"Unknown write block size: {block_size}")
    
    def generate_read_job(self, pattern: Dict, capacity: str, output_dir: str) -> str:
        """Generate FIO job for read pattern"""
        block_size = pattern['block_size']
        percentage = pattern['percentage']
        throughput = self.calculate_throughput(capacity, "read", block_size, percentage)
        
        job_name = f"profile{self.profile_id}_read_{block_size}_{capacity}"
        job_file = os.path.join(output_dir, f"{job_name}.fio")
        
        mount_point = self.config['test_environment']['mount_point']
        test_file = self.config['test_environment']['test_file']
        runtime_sec = self.config['runtime_hours'] * 3600
        
        fio_content = f"""# WLG {self.profile_name} - Read {block_size} ({percentage}%)
# Target: {throughput} MB/s
# Capacity: {capacity}

[global]
ioengine=libaio
direct=1
group_reporting=1
time_based=1
runtime={runtime_sec}
ramp_time=60

[{job_name}]
rw=randread
bs={block_size}
numjobs=1
iodepth=32
filename={mount_point}/{test_file}
size=100%
rate={throughput}m
lat_percentiles=1
"""
        
        with open(job_file, 'w') as f:
            f.write(fio_content)
        
        print(f"✅ Generated: {job_file}")
        return job_file
    
    def generate_write_job(self, pattern: Dict, capacity: str, output_dir: str) -> str:
        """Generate FIO job for write pattern"""
        block_size = pattern['block_size']
        percentage = pattern['percentage']
        throughput = self.calculate_throughput(capacity, "write", block_size, percentage)
        
        job_name = f"profile{self.profile_id}_write_{block_size}_{capacity}"
        job_file = os.path.join(output_dir, f"{job_name}.fio")
        
        mount_point = self.config['test_environment']['mount_point']
        test_file = self.config['test_environment']['test_file']
        runtime_sec = self.config['runtime_hours'] * 3600
        
        fio_content = f"""# WLG {self.profile_name} - Write {block_size} ({percentage}%)
# Target: {throughput} MB/s
# Capacity: {capacity}

[global]
ioengine=libaio
direct=1
group_reporting=1
time_based=1
runtime={runtime_sec}
ramp_time=60

[{job_name}]
rw=randwrite
bs={block_size}
numjobs=1
iodepth=32
filename={mount_point}/{test_file}
size=100%
rate={throughput}m
lat_percentiles=1
"""
        
        with open(job_file, 'w') as f:
            f.write(fio_content)
        
        print(f"✅ Generated: {job_file}")
        return job_file
    
    def generate_all_jobs(self, capacity: str, output_dir: str = "output") -> List[str]:
        """
        Generate all FIO jobs for this profile
        
        Args:
            capacity: "16TB", "32TB", or "64TB"
            output_dir: Directory to save job files
            
        Returns:
            List of generated job file paths
        """
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"Generating FIO jobs for {self.profile_name} ({capacity})")
        print(f"{'='*60}\n")
        
        job_files = []
        
        # Generate read jobs
        print("📖 Read Jobs:")
        for pattern in self.config['read_patterns']:
            job_file = self.generate_read_job(pattern, capacity, output_dir)
            job_files.append(job_file)
        
        # Generate write jobs
        print("\n✍️  Write Jobs:")
        for pattern in self.config['write_patterns']:
            job_file = self.generate_write_job(pattern, capacity, output_dir)
            job_files.append(job_file)
        
        print(f"\n{'='*60}")
        print(f"✅ Generated {len(job_files)} FIO jobs")
        print(f"{'='*60}\n")
        
        return job_files
    
    def generate_summary(self, capacity: str) -> str:
        """Generate summary of expected workload"""
        targets = self.config['throughput_targets'][capacity]
        
        # Calculate read breakdown
        read_total = targets['read_total_mbps']
        read_breakdown = []
        for pattern in self.config['read_patterns']:
            mbps = int(read_total * (pattern['percentage'] / 100))
            read_breakdown.append(f"  - {pattern['block_size']}: {mbps} MB/s ({pattern['percentage']}%)")
        
        # Write breakdown
        write_breakdown = [
            f"  - 4k: {targets['write_4k_mbps']} MB/s (65%)",
            f"  - 40k: {targets['write_40k_mbps']} MB/s (35%)"
        ]
        
        summary = f"""
WLG {self.profile_name} Workload Summary ({capacity})
{'='*60}

Read Throughput: {read_total} MB/s
{chr(10).join(read_breakdown)}

Write Throughput: {targets['write_4k_mbps'] + targets['write_40k_mbps']} MB/s
{chr(10).join(write_breakdown)}

Total I/O: {read_total + targets['write_4k_mbps'] + targets['write_40k_mbps']} MB/s
Power Limit: {self.config['power_limit_watts']}W
Runtime: {self.config['runtime_hours']} hours
{'='*60}
"""
        return summary


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python generator.py <config_file> <capacity>")
        print("Example: python generator.py config/profile_1.json 64TB")
        sys.exit(1)
    
    config_file = sys.argv[1]
    capacity = sys.argv[2]
    
    generator = WLGJobGenerator(config_file)
    
    # Print summary
    print(generator.generate_summary(capacity))
    
    # Generate jobs
    job_files = generator.generate_all_jobs(capacity)
    
    # Save job list
    with open(f"profile_{generator.profile_id}_{capacity}_jobs.txt", 'w') as f:
        f.write('\n'.join(job_files))
    
    print(f"📝 Job list saved to: profile_{generator.profile_id}_{capacity}_jobs.txt")
