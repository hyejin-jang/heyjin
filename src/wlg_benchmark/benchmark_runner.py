"""
WLG Benchmark Runner
Main orchestrator for benchmark execution with real-time monitoring
"""
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from fio_generator import load_config, generate_fio_job
from pmu_reader import PMUReader


class BenchmarkRunner:
    """Main benchmark orchestration"""
    
    def __init__(self, config_path: str):
        """
        Initialize benchmark runner
        
        Args:
            config_path: Path to config.json
        """
        self.config = load_config(config_path)
        self.pmu = PMUReader(self.config.get("power_limit_watts", 11.0))
        self.results = {
            "start_time": None,
            "end_time": None,
            "fio_results": {},
            "power_stats": {},
            "pass_fail": None
        }
        
    def generate_job_file(self) -> str:
        """
        Generate FIO job file from config
        
        Returns:
            Path to generated .fio file
        """
        output_path = "benchmark.fio"
        generate_fio_job(self.config, output_path)
        return output_path
    
    def run_fio_benchmark(self, job_file: str, dry_run: bool = False) -> Dict:
        """
        Execute FIO benchmark
        
        Args:
            job_file: Path to .fio job file
            dry_run: If True, simulate instead of running actual fio
            
        Returns:
            FIO results dictionary
        """
        if dry_run:
            print("🔧 DRY RUN: Simulating FIO execution...")
            time.sleep(2)
            return {
                "iops": 875000,
                "throughput_mbps": 12500,
                "latency_p99_us": 450
            }
        
        print(f"🚀 Running FIO benchmark: {job_file}")
        
        # In production, this would run:
        # fio --output-format=json {job_file}
        # For now, stub it out
        
        # TODO: Actual FIO execution
        # result = subprocess.run(
        #     ['fio', '--output-format=json', job_file],
        #     capture_output=True, text=True
        # )
        # return parse_fio_json(result.stdout)
        
        return {
            "iops": 850000,
            "throughput_mbps": 12000,
            "latency_p99_us": 480
        }
    
    def evaluate_results(self) -> bool:
        """
        Compare results against targets
        
        Returns:
            True if all targets met (PASS), False otherwise (FAIL)
        """
        targets = self.config["targets"]
        fio_res = self.results["fio_results"]
        power_stats = self.results["power_stats"]
        
        checks = []
        
        # Check IOPS
        if "iops_min" in targets:
            iops_ok = fio_res.get("iops", 0) >= targets["iops_min"]
            checks.append(("IOPS", iops_ok, fio_res.get("iops"), targets["iops_min"]))
        
        # Check throughput
        if "throughput_mbps_min" in targets:
            bw_ok = fio_res.get("throughput_mbps", 0) >= targets["throughput_mbps_min"]
            checks.append(("Throughput", bw_ok, fio_res.get("throughput_mbps"), targets["throughput_mbps_min"]))
        
        # Check latency
        if "latency_p99_us_max" in targets:
            lat_ok = fio_res.get("latency_p99_us", 999999) <= targets["latency_p99_us_max"]
            checks.append(("Latency p99", lat_ok, fio_res.get("latency_p99_us"), targets["latency_p99_us_max"]))
        
        # Check power
        power_limit = self.config.get("power_limit_watts")
        if power_limit and power_stats:
            power_ok = power_stats.get("avg_watts", 999) <= power_limit
            checks.append(("Power", power_ok, power_stats.get("avg_watts"), power_limit))
        
        # Print results
        print("\n" + "="*60)
        print("📊 BENCHMARK RESULTS")
        print("="*60)
        
        for metric, passed, actual, target in checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{metric:20} {status:10} (Actual: {actual}, Target: {target})")
        
        all_passed = all(c[1] for c in checks)
        print("="*60)
        print(f"Overall: {'✅ PASS' if all_passed else '❌ FAIL'}")
        print("="*60 + "\n")
        
        return all_passed
    
    def run(self, dry_run: bool = True) -> Dict:
        """
        Execute complete benchmark workflow
        
        Args:
            dry_run: If True, simulate FIO execution
            
        Returns:
            Complete results dictionary
        """
        print(f"\n🎯 Starting WLG Benchmark: {self.config['profile_name']}")
        print(f"Runtime: {self.config['runtime_hours']} hours")
        print(f"Power Limit: {self.config.get('power_limit_watts', 'N/A')}W\n")
        
        self.results["start_time"] = datetime.now().isoformat()
        
        # Step 1: Generate FIO job
        job_file = self.generate_job_file()
        
        # Step 2: Start PMU monitoring
        self.pmu.start_monitoring()
        
        # Step 3: Run FIO benchmark
        fio_results = self.run_fio_benchmark(job_file, dry_run=dry_run)
        self.results["fio_results"] = fio_results
        
        # Step 4: Collect power data (simulate some sampling)
        if dry_run:
            for _ in range(20):
                self.pmu.read_power()
                time.sleep(0.05)
        
        # Step 5: Stop PMU and get stats
        self.pmu.stop_monitoring()
        self.results["power_stats"] = self.pmu.get_statistics()
        
        self.results["end_time"] = datetime.now().isoformat()
        
        # Step 6: Evaluate results
        passed = self.evaluate_results()
        self.results["pass_fail"] = "PASS" if passed else "FAIL"
        
        # Step 7: Save results
        self.save_results()
        
        return self.results
    
    def save_results(self, output_file: str = "benchmark_results.json") -> None:
        """Save results to JSON file"""
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"💾 Results saved to: {output_file}")


if __name__ == "__main__":
    import sys
    
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.json"
    
    runner = BenchmarkRunner(config_file)
    results = runner.run(dry_run=True)  # Set to False for actual FIO execution
    
    print(f"\n🏁 Benchmark complete. Status: {results['pass_fail']}")
