import abc
import glob
import io
import logging
import os
import tarfile
from multiprocessing import Pool
from typing import Optional, Union

import pandas
import requests
from evaluator.datasets.thermoml import ThermoMLDataSet
from pydantic import Field

from nonbonded.library.curation.components import Component, ComponentSchema
from nonbonded.library.curation.exceptions import InvalidInputException
from nonbonded.library.utilities import cd_to_temporary_directory

logger = logging.getLogger(__name__)


class ProcessThermoMLDataSchema(ComponentSchema, abc.ABC):

    retain_uncertainties: bool = Field(
        True,
        description="If False, all uncertainties in measured property values will be "
        "stripped from the final data set.",
    )

    cache_file_name: Optional[str] = Field(
        None,
        description="The path to the file to store the output of this component "
        "into, and to restore the output of this component from.",
    )


class ProcessThermoMLData(Component[ProcessThermoMLDataSchema]):
    @classmethod
    def _download_data(cls):

        journals = ["JCED", "JCT", "FPE", "TCA", "IJT"]

        for journal in journals:

            # Download the archive of all properties from the journal.
            request = requests.get(
                f"https://trc.nist.gov/ThermoML/{journal}.tgz", stream=True
            )

            # Make sure the request went ok.
            request.raise_for_status()

            # Unzip the files into a new 'ijt_files' directory.
            tar_file = tarfile.open(fileobj=io.BytesIO(request.content))
            tar_file.extractall()

    @classmethod
    def _process_archive(cls, file_path: str) -> pandas.DataFrame:

        # noinspection PyBroadException
        try:
            data_set = ThermoMLDataSet.from_file(file_path)

        except Exception:

            logger.exception(
                f"An exception was raised when processing {file_path}. This file will "
                f"be skipped."
            )
            return pandas.DataFrame()

        # A data set will be none if no 'valid' properties were found
        # in the archive file.
        if data_set is None:
            return pandas.DataFrame()

        data_frame = data_set.to_pandas()
        return data_frame

    @classmethod
    def _apply(
        cls,
        data_frame: pandas.DataFrame,
        schema: ProcessThermoMLDataSchema,
        n_processes,
    ) -> pandas.DataFrame:

        if len(data_frame) > 0:

            raise InvalidInputException(
                "This protocol expects the input data frame to be empty"
            )

        if schema.cache_file_name is not None and os.path.isfile(
            schema.cache_file_name
        ):

            cached_data = pandas.read_csv(schema.cache_file_name)
            return cached_data

        with cd_to_temporary_directory():

            cls._download_data()

            # Get the names of the extracted files
            file_names = glob.glob("*.xml")

            with Pool(processes=n_processes) as pool:
                data_frames = pool.imap(cls._process_archive, file_names)

        data_frame = pandas.concat(data_frames, ignore_index=True, sort=False)

        for header in data_frame:

            if header.find(" Uncertainty ") >= 0 and not schema.retain_uncertainties:
                data_frame = data_frame.drop(header, axis=1)

        if schema.cache_file_name is not None:
            data_frame.to_csv(schema.cache_file_name, index=False)

        return data_frame


ProcessComponentSchema = Union[ProcessThermoMLDataSchema]
