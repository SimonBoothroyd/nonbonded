from fastapi import APIRouter, HTTPException
from starlette.responses import Response

from nonbonded.library.utilities.molecules import smiles_to_image, url_string_to_smiles

router = APIRouter()


@router.get("/{smiles}/image")
async def get_molecule_image(smiles: str):

    smiles = url_string_to_smiles(smiles)

    try:
        svg_content = smiles_to_image(smiles)
    except ImportError:
        raise HTTPException(
            501,
            "RDKit could not be found on the server. Make sure it is installed to use "
            "this endpoint.",
        )

    svg_response = Response(svg_content, media_type="image/svg+xml")

    return svg_response
