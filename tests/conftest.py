import sys
import os

# Get the absolute path to the project's root directory
# __file__ in tests/conftest.py is /home/brooo/10xdevs/steambay/tests/conftest.py
# os.path.dirname(__file__) is /home/brooo/10xdevs/steambay/tests
# os.path.dirname(os.path.dirname(__file__)) is /home/brooo/10xdevs/steambay
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add PROJECT_ROOT to sys.path so that Python can find the 'src' module
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Add src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
# Add frontend/src directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'src'))) 