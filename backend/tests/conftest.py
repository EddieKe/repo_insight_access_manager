import os
import sys

# Add the parent directory to the path so tests can import from the backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))