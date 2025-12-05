"""
WLG Profile Test Orchestrator
Manages concurrent execution of multiple FIO jobs
"""
import subprocess
import json
import time
import os
from typing import List, Dict
from datetime import datetime
import threading


class WLGOrchestrator:
    """Orchestrate multi-threaded FIO execution"""
    
    def __init__(self, profile_config_path: str):
        """Initialize orchestrator"""
        with open(profile_config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.processes = []
        self.results = {}
        self.start_time = None
    
    def run_fio_job(self, job_file: str, job_name: str) -> Dict:
        """
        Run single FIO job and collect results
        
        Args:
            job_file: Path to .fio file
            job_name: Identifier for this job
            
        Returns:
            Job results dictionary
        """
        print(f"🚀 Starting: {job_name}")
        
        # Run FIO with JSON output
        cmd = ['fio', '--output-format=json', job_file]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config['runtime_hours'] * 3600 + 300  # +5 min buffer
            )
            
            if result.returncode == 0:
                # Parse JSON output
                fio_output = json.loads(result.stdout)
                return {
                    'job_name': job_name,
                    'status': 'success',
                    'output': fio_output,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'job_name': job_name,
                    'status': 'failed',
                    'error': result.stderr,
                    'timestamp': datetime.now().isoformat()
                }
        
        except subprocess.TimeoutExpired:
            return {
                'job_name': job_name,
                'status': 'timeout',
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'job_name': job_name,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def run_job_async(self, job_file: str, job_name: str):
        """Run FIO job in separate thread"""
        result = self.run_fio_job(job_file, job_name)
        self.results[job_name] = result
        print(f"✅ Completed: {job_name}")
    
    def run_profile(self, job_files: List[str], output_dir: str = "results") -> Dict:
        """
        Run all jobs for a profile concurrently
        
        Args:
            job_files: List of .fio file paths
            output_dir: Directory to save results
            
        Returns:
            Combined results dictionary
        """
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n{'='*60}")
        print(f"Starting WLG Profile {self.config['profile_id']} Test")
        print(f"Running {len(job_files)} concurrent jobs")
        print(f"{'='*60}\n")
        
        self.start_time = datetime.now()
        threads = []
        
        # Start all jobs as threads
        for job_file in job_files:
            job_name = os.path.basename(job_file).replace('.fio', '')
            
            thread = threading.Thread(
                target=self.run_job_async,
                args=(job_file, job_name)
            )
            thread.start()
            threads.append(thread)
            time.sleep(1)  # Stagger starts slightly
        
        # Wait for all to complete
        print(f"\n⏳ Waiting for all jobs to complete...")
        print(f"   Estimated runtime: {self.config['runtime_hours']} hours\n")
        
        for thread in threads:
            thread.join()
        
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print(f"\n{'='*60}")
        print(f"✅ All jobs completed")
        print(f"   Duration: {duration/3600:.2f} hours")
        print(f"{'='*60}\n")
        
        # Save results
        results_file = os.path.join(
            output_dir,
            f"profile_{self.config['profile_id']}_results_{int(time.time())}.json"
        )
        
        combined_results = {
            'profile_id': self.config['profile_id'],
            'profile_name': self.config['profile_name'],
            'start_time': self.start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_hours': duration / 3600,
            'jobs': self.results
        }
        
        with open(results_file, 'w') as f:
            json.dump(combined_results, f, indent=2)
        
        print(f"💾 Results saved to: {results_file}\n")
        
        return combined_results
    
    def validate_results(self, results: Dict, capacity: str) -> Dict:
        """
        Validate test results against requirements
        
        Args:
            results: Test results dictionary
            capacity: Tested capacity (e.g., "64TB")
            
        Returns:
            Validation report
        """
        targets = self.config['throughput_targets'][capacity]
        validation = {
            'pass': True,
            'checks': []
        }
        
        # Check each job
        for job_name, job_result in results['jobs'].items():
            if job_result['status'] != 'success':
                validation['checks'].append({
                    'job': job_name,
                    'check': 'execution',
                    'passed': False,
                    'message': f"Job failed: {job_result.get('error', 'Unknown')}"
                })
                validation['pass'] = False
                continue
            
            # Extract FIO metrics (simplified - actual parsing needed)
            # This would parse job_result['output'] for throughput and latency
            # For now, placeholder
            validation['checks'].append({
                'job': job_name,
                'check': 'execution',
                'passed': True,
                'message': 'Job completed successfully'
            })
        
        return validation


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py <job_list_file>")
        print("Example: python orchestrator.py profile_1_64TB_jobs.txt")
        sys.exit(1)
    
    job_list_file = sys.argv[1]
    
    # Read job files
    with open(job_list_file, 'r') as f:
        job_files = [line.strip() for line in f if line.strip()]
    
    # Extract profile from first job file
    first_job = os.path.basename(job_files[0])
    profile_num = first_job.split('_')[0].replace('profile', '')
    config_file = f"config/profile_{profile_num}.json"
    
    print(f"📋 Using config: {config_file}")
    print(f"📁 {len(job_files)} jobs to run\n")
    
    orchestrator = WLGOrchestrator(config_file)
    results = orchestrator.run_profile(job_files)
    
    print("\n🎉 Test completed!")
