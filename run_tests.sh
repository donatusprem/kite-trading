#!/bin/bash
echo "Running Nifty Strategy Check..."
python3 check_nifty_strategy.py > nifty_output.txt 2>&1
cat nifty_output.txt

echo "Running Live Edge Finder Integration Check..."
python3 Live_Edge_Finder.py > finder_output.txt 2>&1
cat finder_output.txt
