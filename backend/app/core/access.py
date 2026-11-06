"""Request identity supplied by the authentication boundary."""

from fastapi import HTTPException, Request


def current_user(request: Request):
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Silakan masuk terlebih dahulu.")
    return user
