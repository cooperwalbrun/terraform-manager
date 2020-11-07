import sys

import setuptools
from pkg_resources import VersionConflict, require

try:
    require("setuptools>=38.3")
except VersionConflict:
    print("Error: setuptools version is too old (lower than v38.3)!")
    sys.exit(1)

# The if __name__ == "__main__" condition that is created by default by PyScaffold was removed so
# that pip-compile commands work properly. Beware issuing PyScaffold update commands because
# setup.py will probably be overlaid by PyScaffold during that process.
setuptools.setup(use_pyscaffold=True)
