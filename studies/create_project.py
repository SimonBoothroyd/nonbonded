import lorem
import pandas
import requests

from nonbonded.library.data.pandas import data_frame_to_summary
from nonbonded.library.models.data import (
    TargetDataSet,
    TargetProperty,
    StatePoint,
    SubstanceType, PropertyType,
)
from nonbonded.library.models.environments import ChemicalEnvironment
from nonbonded.library.models.project import Author, Optimization, Project, Study


def define_target_data_set():

    # Define the target properties
    pure_rho = TargetProperty(
        property_type=PropertyType(
            property_class="Density", substance_type=SubstanceType.Pure
        ),
        target_states=[
            StatePoint(temperature=298.15, pressure=101.325, mole_fractions=(1.0,))
        ],
    )
    pure_h_vap = TargetProperty(
        property_type=PropertyType(
            property_class="EnthalpyOfVaporization", substance_type=SubstanceType.Pure
        ),
        composition=SubstanceType.Pure,
        target_states=[
            StatePoint(temperature=298.15, pressure=101.325, mole_fractions=(1.0,))
        ],
    )

    # Define the alcohol-ester-acid study.
    target_data_set = TargetDataSet(
        target_properties=[pure_rho, pure_h_vap],
        chemical_environments=[
            ChemicalEnvironment.CarboxylicAcid,
            ChemicalEnvironment.Hydroxy,
            ChemicalEnvironment.CarboxylicAcidEster,
        ],
    )

    return target_data_set


def main():
    target_data_set = define_target_data_set()

    study = Study(
        identifier="alcohol_ester",
        title="Alcohol + Ester",
        description="\n".join([lorem.paragraph()] * 3),
        optimizations=[
            Optimization(
                title="rho_x_h_vap",
                description="\n".join([lorem.paragraph()] * 1),
                training_set=target_data_set,
            )
        ],
        test_set=target_data_set,
    )

    # Define the main project.
    project = Project(
        identifier="binary_mixture",
        title="Binary Mixture Feasibility Study",
        abstract="\n".join([lorem.paragraph()] * 4),
        authors=[
            Author(
                name="Simon Boothroyd",
                email="simon.boothroyd@colorado.edu",
                institute="University of Colorado Boulder",
            ),
            Author(
                name="Owen Madin",
                email="owen.madin@colorado.edu",
                institute="University of Colorado Boulder",
            ),
        ],
        studies=[study],
    )

    requests.post(url="http://127.0.0.1:5000/projects/", data=project.json())

    test_set_summary = data_frame_to_summary(pandas.read_csv("test_set.csv"))
    requests.post(
        url=(
            f"http://127.0.0.1:5000/projects/"
            f"{project.identifier}/{study.identifier}/test/summary"
        ),
        data=test_set_summary.json()
    )


if __name__ == "__main__":
    main()
