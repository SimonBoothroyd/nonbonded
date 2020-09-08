import errno
import os
from contextlib import contextmanager
from tempfile import TemporaryDirectory
from typing import Optional


def get_data_file_path(relative_path: str) -> str:
    """Get the full path to one of the files included in this packages data
    directory.

    In the source distribution these files are located in ``nonbonded/data/``.
    On installation, they're moved to somewhere in the user's python
    site-packages directory.

    Parameters
    ----------
    relative_path
        The relative path of the file to load.

    Returns
    -------
        The absolute path to the file.

    Raises
    ------
    FileNotFoundError
    """

    from pkg_resources import resource_filename

    file_path = resource_filename("nonbonded", os.path.join("data", relative_path))

    if not os.path.exists(file_path):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file_path)

    return file_path


@contextmanager
def temporary_cd(directory_path: Optional[str] = None):
    """Temporarily move the current working directory to the path
    specified. If no path is given, a temporary directory will be
    created, moved into, and then destroyed when the context manager
    is closed.

    Parameters
    ----------
    directory_path: str, optional

    Returns
    -------

    """

    if directory_path is not None and len(directory_path) == 0:
        yield
        return

    old_directory = os.getcwd()

    try:

        if directory_path is None:

            with TemporaryDirectory() as new_directory:
                os.chdir(new_directory)
                yield

        else:

            os.chdir(directory_path)
            yield

    finally:
        os.chdir(old_directory)
