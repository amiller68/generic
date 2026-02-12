from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import RedirectResponse
import datetime
from jose import jwt

from ..deps import app_state

router = APIRouter()


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/app/login")
    response.delete_cookie("session")
    return response


@router.get("/google/login")
async def google_login(state=Depends(app_state)):
    return await state.google_sso.get_login_redirect()


@router.get("/google/callback")
async def google_callback(request: Request, state=Depends(app_state)):
    openid = await state.google_sso.verify_and_process(request)
    if not openid:
        raise HTTPException(status_code=401, detail="Unauthorized")

    expiration = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(
        days=1
    )
    token = jwt.encode(
        {"pld": openid.dict(), "exp": expiration, "sub": openid.id},
        key=state.secrets.service_secret,
        algorithm="HS256",
    )

    response = RedirectResponse(url="/app/dashboard")
    response.set_cookie(key="session", value=token, expires=expiration)
    return response
