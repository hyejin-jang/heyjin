# AI Power Modeling Tool

Machine learning-based power consumption prediction and optimization for SSD WLG compliance.

## 🎯 Overview

This tool uses linear regression to model SSD power consumption based on workload patterns and provides actionable recommendations to meet WLG power targets (11W).

## 📐 Power Model

```
Power (W) = a × Read_MB/s + b × Write_MB/s + c × WAF + d

Where:
- a = Read power coefficient
- b = Write power coefficient
- c = WAF impact coefficient
- d = Baseline (idle) power
```

## 📁 Components

### 1. data_collector.py
Collects training data by running various workloads:
- Different R/W ratios (0/100, 25/75, 50/50, 75/25, 100/0)
- Multiple block sizes (4k, 128k)
- Measures power, throughput, WAF

### 2. power_model.py
Trains linear regression model using scikit-learn:
- Fits coefficients from training data
- Validates with test set
- Saves trained model to `.pkl` file

### 3. optimizer.py
Generates WLG optimization recommendations:
- Analyzes current workload
- Predicts power consumption
- Suggests specific actions (reduce writes, improve WAF)

### 4. model_visualizer.html
Interactive 3D visualization:
- Surface plot showing power vs. read/write throughput
- Live prediction with sliders
- Target power plane overlay (11W)

## 🚀 Usage

### Train Model

```bash
cd power_modeling

# 1. Collect training data
python data_collector.py

# 2. Train model
python power_model.py

# Output: power_model.pkl, training_data.json
```

### Optimize Workload

```bash
# Get recommendations for current workload
python optimizer.py

# Example output:
# ⚡ Predicted Power: 12.5W
# 💡 Recommendations:
#   1. Reduce write throughput by 20%
#      → Estimated power: 10.8W (saves 1.7W)
```

### Visualize

```bash
firefox model_visualizer.html
```

Use sliders to explore:
- How read/write ratio affects power
- WAF impact on consumption
- Find optimal settings for 11W target

## 📊 Example Results

```python
# Current workload
Read: 2000 MB/s
Write: 3000 MB/s
WAF: 2.5

# Predicted: 12.5W (1.5W over 11W target)

# Recommendation: Reduce writes to 2400 MB/s
# → New prediction: 10.9W ✓
```

## 🔐 Security

- ✅ Training data stays local
- ✅ No internal firmware details exposed
- ✅ Model coefficients are abstract numbers

## 🔧 Production Integration

Replace stub in `data_collector.py`:

```python
# Use actual PMU and FIO
from pmu_reader import PMUReader
import subprocess

pmu = PMUReader()
pmu.start_monitoring()

# Run real FIO workload
subprocess.run(['fio', job_file])

power = pmu.get_statistics()['avg_watts']
```

## 📝 Dependencies

```bash
pip install numpy scikit-learn
```

## 🎓 PoC Value

**Demonstrates:**
1. AI can learn power patterns from data
2. Provides actionable WLG optimization advice
3. Interactive visualization aids understanding

**Next Steps:**
- Integrate with real PMU data
- Expand to multi-variable optimization
- Add neural network for non-linear effects
