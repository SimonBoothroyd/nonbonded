import functools
import logging
from typing import List, Optional, Union

from nonbonded.library.models.datasets import Component
from nonbonded.library.utilities.environments import ChemicalEnvironment

logger = logging.getLogger(__name__)


def checkmol_code_to_environment(checkmol_code) -> ChemicalEnvironment:

    checkmol_code_map = {
        "000": ChemicalEnvironment.Alkane,
        "001": ChemicalEnvironment.Cation,
        "002": ChemicalEnvironment.Anion,
        "003": ChemicalEnvironment.Carbonyl,
        "004": ChemicalEnvironment.Aldehyde,
        "005": ChemicalEnvironment.Ketone,
        "006": ChemicalEnvironment.Thiocarbonyl,
        "007": ChemicalEnvironment.Thioaldehyde,
        "008": ChemicalEnvironment.Thioketone,
        "009": ChemicalEnvironment.Imine,
        "010": ChemicalEnvironment.Hydrazone,
        "011": ChemicalEnvironment.Semicarbazone,
        "012": ChemicalEnvironment.Thiosemicarbazone,
        "013": ChemicalEnvironment.Oxime,
        "014": ChemicalEnvironment.OximeEther,
        "015": ChemicalEnvironment.Ketene,
        "016": ChemicalEnvironment.KeteneAcetalDeriv,
        "017": ChemicalEnvironment.CarbonylHydrate,
        "018": ChemicalEnvironment.Hemiacetal,
        "019": ChemicalEnvironment.Acetal,
        "020": ChemicalEnvironment.Hemiaminal,
        "021": ChemicalEnvironment.Aminal,
        "022": ChemicalEnvironment.Thiohemiaminal,
        "023": ChemicalEnvironment.Thioacetal,
        "024": ChemicalEnvironment.Enamine,
        "025": ChemicalEnvironment.Enol,
        "026": ChemicalEnvironment.Enolether,
        "027": ChemicalEnvironment.Hydroxy,
        "028": ChemicalEnvironment.Alcohol,
        "029": ChemicalEnvironment.PrimaryAlcohol,
        "030": ChemicalEnvironment.SecondaryAlcohol,
        "031": ChemicalEnvironment.TertiaryAlcohol,
        "032": ChemicalEnvironment.Diol_1_2,
        "033": ChemicalEnvironment.Aminoalcohol_1_2,
        "034": ChemicalEnvironment.Phenol,
        "035": ChemicalEnvironment.Diphenol_1_2,
        "036": ChemicalEnvironment.Enediol,
        "037": ChemicalEnvironment.Ether,
        "038": ChemicalEnvironment.Dialkylether,
        "039": ChemicalEnvironment.Alkylarylether,
        "040": ChemicalEnvironment.Diarylether,
        "041": ChemicalEnvironment.Thioether,
        "042": ChemicalEnvironment.Disulfide,
        "043": ChemicalEnvironment.Peroxide,
        "044": ChemicalEnvironment.Hydroperoxide,
        "045": ChemicalEnvironment.Hydrazine,
        "046": ChemicalEnvironment.Hydroxylamine,
        "047": ChemicalEnvironment.Amine,
        "048": ChemicalEnvironment.PrimaryAmine,
        "049": ChemicalEnvironment.PrimaryAliphAmine,
        "050": ChemicalEnvironment.PrimaryAromAmine,
        "051": ChemicalEnvironment.SecondaryAmine,
        "052": ChemicalEnvironment.SecondaryAliphAmine,
        "053": ChemicalEnvironment.SecondaryMixedAmine,
        "054": ChemicalEnvironment.SecondaryAromAmine,
        "055": ChemicalEnvironment.TertiaryAmine,
        "056": ChemicalEnvironment.TertiaryAliphAmine,
        "057": ChemicalEnvironment.TertiaryMixedAmine,
        "058": ChemicalEnvironment.TertiaryAromAmine,
        "059": ChemicalEnvironment.QuartAmmonium,
        "060": ChemicalEnvironment.NOxide,
        "061": ChemicalEnvironment.HalogenDeriv,
        "062": ChemicalEnvironment.AlkylHalide,
        "063": ChemicalEnvironment.AlkylFluoride,
        "064": ChemicalEnvironment.AlkylChloride,
        "065": ChemicalEnvironment.AlkylBromide,
        "066": ChemicalEnvironment.AlkylIodide,
        "067": ChemicalEnvironment.ArylHalide,
        "068": ChemicalEnvironment.ArylFluoride,
        "069": ChemicalEnvironment.ArylChloride,
        "070": ChemicalEnvironment.ArylBromide,
        "071": ChemicalEnvironment.ArylIodide,
        "072": ChemicalEnvironment.Organometallic,
        "073": ChemicalEnvironment.Organolithium,
        "074": ChemicalEnvironment.Organomagnesium,
        "075": ChemicalEnvironment.CarboxylicAcidDeriv,
        "076": ChemicalEnvironment.CarboxylicAcid,
        "077": ChemicalEnvironment.CarboxylicAcidSalt,
        "078": ChemicalEnvironment.CarboxylicAcidEster,
        "079": ChemicalEnvironment.Lactone,
        "080": ChemicalEnvironment.CarboxylicAcidAmide,
        "081": ChemicalEnvironment.CarboxylicAcidPrimaryAmide,
        "082": ChemicalEnvironment.CarboxylicAcidSecondaryAmide,
        "083": ChemicalEnvironment.CarboxylicAcidTertiaryAmide,
        "084": ChemicalEnvironment.Lactam,
        "085": ChemicalEnvironment.CarboxylicAcidHydrazide,
        "086": ChemicalEnvironment.CarboxylicAcidAzide,
        "087": ChemicalEnvironment.HydroxamicAcid,
        "088": ChemicalEnvironment.CarboxylicAcidAmidine,
        "089": ChemicalEnvironment.CarboxylicAcidAmidrazone,
        "090": ChemicalEnvironment.Nitrile,
        "091": ChemicalEnvironment.AcylHalide,
        "092": ChemicalEnvironment.AcylFluoride,
        "093": ChemicalEnvironment.AcylChloride,
        "094": ChemicalEnvironment.AcylBromide,
        "095": ChemicalEnvironment.AcylIodide,
        "096": ChemicalEnvironment.AcylCyanide,
        "097": ChemicalEnvironment.ImidoEster,
        "098": ChemicalEnvironment.ImidoylHalide,
        "099": ChemicalEnvironment.ThiocarboxylicAcidDeriv,
        "100": ChemicalEnvironment.ThiocarboxylicAcid,
        "101": ChemicalEnvironment.ThiocarboxylicAcidEster,
        "102": ChemicalEnvironment.Thiolactone,
        "103": ChemicalEnvironment.ThiocarboxylicAcidAmide,
        "104": ChemicalEnvironment.Thiolactam,
        "105": ChemicalEnvironment.ImidoThioester,
        "106": ChemicalEnvironment.Oxohetarene,
        "107": ChemicalEnvironment.Thioxohetarene,
        "108": ChemicalEnvironment.Iminohetarene,
        "109": ChemicalEnvironment.OrthocarboxylicAcidDeriv,
        "110": ChemicalEnvironment.CarboxylicAcidOrthoester,
        "111": ChemicalEnvironment.CarboxylicAcidAmideAcetal,
        "112": ChemicalEnvironment.CarboxylicAcidAnhydride,
        "113": ChemicalEnvironment.CarboxylicAcidImide,
        "114": ChemicalEnvironment.CarboxylicAcidUnsubstImide,
        "115": ChemicalEnvironment.CarboxylicAcidSubstImide,
        "116": ChemicalEnvironment.Co2Deriv,
        "117": ChemicalEnvironment.CarbonicAcidDeriv,
        "118": ChemicalEnvironment.CarbonicAcidMonoester,
        "119": ChemicalEnvironment.CarbonicAcidDiester,
        "120": ChemicalEnvironment.CarbonicAcidEsterHalide,
        "121": ChemicalEnvironment.ThiocarbonicAcidDeriv,
        "122": ChemicalEnvironment.ThiocarbonicAcidMonoester,
        "123": ChemicalEnvironment.ThiocarbonicAcidDiester,
        "124": ChemicalEnvironment.ThiocarbonicAcidEsterHalide,
        "125": ChemicalEnvironment.CarbamicAcidDeriv,
        "126": ChemicalEnvironment.CarbamicAcid,
        "127": ChemicalEnvironment.CarbamicAcidEster,
        "128": ChemicalEnvironment.CarbamicAcidHalide,
        "129": ChemicalEnvironment.ThiocarbamicAcidDeriv,
        "130": ChemicalEnvironment.ThiocarbamicAcid,
        "131": ChemicalEnvironment.ThiocarbamicAcidEster,
        "132": ChemicalEnvironment.ThiocarbamicAcidHalide,
        "133": ChemicalEnvironment.Urea,
        "134": ChemicalEnvironment.Isourea,
        "135": ChemicalEnvironment.Thiourea,
        "136": ChemicalEnvironment.Isothiourea,
        "137": ChemicalEnvironment.Guanidine,
        "138": ChemicalEnvironment.Semicarbazide,
        "139": ChemicalEnvironment.Thiosemicarbazide,
        "140": ChemicalEnvironment.Azide,
        "141": ChemicalEnvironment.AzoCompound,
        "142": ChemicalEnvironment.DiazoniumSalt,
        "143": ChemicalEnvironment.Isonitrile,
        "144": ChemicalEnvironment.Cyanate,
        "145": ChemicalEnvironment.Isocyanate,
        "146": ChemicalEnvironment.Thiocyanate,
        "147": ChemicalEnvironment.Isothiocyanate,
        "148": ChemicalEnvironment.Carbodiimide,
        "149": ChemicalEnvironment.NitrosoCompound,
        "150": ChemicalEnvironment.NitroCompound,
        "151": ChemicalEnvironment.Nitrite,
        "152": ChemicalEnvironment.Nitrate,
        "153": ChemicalEnvironment.SulfuricAcidDeriv,
        "154": ChemicalEnvironment.SulfuricAcid,
        "155": ChemicalEnvironment.SulfuricAcidMonoester,
        "156": ChemicalEnvironment.SulfuricAcidDiester,
        "157": ChemicalEnvironment.SulfuricAcidAmideEster,
        "158": ChemicalEnvironment.SulfuricAcidAmide,
        "159": ChemicalEnvironment.SulfuricAcidDiamide,
        "160": ChemicalEnvironment.SulfurylHalide,
        "161": ChemicalEnvironment.SulfonicAcidDeriv,
        "162": ChemicalEnvironment.SulfonicAcid,
        "163": ChemicalEnvironment.SulfonicAcidEster,
        "164": ChemicalEnvironment.Sulfonamide,
        "165": ChemicalEnvironment.SulfonylHalide,
        "166": ChemicalEnvironment.Sulfone,
        "167": ChemicalEnvironment.Sulfoxide,
        "168": ChemicalEnvironment.SulfinicAcidDeriv,
        "169": ChemicalEnvironment.SulfinicAcid,
        "170": ChemicalEnvironment.SulfinicAcidEster,
        "171": ChemicalEnvironment.SulfinicAcidHalide,
        "172": ChemicalEnvironment.SulfinicAcidAmide,
        "173": ChemicalEnvironment.SulfenicAcidDeriv,
        "174": ChemicalEnvironment.SulfenicAcid,
        "175": ChemicalEnvironment.SulfenicAcidEster,
        "176": ChemicalEnvironment.SulfenicAcidHalide,
        "177": ChemicalEnvironment.SulfenicAcidAmide,
        "178": ChemicalEnvironment.Thiol,
        "179": ChemicalEnvironment.Alkylthiol,
        "180": ChemicalEnvironment.Arylthiol,
        "181": ChemicalEnvironment.PhosphoricAcidDeriv,
        "182": ChemicalEnvironment.PhosphoricAcid,
        "183": ChemicalEnvironment.PhosphoricAcidEster,
        "184": ChemicalEnvironment.PhosphoricAcidHalide,
        "185": ChemicalEnvironment.PhosphoricAcidAmide,
        "186": ChemicalEnvironment.ThiophosphoricAcidDeriv,
        "187": ChemicalEnvironment.ThiophosphoricAcid,
        "188": ChemicalEnvironment.ThiophosphoricAcidEster,
        "189": ChemicalEnvironment.ThiophosphoricAcidHalide,
        "190": ChemicalEnvironment.ThiophosphoricAcidAmide,
        "191": ChemicalEnvironment.PhosphonicAcidDeriv,
        "192": ChemicalEnvironment.PhosphonicAcid,
        "193": ChemicalEnvironment.PhosphonicAcidEster,
        "194": ChemicalEnvironment.Phosphine,
        "195": ChemicalEnvironment.Phosphinoxide,
        "196": ChemicalEnvironment.BoronicAcidDeriv,
        "197": ChemicalEnvironment.BoronicAcid,
        "198": ChemicalEnvironment.BoronicAcidEster,
        "199": ChemicalEnvironment.Alkene,
        "200": ChemicalEnvironment.Alkyne,
        "201": ChemicalEnvironment.Aromatic,
        "202": ChemicalEnvironment.Heterocycle,
        "203": ChemicalEnvironment.AlphaAminoacid,
        "204": ChemicalEnvironment.AlphaHydroxyacid,
    }
    return checkmol_code_map[checkmol_code]


