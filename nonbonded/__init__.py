"""
nonbonded
Automated optimization and assesment of nonbonded force field parameters
"""

# Handle versioneer
from ._version import get_versions

try:
    versions = get_versions()
    __version__ = versions["version"]
    __git_revision__ = versions["full-revisionid"]
    del get_versions, versions
except ValueError:
    pass
