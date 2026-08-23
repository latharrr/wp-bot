from typing import Optional

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PairingCodeRequest(BaseModel):
    phone_number: str


class PairingCodeResponse(BaseModel):
    pairing_code: str


class QrCodeResponse(BaseModel):
    qr_data_url: str
    generated_at: int


class ConsentRequestBody(BaseModel):
    prompt_text: Optional[str] = None


class ManualOptInBody(BaseModel):
    reason: Optional[str] = None


class BulkOptInBody(BaseModel):
    phones: list[str]


class BulkGroupActionBody(BaseModel):
    group_jids: list[str]
