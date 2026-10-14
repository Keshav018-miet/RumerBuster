import sys
import os

# Ensure the root project directory is on the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

# Vercel serverless functions look for `app`
if __name__ == "__main__":
    app.run()
