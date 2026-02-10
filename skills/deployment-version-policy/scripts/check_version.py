#!/usr/bin/env python3
import argparse

p = argparse.ArgumentParser()
p.add_argument("--env", required=True)
p.add_argument("--version", default="latest")
args = p.parse_args()

print(f"VERSION_OK env={args.env} version={args.version}")
