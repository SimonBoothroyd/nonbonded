import lorem
import pandas
import requests

from nonbonded.library.data.pandas import data_frame_to_summary
from nonbonded.library.models.datasets import StatePoint, TargetDataSet, TargetProperty
from nonbonded.library.models.environments import ChemicalEnvironment
from nonbonded.library.models.forcefield import SmirnoffParameter
from nonbonded.library.models.project import Author, Optimization, Project, Study


def define_alcohol_study():

    # Define the environments of interest.
    train_environments = [
        ChemicalEnvironment.CarboxylicAcid,
        ChemicalEnvironment.Hydroxy,
        ChemicalEnvironment.CarboxylicAcidEster,
    ]
    test_environments = [*train_environments, ChemicalEnvironment.Ether]

    # Define the parameters to be optimized.
    vdw_smirks_to_optimize = [
        "[#1:1]-[#6X4]",
        "[#6:1]",
        "[#6X4:1]",
        "[#8:1]",
        "[#8X2H0+0:1]",
        "[#8X2H1+0:1]",
    ]

    parameters_to_optimize = [
        *[
            SmirnoffParameter(handler_type="vdW", attribute_name="epsilon", smirks=x)
            for x in vdw_smirks_to_optimize
        ],
        *[
            SmirnoffParameter(handler_type="vdW", attribute_name="rmin_half", smirks=x)
            for x in vdw_smirks_to_optimize
        ],
    ]

    # Define the optimization denominators.
    denominators = {
        "Density": "0.0482 g / ml",
        "EnthalpyOfMixing": "1.594 kJ / mol",
        "EnthalpyOfVaporization": "25.683 kJ / mol",
        "ExcessMolarVolume": "0.392 cm ** 3 / mol",
    }

    # Define the target states.
    pure_states = [
        StatePoint(temperature=298.15, pressure=101.325, mole_fractions=(1.0,))
    ]
    binary_states = [
        StatePoint(temperature=298.15, pressure=101.325, mole_fractions=(0.25, 0.75)),
        StatePoint(temperature=298.15, pressure=101.325, mole_fractions=(0.50, 0.50)),
        StatePoint(temperature=298.15, pressure=101.325, mole_fractions=(0.75, 0.25)),
    ]

    # Define the target properties.
    pure_rho = TargetProperty(
        property_type="Density", n_components=1, target_states=pure_states
    )
    pure_h_vap = TargetProperty(
        property_type="EnthalpyOfVaporization",
        n_components=1,
        target_states=pure_states,
    )
    binary_rho = TargetProperty(
        property_type="Density", n_components=2, target_states=binary_states
    )
    binary_h_mix = TargetProperty(
            property_type="EnthalpyOfMixing",
            n_components=2,
            target_states=binary_states,
    )
    v_excess = TargetProperty(
        property_type="ExcessMolarVolume", n_components=2, target_states=binary_states
    )

    # Define the optimizations which are part of the study.
    rho_pure_h_vap = TargetDataSet(
        target_properties=[pure_rho, pure_h_vap],
        chemical_environments=train_environments,
    )
    h_mix_rho_x = TargetDataSet(
        target_properties=[binary_h_mix, binary_rho],
        chemical_environments=train_environments,
    )
    h_mix_rho_v_excess = TargetDataSet(
        target_properties=[binary_h_mix, v_excess],
        chemical_environments=train_environments,
    )
    h_mix_rho_x_rho_pure = TargetDataSet(
        target_properties=[binary_h_mix, binary_rho, pure_rho],
        chemical_environments=train_environments,
    )
    h_mix_rho_x_rho_pure_h_vap = TargetDataSet(
        target_properties=[binary_h_mix, binary_rho, pure_rho, pure_h_vap],
        chemical_environments=train_environments,
    )

    test_set = TargetDataSet(
        target_properties=[pure_rho, pure_h_vap, binary_rho, binary_h_mix, v_excess],
        chemical_environments=test_environments,
    )

    study = Study(
        identifier="alcohol_ester",
        title="Alcohol + Ester",
        description="\n".join([lorem.paragraph()] * 3),
        initial_force_field_name="openff-1.0.0.offxml",
        optimizations=[
            Optimization(
                identifier="rho_pure_h_vap",
                title="rho + Hvap",
                description="\n".join([lorem.paragraph()] * 1),
                target_training_set=rho_pure_h_vap,
                parameters_to_train=parameters_to_optimize,
                denominators=denominators,
            ),
            Optimization(
                identifier="h_mix_rho_x",
                title="Hmix(x) + rho(x)",
                description="\n".join([lorem.paragraph()] * 1),
                target_training_set=h_mix_rho_x,
                parameters_to_train=parameters_to_optimize,
                denominators=denominators,
            ),
            Optimization(
                identifier="h_mix_v_excess",
                title="Hmix(x) + Vexcess(x)",
                description="\n".join([lorem.paragraph()] * 1),
                target_training_set=h_mix_rho_v_excess,
                parameters_to_train=parameters_to_optimize,
                denominators=denominators,
            ),
            Optimization(
                identifier="h_mix_rho_x_rho_pure",
                title="Hmix(x) + rho(x) + rho",
                description="\n".join([lorem.paragraph()] * 1),
                target_training_set=h_mix_rho_x_rho_pure,
                parameters_to_train=parameters_to_optimize,
                denominators=denominators,
            ),
            Optimization(
                identifier="h_mix_rho_x_rho_pure_h_vap",
                title="Hmix(x) + rho(x) + rho + Hvap",
                description="\n".join([lorem.paragraph()] * 1),
                target_training_set=h_mix_rho_x_rho_pure_h_vap,
                parameters_to_train=parameters_to_optimize,
                denominators=denominators,
            ),
        ],
        target_test_set=test_set,
    )

    return study


