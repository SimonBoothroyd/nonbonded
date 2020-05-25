from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette import status

from nonbonded.backend.core.config import settings

ACCESS_TOKEN_NAME = "access_token"

acces_token_header = APIKeyHeader(name=ACCESS_TOKEN_NAME)


def check_access_token(access_token: str = Security(acces_token_header)):

    if access_token == settings.ACCESS_TOKEN:
        return access_token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token.",
    )
