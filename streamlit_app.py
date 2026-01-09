"""
Streamlit Cloud entry point.

This file exists to ensure proper Python path configuration
when deployed to Streamlit Cloud.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import and run the main app
from app.main import main

if __name__ == "__main__":
    main()
else:
    # Streamlit imports the module rather than running it
    main()
