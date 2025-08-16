import os
import sys
import subprocess

# Path to your actual script
script_path = os.path.join(os.path.dirname(__file__), "captive_protal.py")

# Run with sudo
try:
    subprocess.run(["sudo", sys.executable, script_path] + sys.argv[1:], check=True)
except subprocess.CalledProcessError as e:
    print(f"Error while running script: {e}")
