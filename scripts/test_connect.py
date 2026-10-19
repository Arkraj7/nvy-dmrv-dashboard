#!/usr/bin/env python3
"""Test basic HTTPS connectivity on the runner."""
import requests
import certifi

print("Testing connectivity...")

try:
    r = requests.get('https://example.com', timeout=10, verify=certifi.where())
    print('example.com:', r.status_code)
except Exception as e:
    print('ERROR:', type(e).__name__, str(e))

try:
    r = requests.get('https://www.ceew.in/careers', timeout=15, verify=certifi.where(), headers={'User-Agent': 'UrbanForestPark-Verifier/1.0'})
    print('ceew.in/careers:', r.status_code)
except Exception as e:
    print('ceew.in ERROR:', type(e).__name__, str(e))