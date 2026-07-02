from pydantic import BaseModel, EmailStr


class ContactForm(BaseModel):
    name: str
    phone: str
    email: EmailStr
    suburb: str
    message: str
