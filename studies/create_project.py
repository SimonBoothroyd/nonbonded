import requests

from nonbonded.library.models.data import (
    ChemicalEnvironment,
    DataSetDefinition,
    PropertyDefinition,
    StatePoint,
    SubstanceType,
)
from nonbonded.library.models.project import Author, Optimization, Project, Study


def main():
    # Define the common types of properties
    pure_rho = PropertyDefinition(
        property_type="Density",
        composition=SubstanceType.Pure,
        target_states=[
            StatePoint(temperature=298.15, pressure=101.325, mole_fractions=(1.0,))
        ],
    )
    pure_h_vap = PropertyDefinition(
        property_type="EnthalpyOfVaporization",
        composition=SubstanceType.Pure,
        target_states=[
            StatePoint(temperature=298.15, pressure=101.325, mole_fractions=(1.0,))
        ],
    )

    # Define the alcohol-ester-acid study.
    alcohol_ester_data_set = DataSetDefinition(
        property_definitions=[pure_rho, pure_h_vap],
        chemical_environments=[
            ChemicalEnvironment.Caboxylic_acid,
            ChemicalEnvironment.Hydroxy,
            ChemicalEnvironment.Ester,
        ],
    )

    alcohol_ester_study = Study(
        title="Alcohol + Ester",
        description="Lorem ipsum.",
        optimizations=[
            Optimization(
                title="rho_x_h_vap",
                description="Lorem ipsum.",
                training_set=alcohol_ester_data_set,
            )
        ],
        test_set=alcohol_ester_data_set,
    )

    # Define the main project.
    project = Project(
        identifier="binary_mixture",
        title="Binary Mixture Feasability Study",
        abstract="Lorem ipsum.",
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
        studies=[alcohol_ester_study],
    )

    requests.post(url="http://127.0.0.1:5000/projects/", data=project.json())


if __name__ == "__main__":
    main()
