from app.core.config import ContactSettings

EMAIL = "someone@example.com"
PHONE = "+45 12 34 56 78"
LINKEDIN = "https://www.example.com/in/someone"


def test_contact_values_are_hidden_in_repr() -> None:
    contact = ContactSettings.model_validate({"email": EMAIL, "phone": PHONE, "linkedin": LINKEDIN})

    shown = repr(contact)

    for value in (EMAIL, PHONE, LINKEDIN):
        assert value not in shown


def test_contact_values_are_readable_when_unwrapped() -> None:
    contact = ContactSettings.model_validate({"email": EMAIL, "phone": PHONE, "linkedin": LINKEDIN})

    assert contact.email.get_secret_value() == EMAIL
