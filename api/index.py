import sys
import os

# Ensure the root project directory is on the Python path
basedir = os.path.abspath(os.path.dirname(__file__))
parent_dir = os.path.dirname(basedir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from app import app
