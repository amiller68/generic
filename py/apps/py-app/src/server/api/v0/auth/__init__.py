from fastapi import APIRouter
from . import whoami

router = APIRouter()

router.add_api_route("/whoami", whoami.handler, methods=["GET"])
