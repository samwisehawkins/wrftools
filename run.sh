#!/bin/bash
pytime --cycles=[00] > times.txt
python prepare.py --config=config/prepare.yaml times.txt
pysub --config=config/submit.yaml times.txt
