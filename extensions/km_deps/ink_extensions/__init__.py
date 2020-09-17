import os
import sys

# make sources in "inkex" directories importable from anywhere (e.g., `import inkex`).
# this method of handling dependencies can cause subtle bugs
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__))))

