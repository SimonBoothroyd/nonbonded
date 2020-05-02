from typing import List

from pydantic import BaseModel, Field

from nonbonded.library.models.environments import ChemicalEnvironment


class Molecule(BaseModel):

    smiles: str = Field(..., description="The smiles descriptor of the molecule.")

    environments: List[ChemicalEnvironment] = Field(
        ..., description="The chemical environments present in this molecule."
    )
