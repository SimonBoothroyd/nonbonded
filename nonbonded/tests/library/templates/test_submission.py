import pytest

from nonbonded.library.templates.submission import Submission, SubmissionTemplate
from nonbonded.library.utilities.exceptions import UnrecognisedKwargsError


@pytest.mark.parametrize(
    "template_name, expected",
    [
        (
            "submit_lilac.txt",
            "\n".join(
                [
                    "#!/bin/bash",
                    "#",
                    "# Set the job name and wall time / memory limit",
                    "#BSUB -J test",
                    "#BSUB -W 12:34",
                    "#BSUB -M 1",
                    "#",
                    "# Set the output and error output paths.",
                    "#BSUB -o  %J.o",
                    "#BSUB -e  %J.e",
                    "#",
                    "# Set any gpu options.",
                    "#BSUB -q gpuqueue",
                    "#BSUB -gpu num=1:j_exclusive=yes:mode=shared:mps=no:",
                    "",
                    ". ~/.bashrc",
                    "",
                    "# Use the right conda environment",
                    "conda activate test-env",
                    "conda env export > conda_env.yaml",
                    "",
                    "# Run the commands",
                    "test command 1",
                    "test command 2",
                    "",
                ]
            ),
        )
    ],
)
def test_submission_template(template_name, expected):

    content = SubmissionTemplate.generate(
        template_name,
        Submission(
            job_name="test",
            wall_clock_limit="12:34",
            max_memory=1,
            gpu=True,
            environment_name="test-env",
            commands=["test command 1", "test command 2"],
        ),
    )

    assert content == expected


def test_invalid_option():

    with pytest.raises(UnrecognisedKwargsError) as error_info:

        SubmissionTemplate.generate(
            "submit_lilac.txt",
            Submission(
                job_name="test",
                wall_clock_limit="12:34",
                max_memory=1,
                gpu=True,
                environment_name="test-env",
                commands=["test command 1", "test command 2"],
            ),
            invalid_kwarg_1=1,
        )

    assert "invalid_kwarg_1" in error_info.value.kwarg_names
