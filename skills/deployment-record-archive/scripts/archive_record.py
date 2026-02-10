#!/usr/bin/env python3
import json
import time
import uuid
import sys

record = json.load(open(sys.argv[1], 'r', encoding='utf-8'))
record.setdefault('record_id', str(uuid.uuid4()))
record.setdefault('archived_at', int(time.time()))

with open(sys.argv[2], 'a', encoding='utf-8') as f:
    f.write(json.dumps(record, ensure_ascii=True) + '\n')

print(record['record_id'])