def main():

    study = define_alcohol_study()

    # Define the main project.
    project = Project(
        identifier="binary_mixture",
        title="Binary Mixture Feasibility Study",
        abstract=(
            "In this study we aim to more rigorously understand whether it is more "
            "beneficial to optimize the non-bonded interaction parameters of a force "
            "field on solely pure data, binary mixture data, or a combination of both, "
            "with an emphasis here on density (including density , and excess molar "
            "volume) and enthalpy (including  enthalpy of vaporization  and enthalpy of "
            "mixing) data."
            "\n\n"
            "We anticipate that training a force field on mixture data will improve its "
            "performance at reproducing mixture properties while slightly degrading its "
            "performance on pure properties. Vice versa, we would expect that training "
            "on pure properties would improve its performance on pure properties while "
            "slightly degrading its performance on mixture properties. Here we aim to "
            "identify how much mixture properties improve relative to the degradation "
            "of pure properties when training on mixtures, compared to how much pure "
            "properties improve relative to the degradation of mixture properties when "
            "training on pure properties."
        ),
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

    Project.validate(project)

    requests.post(url="http://127.0.0.1:5000/projects/", data=project.json())

    test_set_summary = data_frame_to_summary(pandas.read_csv("test_set.csv"))
    requests.post(
        url=(
            f"http://127.0.0.1:5000/projects/"
            f"{project.identifier}/studies/{study.identifier}/test/dataset"
        ),
        data=test_set_summary.json(),
    )
    pure_set_summary = data_frame_to_summary(
        pandas.read_csv("rho_pure_h_vap_training_set.csv")
    )
    requests.post(
        url=(
            f"http://127.0.0.1:5000/projects/"
            f"{project.identifier}/studies/{study.identifier}/train/rho_pure_h_vap/dataset"
        ),
        data=pure_set_summary.json(),
    )
    mixture_set_summary = data_frame_to_summary(
        pandas.read_csv("h_mix_rho_x_training_set.csv")
    )
    requests.post(
        url=(
            f"http://127.0.0.1:5000/projects/"
            f"{project.identifier}/studies/{study.identifier}/train/h_mix_rho_x/dataset"
        ),
        data=mixture_set_summary.json(),
    )


if __name__ == "__main__":
    main()