@functools.lru_cache(1000)
def analyse_functional_groups(smiles):
    """Employs checkmol to determine which chemical moieties
    are encoded by a given smiles pattern.

    Notes
    -----
    See https://homepage.univie.ac.at/norbert.haider/cheminf/fgtable.pdf
    for information about the group numbers (i.e moiety types).

    Parameters
    ----------
    smiles: str
        The smiles pattern to examine.

    Returns
    -------
    dict of ChemicalEnvironment and int, optional
        A dictionary where each key corresponds to the `checkmol` defined group
        number, and each value if the number of instances of that moiety. If
        `checkmol` did not execute correctly, returns None.
    """
    import shutil
    import subprocess
    import tempfile

    from openforcefield.topology import Molecule

    if smiles == "O" or smiles == "[H]O[H]":
        return {ChemicalEnvironment.Aqueous: 1}
    if smiles == "N":
        return {ChemicalEnvironment.Amine: 1}

    # Make sure the checkmol utility has been installed separately.
    if shutil.which("checkmol") is None:

        raise FileNotFoundError(
            "checkmol was not found on this machine. Visit http://merian.pch.univie.ac."
            "at/~nhaider/cheminf/cmmm.html to obtain it."
        )

    openff_molecule: Molecule = Molecule.from_smiles(
        smiles, allow_undefined_stereo=True
    )

    # Save the smile pattern out as an SDF file, ready to use as input to checkmol.
    with tempfile.NamedTemporaryFile(suffix=".sdf") as file:

        openff_molecule.to_file(file.name, "SDF")

        # Execute checkmol.
        try:

            result = subprocess.check_output(
                ["checkmol", "-p", file.name],
                stderr=subprocess.STDOUT,
            ).decode()

        except subprocess.CalledProcessError:
            result = None

    if result is None:
        return None
    elif len(result) == 0:
        return {ChemicalEnvironment.Alkane: 1}

    groups = {}

    for group in result.splitlines():

        group_code, group_count, _ = group.split(":")

        group_environment = checkmol_code_to_environment(group_code[1:])
        groups[group_environment] = int(group_count)

    return groups


