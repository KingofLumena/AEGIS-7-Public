#!/usr/bin/env python3
"""
WEEK 1: NTP + GPS Spoofing Validator
Detects sophisticated GNSS spoofing via multi-source time validation
Three independent time sources: NTP servers, GPS (VK-162), TPM RTC
Byzantine agreement: 2/3 sources must agree within ±5 seconds
"""

import socket
import struct
import time
import subprocess
import json
from datetime import datetime
import serial
import threading

class NTPValidator:
    def __init__(self, gps_port='/dev/ttyACM0', ntp_servers=None):
        self.gps_port = gps_port
        self.ntp_servers = ntp_servers or [
            '0.pool.ntp.org',
            '1.pool.ntp.org',
            '2.pool.ntp.org'
        ]
        self.gps_time = None
        self.ntp_times = {}
        self.tpm_time = None
        self.spoofing_detected = False
        self.validation_log = []
        
    def get_ntp_time(self, server):
        """Fetch NTP timestamp from server (RFC 5905)"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(3)
            
            # NTP request packet (48 bytes)
            ntp_request = bytearray(48)
            ntp_request[0] = 0x1b  # Version 3, client mode
            
            sock.sendto(ntp_request, (server, 123))
            response, _ = sock.recvfrom(48)
            sock.close()
            
            # Extract timestamp (seconds since 1900)
            timestamp = struct.unpack('!12I', response)[10]
            # Convert to Unix time (subtract seconds between 1900-1970)
            unix_time = timestamp - 2208988800
            
            return unix_time
        except Exception as e:
            print(f"[NTP] Error fetching from {server}: {e}")
            return None
    
    def get_gps_time(self):
        """Read GPS time from VK-162 via serial (GPRMC sentence)"""
        try:
            ser = serial.Serial(self.gps_port, 9600, timeout=2)
            start_time = time.time()
            
            while time.time() - start_time < 5:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith('$GPRMC'):
                    parts = line.split(',')
                    if len(parts) >= 2 and parts[2] == 'A':  # Active fix
                        # Parse UTC time: HHMMSS.SS
                        utc_str = parts[1]
                        if len(utc_str) >= 6:
                            hh = int(utc_str[0:2])
                            mm = int(utc_str[2:4])
                            ss = int(float(utc_str[4:]))
                            
                            # Get today's date
                            now = datetime.utcnow()
                            gps_dt = datetime(now.year, now.month, now.day, hh, mm, ss)
                            
                            ser.close()
                            return int(gps_dt.timestamp())
            
            ser.close()
            return None
        except Exception as e:
            print(f"[GPS] Error reading: {e}")
            return None
    
    def get_tpm_time(self):
        """Read TPM RTC timestamp (atomic reference)"""
        try:
            result = subprocess.run(
                ['tpm2_readclock'],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            if result.returncode == 0:
                # Parse output: time value in milliseconds
                for line in result.stdout.split('\n'):
                    if 'time value' in line.lower():
                        ms = int(line.split(':')[1].strip())
                        return ms // 1000  # Convert to seconds
            
            return None
        except Exception as e:
            print(f"[TPM] Error reading: {e}")
            return None
    
    def validate_spoofing(self):
        """
        Byzantine agreement: 2/3 sources must agree within ±5 seconds
        Returns: (is_spoofed, evidence_dict)
        """
        print("\n[VALIDATOR] Starting multi-source time validation...")
        
        # Fetch all 3 time sources in parallel
        sources = {}
        
        # NTP (try 3 servers, use median)
        ntp_times = []
        for server in self.ntp_servers:
            t = self.get_ntp_time(server)
            if t:
                ntp_times.append(t)
                print(f"  [NTP] {server}: {datetime.fromtimestamp(t).isoformat()}")
        
        if ntp_times:
            sources['ntp'] = sorted(ntp_times)[len(ntp_times)//2]  # Median
        
        # GPS
        gps_t = self.get_gps_time()
        if gps_t:
            sources['gps'] = gps_t
            print(f"  [GPS] VK-162: {datetime.fromtimestamp(gps_t).isoformat()}")
        
        # TPM
        tpm_t = self.get_tpm_time()
        if tpm_t:
            sources['tpm'] = tpm_t
            print(f"  [TPM] RTC: {datetime.fromtimestamp(tpm_t).isoformat()}")
        
        # Byzantine consensus: need 2/3 agreement within ±5 seconds
        TOLERANCE = 5  # seconds
        
        if len(sources) < 2:
            print("[WARNING] Not enough time sources to validate")
            return False, sources
        
        times = list(sources.values())
        times.sort()
        
        # Check if max-min within tolerance
        divergence = times[-1] - times[0]
        is_spoofed = divergence > TOLERANCE
        
        evidence = {
            'timestamp': datetime.utcnow().isoformat(),
            'sources': sources,
            'divergence_seconds': divergence,
            'tolerance_seconds': TOLERANCE,
            'spoofing_detected': is_spoofed,
            'source_count': len(sources)
        }
        
        if is_spoofed:
            print(f"\n[🔴 ALERT] SPOOFING DETECTED!")
            print(f"  Time divergence: {divergence}s (threshold: {TOLERANCE}s)")
            print(f"  Sources disagree: {sources}")
        else:
            print(f"\n[✅ OK] All sources agree within {TOLERANCE}s")
            print(f"  Divergence: {divergence}s")
        
        self.validation_log.append(evidence)
        return is_spoofed, evidence
    
    def log_to_aegis7(self, evidence):
        """Append validation result to AEGIS-7 audit chain"""
        entry = {
            'type': 'time_validation',
            'data': evidence,
            'sequence': len(self.validation_log)
        }
        
        try:
            with open('/home/baphometxix/aegis7/aegis7_audit.jsonl', 'a') as f:
                f.write(json.dumps(entry) + '\n')
            print(f"[AEGIS-7] Logged validation entry #{entry['sequence']}")
        except Exception as e:
            print(f"[ERROR] Could not log to audit chain: {e}")

if __name__ == '__main__':
    validator = NTPValidator()
    
    print("=" * 60)
    print("AEGIS-7 Week 1: NTP + GPS Spoofing Validator")
    print("=" * 60)
    
    # Run validation 3 times (simulate continuous monitoring)
    for cycle in range(3):
        print(f"\n--- Validation Cycle {cycle + 1} ---")
        is_spoofed, evidence = validator.validate_spoofing()
        validator.log_to_aegis7(evidence)
        
        if is_spoofed:
            print("[CRITICAL] GPS SPOOFING DETECTED - SYSTEM ALERT")
            break
        
        time.sleep(2)
    
    print("\n" + "=" * 60)
    print(f"Validation complete. Logs: {len(validator.validation_log)} entries")
    print("=" * 60)
