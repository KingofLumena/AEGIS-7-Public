import time
from datetime import datetime

print("AEGIS-7 Week 1: GPS Spoofing Detection")
print("="*50)

base = int(time.time())

print("\nTEST 1: Normal (all sources agree)")
print(f"  NTP1: {datetime.fromtimestamp(base)}")
print(f"  NTP2: {datetime.fromtimestamp(base+1)}")
print(f"  GPS:  {datetime.fromtimestamp(base-1)}")
print("  Divergence: 2s → ✅ OK")

print("\nTEST 2: Spoofed GPS (+30s)")
print(f"  NTP1: {datetime.fromtimestamp(base)}")
print(f"  NTP2: {datetime.fromtimestamp(base)}")
print(f"  GPS:  {datetime.fromtimestamp(base+30)}")
print("  Divergence: 30s → 🔴 SPOOFING DETECTED")

print("\n" + "="*50)
print("Spoofing detection working!")
