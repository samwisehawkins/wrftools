#!/bin/bash
cd "$(dirname "$0")"
python prepare.py --config=prepare.yaml
python submit.py --config=submit.yaml
