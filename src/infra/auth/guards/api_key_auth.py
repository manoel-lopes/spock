from fastapi import Depends, HTTPException, Request, status

from src.infra.env.env_service import env_service


async def require_api_key(request: Request) -> None:
    api_key = request.headers.get("x-api-key")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )
    valid_keys = env_service.api_key_list
    if not valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No API keys configured",
        )
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


ApiKeyAuth = Depends(require_api_key)
