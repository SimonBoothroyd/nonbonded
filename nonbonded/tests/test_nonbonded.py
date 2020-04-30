"""
Unit and regression test for the nonbonded package.
"""

# Import package, test suite, and other packages as needed
import nonbonded
import pytest
import sys

def test_nonbonded_imported():
    """Sample test, will always pass so long as import statement worked"""
    assert "nonbonded" in sys.modules
