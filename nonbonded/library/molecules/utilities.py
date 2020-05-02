import functools

from cmiles.utils import load_molecule
from rdkit.Chem import rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D


@functools.lru_cache(500)
def smiles_to_image(smiles_tuple):

    rdkit_molecules = [
        load_molecule(smiles, toolkit="rdkit") for smiles in smiles_tuple
    ]

    for rdkit_molecule in rdkit_molecules:

        if not rdkit_molecule.GetNumConformers():
            rdDepictor.Compute2DCoords(rdkit_molecule)

    n_molecules = len(smiles_tuple)

    drawer = rdMolDraw2D.MolDraw2DSVG(n_molecules * 200, 200, 150, 200)
    drawer.drawOptions().padding = 0.05

    for index, rdkit_molecule in enumerate(rdkit_molecules):

        drawer.SetOffset(index * 200 + 25, 0)
        drawer.DrawMolecule(rdkit_molecule)

    drawer.FinishDrawing()

    svg = drawer.GetDrawingText()
    return svg