def components_to_category(
    components: Union[List[str], List[Component]],
    environments: List[ChemicalEnvironment],
) -> Optional[str]:
    """Attempts to assign a category to a list of components (or SMILES patterns)
    based off of the chemical environments that they contain.

    Parameters
    ----------
    components
        The components to categorize.
    environments
        The environments to base the category off of.
    """

    import numpy

    if len(environments) == 0:
        return None

    if not all(
        isinstance(component, Component) for component in components
    ) and not all(isinstance(component, str) for component in components):

        raise TypeError(
            "The components must either all be `Component` objects or all SMILES "
            "patterns."
        )

    components = [
        component
        if isinstance(component, Component)
        else Component(smiles=component, mole_fraction=1.0)
        for component in components
    ]

    sorted_components = [*sorted(components, key=lambda x: x.smiles)]
    assigned_environments = []

    for component in sorted_components:

        # Determine which environments are present in this component.
        component_environments = analyse_functional_groups(component.smiles)
        # Filter out any environments which we are not interested in.
        component_environments = {
            x: y for x, y in component_environments.items() if x in environments
        }

        if len(component_environments) == 0:
            logger.info(
                f"The substance with SMILES={[x.smiles for x in components]} "
                f"could not be assigned a category. More than likely one or more "
                f"of the components contains only environments which were not "
                f"marked for analysis. It will be assigned a category of "
                f"'Uncategorized' instead."
            )
            return "Uncategorized"

        # Try to find the environment which appears the most times in a molecule.
        # We sort the environments to try and make the case where multiple
        # environments appear with the same frequency deterministic.
        component_environment_keys = sorted(
            component_environments.keys(), key=lambda x: x.value
        )

        most_common_environment = "None"
        most_occurrences = -1

        for key in component_environment_keys:

            if component_environments[key] > most_occurrences:
                most_common_environment = key.value
                most_occurrences = component_environments[key]

        assigned_environments.append(most_common_environment)

    # Sort the assignments to try and make the categories deterministic.
    sorted_assigned_environments = [*sorted(assigned_environments)]
    category = ""

    for index, assigned_environment in enumerate(sorted_assigned_environments):

        if index == 0:
            category = assigned_environment
            continue

        previous_environment = sorted_assigned_environments[index - 1]

        previous_component = sorted_components[
            assigned_environments.index(previous_environment)
        ]
        current_component = sorted_components[
            assigned_environments.index(assigned_environment)
        ]

        if numpy.isclose(
            previous_component.mole_fraction, 1.0 / len(components), rtol=0.1
        ) and numpy.isclose(
            current_component.mole_fraction, 1.0 / len(components), rtol=0.1
        ):
            category = f"{category} ~ {assigned_environment}"

        elif previous_component.mole_fraction < current_component.mole_fraction:
            category = f"{category} < {assigned_environment}"
        else:
            category = f"{category} > {assigned_environment}"

    return category
