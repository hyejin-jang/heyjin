"""
Data Collector for Power Modeling
Collects training data by running various workloads and measuring power
"""
import json
import time
import random
from typing import List, Dict
from pathlib import Path

# For PoC, we'll simulate. In production, import actual PMU and FIO runners
# from pmu_reader import PMUReader


class PowerDataCollector:
    """
    Collects power consumption data across different workload patterns
    
    For PoC: Simulates data collection
    For Production: Integrates with actual PMU and FIO
    """
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize data collector with config"""
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
        self.training_data = []
    
    def run_workload(self, read_pct: int, write_pct: int, block_size: str) -> Dict:
        """
        Run a specific workload and measure metrics
        
        Args:
            read_pct: Percentage of reads (0-100)
            write_pct: Percentage of writes (0-100)
            block_size: Block size (e.g., "4k", "128k")
            
        Returns:
            Metrics dictionary
        """
        print(f"📊 Running workload: {read_pct}% read, {write_pct}% write, BS={block_size}")
        
        # PoC: Simulate workload execution
        # Production: Actually run fio with these parameters
        time.sleep(0.5)  # Simulate test duration
        
        # Simulate realistic metrics
        # Power increases with write ratio and larger block sizes
        base_power = 8.0
        write_penalty = (write_pct / 100) * 3.0  # Writes consume more power
        block_bonus = 0.5 if block_size == "128k" else 0
        noise = random.uniform(-0.5, 0.5)
        
        power_watts = base_power + write_penalty + block_bonus + noise
        
        # Throughput
        read_mbps = (read_pct / 100) * 5000  # Max 5000 MB/s read
        write_mbps = (write_pct / 100) * 3000  # Max 3000 MB/s write
        
        # WAF (Write Amplification Factor) - higher for more writes
        waf = 1.0 + (write_pct / 100) * 1.5 + random.uniform(-0.2, 0.2)
        
        metrics = {
            "read_pct": read_pct,
            "write_pct": write_pct,
            "block_size": block_size,
            "read_mbps": round(read_mbps, 2),
            "write_mbps": round(write_mbps, 2),
            "waf": round(waf, 2),
            "power_watts": round(power_watts, 2)
        }
        
        print(f"   ⚡ Power: {metrics['power_watts']}W, WAF: {metrics['waf']}")
        
        return metrics
    
    def collect_training_data(self) -> List[Dict]:
        """
        Collect complete training dataset
        
        Returns:
            List of measurement dictionaries
        """
        print("\n🔬 Starting data collection for power modeling...")
        print("="*60)
        
        workloads = self.config["data_collection"]["workload_profiles"]
        block_sizes = self.config["data_collection"]["block_sizes"]
        
        for workload in workloads:
            for block_size in block_sizes:
                metrics = self.run_workload(
                    workload["read_pct"],
                    workload["write_pct"],
                    block_size
                )
                self.training_data.append(metrics)
        
        print("="*60)
        print(f"✅ Collected {len(self.training_data)} data points\n")
        
        return self.training_data
    
    def save_data(self, output_file: str = "training_data.json") -> None:
        """Save collected data to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(self.training_data, f, indent=2)
        print(f"💾 Training data saved to: {output_file}")
    
    def load_data(self, input_file: str = "training_data.json") -> List[Dict]:
        """Load previously collected data"""
        with open(input_file, 'r') as f:
            self.training_data = json.load(f)
        print(f"📂 Loaded {len(self.training_data)} data points from {input_file}")
        return self.training_data


# Production integration example (commented out for PoC)
# def run_actual_workload(read_pct, write_pct, block_size):
#     """Real implementation with FIO and PMU"""
#     # 1. Generate FIO job
#     fio_job = f"""
#     [global]
#     ioengine=libaio
#     direct=1
#     
#     [test]
#     rw=randrw
#     rwmixread={read_pct}
#     bs={block_size}
#     runtime=60
#     """
#     
#     # 2. Start PMU monitoring
#     pmu = PMUReader()
#     pmu.start_monitoring()
#     
#     # 3. Run FIO
#     result = subprocess.run(['fio', fio_job], capture_output=True)
#     
#     # 4. Get power stats
#     pmu.stop_monitoring()
#     power = pmu.get_statistics()['avg_watts']
#     
#     # 5. Parse FIO results for throughput
#     # ...
#     
#     return metrics


if __name__ == "__main__":
    collector = PowerDataCollector()
    data = collector.collect_training_data()
    collector.save_data()
    
    print("\n📈 Sample data points:")
    for i, point in enumerate(data[:3]):
        print(f"  {i+1}. R/W: {point['read_pct']}/{point['write_pct']}%, "
              f"Power: {point['power_watts']}W, WAF: {point['waf']}")
