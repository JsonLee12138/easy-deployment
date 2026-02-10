#!/usr/bin/env python3
import json
import sys

r = json.load(open(sys.argv[1], 'r', encoding='utf-8'))
if r.get('containers_up') and r.get('health_ok') and not r.get('fatal_logs') and r.get('critical_path_ok'):
    print('SMOKE_OK')
    sys.exit(0)
print('SMOKE_FAIL')
sys.exit(1)
