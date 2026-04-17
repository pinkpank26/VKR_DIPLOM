from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserRegister(BaseModel):
    email: EmailStr
    password: str
    role: str = "marketer"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ContactCreate(BaseModel):
    email: EmailStr
    full_name: str | None = None
    external_client_id: str | None = None
    consent: bool = True


class TemplateCreate(BaseModel):
    name: str
    subject: str
    body: str


class CampaignCreate(BaseModel):
    name: str
    description: str | None = None
    template_id: int


class CampaignOut(BaseModel):
    id: int
    name: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class SendSummary(BaseModel):
    campaign_id: int
    total: int
    sent: int
    failed: int
    skipped: int