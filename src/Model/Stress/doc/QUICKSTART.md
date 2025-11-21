# Quick Start Guide

## Running the Demo

### Option 1: Terminal (Recommended)

```bash
# Navigate to SWE directory
cd /Users/eojunho/HYU/25-2/SWE

# Activate venv
source venv/bin/activate

# Run demo
cd SWEG04/SWE-G04-SPACE/Model/Stress
python demo.py
```

### Option 2: VSCode

1. Open VSCode in SWE directory
2. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
3. Type "Python: Select Interpreter"
4. Choose `./venv/bin/python`
5. Open `demo.py`
6. Click "Run Python File" button (▶️) in top right

### Option 3: Direct Execution

```bash
/Users/eojunho/HYU/25-2/SWE/venv/bin/python demo.py
```

## Demo Output

```
╔══════════════════════════════════════════════════════════╗
║          SPACE Stress Detection Demo                     ║
╚══════════════════════════════════════════════════════════╝

============================================================
Demo 1: Basic HRV Calculation
============================================================

Heart Rate Data: 20 measurements
Mean Heart Rate: 74.3 BPM

HRV Metrics:
  SDNN:  18.16 ms
  RMSSD: 24.61 ms
  pNN50: 0.00 %

============================================================
Demo 2: Stress Detection from HRV
============================================================

Relaxed State:
----------------------------------------
  Mean HR: 61.8 BPM
  RMSSD: 26.28 ms
  Stress Level: Low (낮음)
  Stress Score: 25.0/100
  Confidence: 0.78
  Recommendation: 스트레스 수준이 낮고 건강합니다.

[... more scenarios ...]

============================================================
Demo 3: Real-time Stress Monitoring (10 seconds)
============================================================

[12:30:45] HR: 67 BPM | Stress: MODERATE (45/100)
[12:30:47] HR: 75 BPM | Stress: HIGH (72/100)
[12:30:49] HR: 88 BPM | Stress: VERY_HIGH (91/100)

🚨 HIGH STRESS ALERT!
   Level: 매우 높음
   Score: 91.0/100

✓ Demo completed!
```

## Using in Your Code

### Basic Usage

```python
from hrv_calculator import HRVCalculator
from stress_detector import StressDetector

# Heart rate data from Apple Watch
heart_rates = [72, 75, 73, 76, 74, 77, 75, 73, 71, 74]

# Calculate HRV
calculator = HRVCalculator()
hrv = calculator.calculate_hrv_from_heart_rates(heart_rates)

# Detect stress
detector = StressDetector()
assessment = detector.detect_stress(hrv)

print(f"Stress: {assessment.stress_level.to_korean()}")
print(f"Score: {assessment.stress_score:.0f}/100")
```

### Real-time Monitoring

```python
from realtime_monitor import RealtimeStressMonitor

# Create monitor
monitor = RealtimeStressMonitor(
    window_size=60,
    update_interval=10
)

# Add heart rate measurements
while True:
    hr = get_heart_rate_from_apple_watch()
    assessment = monitor.add_heart_rate(hr)

    if assessment:
        print(f"Stress: {assessment.stress_level}")
```

## Troubleshooting

### ModuleNotFoundError: No module named 'numpy'

**Solution**: Make sure you're using the venv Python interpreter

```bash
# Check which Python you're using
which python

# Should output: /Users/eojunho/HYU/25-2/SWE/venv/bin/python

# If not, activate venv
source /Users/eojunho/HYU/25-2/SWE/venv/bin/activate
```

### ImportError: attempted relative import

**Solution**: Already fixed! The imports have been changed to absolute imports.

### VSCode not finding modules

**Solution**:
1. Reload VSCode window: `Cmd+Shift+P` → "Developer: Reload Window"
2. Select correct interpreter: `Cmd+Shift+P` → "Python: Select Interpreter" → Choose venv
3. Check `.vscode/settings.json` exists with correct paths

## Files

- `demo.py` - Quick auto-run demo (no user input required)
- `example_usage.py` - Full examples with detailed explanations
- `hrv_calculator.py` - HRV calculation module
- `stress_detector.py` - Stress detection module
- `realtime_monitor.py` - Real-time monitoring module
- `README.md` - Full documentation

## Next Steps

- Read [README.md](README.md) for detailed documentation
- Explore [example_usage.py](example_usage.py) for more examples
- Integrate with Apple Watch using HealthKit
- Connect to FastAPI backend for smart home automation
