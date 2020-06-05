import functools
import urllib.parse


@functools.lru_cache(1000)
def smiles_to_image(smiles: str):

    from rdkit import Chem
    from rdkit.Chem.Draw import rdMolDraw2D

    smiles_parser = Chem.rdmolfiles.SmilesParserParams()
    smiles_parser.removeHs = False

    rdkit_molecule = Chem.MolFromSmiles(smiles, smiles_parser)

    if not rdkit_molecule.GetNumConformers():
        Chem.rdDepictor.Compute2DCoords(rdkit_molecule)

    drawer = rdMolDraw2D.MolDraw2DSVG(200, 200, 150, 200)
    drawer.drawOptions().padding = 0.05

    drawer.SetOffset(25, 0)
    drawer.DrawMolecule(rdkit_molecule)

    drawer.FinishDrawing()

    svg = drawer.GetDrawingText()
    return svg


def smiles_to_url_string(smiles):
    return urllib.parse.quote(smiles)


def url_string_to_smiles(url_string):
    return urllib.parse.unquote(url_string)


@functools.lru_cache(1000)
def find_smirks_matches(smiles_pattern, *smirks_patterns):
    """Determines which (if any) of the specified smirks match the specified
    molecule.

    Parameters
    ----------
    smiles_pattern: str
        The SMILES representation to try and match against.
    smirks_patterns: str
        The smirks patterns to try and match.

    Returns
    -------
    list of str
        The matched smirks patterns.
    """

    from openforcefield.topology import Molecule

    if len(smirks_patterns) == 0:
        return []

    molecule = Molecule.from_smiles(smiles_pattern, allow_undefined_stereo=True)

    matches = [
        smirks
        for smirks in smirks_patterns
        if len(molecule.chemical_environment_matches(smirks)) > 0
    ]

    return matches
