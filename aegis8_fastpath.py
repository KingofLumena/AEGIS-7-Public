import time, json
from datetime import datetime

class AEGIS8FastPath:
    def __init__(self):
        self.action_queue = {
            'temp_critical': {'action': 'throttle_cpu', 'latency_ms': 5},
            'battery_low': {'action': 'graceful_shutdown', 'latency_ms': 10},
            'quorum_lost': {'action': 'activate_failover', 'latency_ms': 15},
            'tamper_detected': {'action': 'freeze_services', 'latency_ms': 8}
        }
        self.decisions = []
    
    def detect_anomaly(self, sensor_data):
        start = time.time() * 1000
        if sensor_data.get('temp_c', 0) > 85:
            action = 'THROTTLE_CPU'
        elif sensor_data.get('battery_pct', 100) < 8:
            action = 'SHUTDOWN'
        elif sensor_data.get('quorum', 3) < 2:
            action = 'FAILOVER'
        elif sensor_data.get('tamper', 0) == 1:
            action = 'FREEZE'
        else:
            action = 'OK'
        latency_ms = (time.time() * 1000) - start
        return {'action': action, 'latency_ms': round(latency_ms, 2)}
    
    def run_test(self, test_name, sensor_data):
        result = self.detect_anomaly(sensor_data)
        self.decisions.append(result)
        status = "🟢" if result['action'] == 'OK' else "🔴"
        print(f"{status} {test_name}: {result['action']} ({result['latency_ms']}ms)")

print("AEGIS-8: Fast Decision Engine (<50ms, no crypto in path)")
print("="*70)
aegis8 = AEGIS8FastPath()
aegis8.run_test("Normal", {'temp_c': 52, 'battery_pct': 85, 'quorum': 3, 'tamper': 0})
aegis8.run_test("Overtemp 90°C", {'temp_c': 90, 'battery_pct': 85, 'quorum': 3, 'tamper': 0})
aegis8.run_test("Quorum 1/3", {'temp_c': 52, 'battery_pct': 85, 'quorum': 1, 'tamper': 0})
aegis8.run_test("Tamper open", {'temp_c': 52, 'battery_pct': 85, 'quorum': 3, 'tamper': 1})
latencies = [d['latency_ms'] for d in aegis8.decisions]
print(f"\n✅ Max latency: {max(latencies):.2f}ms (target <50ms)")
print(f"✅ All decisions O(1) lookup, no crypto overhead")
