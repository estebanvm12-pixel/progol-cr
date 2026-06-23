import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from analysis.calibration import calibration_summary
from analysis.bias_detection import detect_biases

print("=== CALIBRATION ===")
result = calibration_summary(last_n=100)
print("Status:", result.get("status"))
print("Sample:", result.get("sample_size"))
print("Brier:", result.get("brier_score"))
print("Accuracy:", result.get("accuracy"))
print("ECE:", result.get("ece"))
print("Calibration:", result.get("calibration"))
print("Narrative:", result.get("narrative"))
print("Curve entries:", len(result.get("curve", [])))
print("Trend entries:", len(result.get("weekly_trend", [])))

print()
print("=== BIAS DETECTION ===")
res = detect_biases(last_n=200)
print("Status:", res.get("status"))
print("Sample:", res.get("sample_size"))
print("Biases:", len(res.get("biases", [])))
print("Insights:", len(res.get("insights", [])))
print("Narrative:", res.get("narrative"))
for b in res.get("biases", []):
    print(f"  [{b.get('severity')}] {b.get('type')}: {b.get('message')}")
for i in res.get("insights", []):
    print(f"  [info] {i.get('type')}: {i.get('message')}")

print()
print("OK - analysis modules OK")
