from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid


class SignupRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class WidgetField(BaseModel):
    name: str
    label: str
    type: str = "text"
    required: bool = False


class WidgetCreate(BaseModel):
    type: str  # signup_form | cta | popover
    title: str
    description: Optional[str] = None
    fields: list[WidgetField] = []
    button_text: str = "Submit"
    display: dict = {}


class WidgetUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    fields: Optional[list[WidgetField]] = None
    button_text: Optional[str] = None
    display: Optional[dict] = None


class WidgetResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    type: str
    title: str
    description: Optional[str]
    fields: list
    button_text: str
    display: dict
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SubmissionCreate(BaseModel):
    widget_id: str
    data: dict
    website: str = ""  # honeypot field -- real users never fill this


class SubmissionResponse(BaseModel):
    id: uuid.UUID
    widget_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True