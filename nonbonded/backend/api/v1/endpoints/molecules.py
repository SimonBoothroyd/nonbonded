from fastapi import APIRouter
from starlette.responses import Response

from nonbonded.library.models.datasets import Substance
from nonbonded.library.utilities.molecules import smiles_to_image

router = APIRouter()


@router.get("/image/{smiles}")
async def get_molecule_image(smiles):

    substance = Substance.from_url_string(smiles)

    svg_content = smiles_to_image(substance.smiles)
    svg_response = Response(svg_content, media_type="image/svg+xml")

    return svg_response
