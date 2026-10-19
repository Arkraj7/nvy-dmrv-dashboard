import os
os.environ['REQUESTS_CA_BUNDLE'] = __import__('certifi').where()

import sys
sys.path.insert(0, 'scripts')
from verify_link import verify_link, load_employers_registry

registry = load_employers_registry('public/employers.json')

# Test with a job-specific URL for CEEW
tests = [
    ('https://www.linkedin.com/jobs/view/123', 'wildlife-institute-of-wii', 'Test', 'Wildlife Institute of India', 'BLOCKED_HOST'),
    ('https://www.ceew.in/careers/research-intern-technology-futures-2', 'council-on-energy-environment-and-water-ceew', 'Research Intern - Technology Futures', 'Council on Energy, Environment and Water (CEEW)', 'OK'),
    ('https://www.ceew.in/careers/nonexistent', 'council-on-energy-environment-and-water-ceew', 'Test', 'CEEW', 'HTTP_404'),
    ('https://www.google.com', 'wildlife-institute-of-wii', 'Test', 'Wildlife Institute of India', 'BLOCKED_HOST'),
    ('https://www.indiawaterportal.org/opportunities/test', 'the-nature-conservancy-tnc', 'Test', 'The Nature Conservancy (TNC)', 'HOST_NOT_IN_REGISTRY'),
    ('https://example.com', 'wildlife-institute-of-wii', 'Test', 'Wildlife Institute of India', 'HOST_NOT_IN_REGISTRY'),
]

print("Running verification tests...")
for url, emp_id, title, org, expected in tests:
    result = verify_link(url, emp_id, title, org)
    status = 'PASS' if result.reason_code == expected else 'FAIL'
    print(f'{status:4s} {expected:30s} -> {result.reason_code:30s} (http={result.http_status}, ok={result.ok}, type={result.entry_type}, detail={result.error_detail[:50]})')