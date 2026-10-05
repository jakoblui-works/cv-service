from app.content.selection.models import Selection
from app.core.config import ContactSettings
from app.render.templating import env

TEMPLATE = "cv.tex.j2"


def render_cv(selection: Selection, contact: ContactSettings) -> str:
    unwrapped = {
        "email": contact.email.get_secret_value(),
        "phone": contact.phone.get_secret_value(),
        "linkedin": contact.linkedin.get_secret_value(),
    }

    return env.get_template(TEMPLATE).render(selection=selection, contact=unwrapped)
