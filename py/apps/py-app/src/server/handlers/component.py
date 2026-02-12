from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Any, Dict

templates = Jinja2Templates(directory="templates")


class ComponentResponseHandler:
    """Handler that returns JSON or HTML components (never full pages)"""

    def __init__(self, component_template_path: str):
        self.component_template_path = component_template_path

    async def respond(
        self, request: Request, data: BaseModel | Dict[str, Any]
    ) -> HTMLResponse | JSONResponse:
        """Return JSON or HTML component based on Accept header"""

        # Convert BaseModel to dict if needed
        if isinstance(data, BaseModel):
            response_data = data.model_dump()
        else:

            print(f"data: {data}")
            response_data = data

        # Check what type of response to return
        hx_request = request.headers.get("HX-Request", "")

        # JSON response for API calls
        if not hx_request:
            print(f"returning json response: {response_data}")
            return JSONResponse(content=response_data)

        # Always return component for HTML (never full page)
        template_data = {"request": request, **response_data}
        return templates.TemplateResponse(self.component_template_path, template_data)
