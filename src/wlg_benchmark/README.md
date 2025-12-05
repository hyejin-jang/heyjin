# WLG Benchmark Suite

Linux-based WLG benchmark tool with real-time monitoring and power measurement.

## 🎯 Features

- **Abstracted Configuration**: All workload parameters in `config.json`
- **FIO Integration**: Automatic fio job generation
- **Power Monitoring**: PMU interface (stub for PoC)
- **Real-time Dashboard**: Live IOPS, Throughput, Latency, Power graphs
- **Pass/Fail Evaluation**: Automatic target comparison
- **TDD**: Test-driven development with pytest

## 📁 Project Structure

```
wlg_benchmark/
├── config.json              # Workload configuration
├── fio_generator.py         # FIO job generator
├── pmu_reader.py            # Power measurement stub
├── benchmark_runner.py      # Main orchestrator
├── realtime_dashboard.html  # Live visualization
├── tests/
│   └── test_fio_generator.py
└── README.md
```

## 🚀 Quick Start

### 1. Configure Workload

Edit `config.json` to define your benchmark:

```json
{
  "profile_name": "WLG_E1S_Profile0",
  "io_patterns": [
    {"type": "read", "block_size": "4k", "percentage": 42},
    {"type": "read", "block_size": "128k", "percentage": 58}
  ],
  "power_limit_watts": 11,
  "targets": {
    "iops_min": 850000,
    "throughput_mbps_min": 12000
  }
}
```

### 2. Run Benchmark

```bash
# Dry run (simulation, no actual FIO)
python benchmark_runner.py config.json

# Real run (requires fio installed)
python benchmark_runner.py config.json --real
```

### 3. View Dashboard

```bash
# Open dashboard in browser
firefox realtime_dashboard.html
```

## 🧪 Testing

```bash
# Run tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_fio_generator.py::test_parse_config -v
```

## 🔧 Production Integration

### PMU Integration

Replace stub in `pmu_reader.py`:

```python
def read_pmu_actual():
    import subprocess
    result = subprocess.run(['/path/to/pmu_script.sh'], 
                           capture_output=True, text=True)
    return float(parse_output(result.stdout))
```

### FIO Execution

Uncomment actual fio execution in `benchmark_runner.py`:

```python
result = subprocess.run(
    ['fio', '--output-format=json', job_file],
    capture_output=True, text=True
)
```

## 📊 Results

Results are saved to `benchmark_results.json`:

```json
{
  "start_time": "2025-12-05T13:00:00",
  "fio_results": {
    "iops": 875000,
    "throughput_mbps": 12500,
    "latency_p99_us": 450
  },
  "power_stats": {
    "avg_watts": 10.8,
    "p99_watts": 11.2
  },
  "pass_fail": "PASS"
}
```

## 🔐 Security

- ✅ No hardcoded paths
- ✅ All specifics in config.json
- ✅ Abstracted interfaces
- ✅ Internal details stay internal

## 📝 License

Internal use only.
