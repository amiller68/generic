from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from typing import Dict, Any

templates = Jinja2Templates(directory="templates")


class PageResponse:
    """Helper for HTMX-aware page responses"""

    def __init__(self, template: str, layout: str = "layouts/app.html"):
        self.template = template
        self.layout = layout

    def render(self, request: Request, data: Dict[str, Any]) -> HTMLResponse:
        template_data = {"request": request, **data}

        # HTMX navigation - return just the content
        if request.headers.get("HX-Request"):
            return templates.TemplateResponse(self.template, template_data)

        # Full page - render content then wrap in layout
        content_template = templates.get_template(self.template)
        content_html = content_template.render(template_data)

        template_data["content"] = content_html
        return templates.TemplateResponse(self.layout, template_data)
