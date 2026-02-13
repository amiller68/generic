import os
from starlette.templating import Jinja2Templates

templates_dir = os.getenv("TEMPLATES_DIR", "templates")
templates = Jinja2Templates(directory=templates_dir)
