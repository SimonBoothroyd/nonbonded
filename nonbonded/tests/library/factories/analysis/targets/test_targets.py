import os

import numpy
from forcebalance.nifty import lp_dump

from nonbonded.library.factories.analysis.targets import TargetAnalysisFactory


def test_read_objective_function(tmpdir):

    # Save an objective function file.
    lp_dump({"X": 1.0}, os.path.join(tmpdir, "objective.p"))

    assert numpy.isclose(TargetAnalysisFactory._read_objective_function(tmpdir), 1.0)
