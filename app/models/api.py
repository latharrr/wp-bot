
from pydantic import BaseModel, Field


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


class MeResponse(BaseModel):
    username: str
    role: str
    allowed_features: list[str]


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8)
    allowed_features: list[str] = []


class UpdateUserFeaturesRequest(BaseModel):
    allowed_features: list[str]


class ManualOptInBody(BaseModel):
    reason: str | None = None


class BulkOptInBody(BaseModel):
    phones: list[str]


class BulkGroupActionBody(BaseModel):
    group_jids: list[str]


class AddKeywordsBody(BaseModel):
    keywords: list[str]


class SetKeywordsEnabledBody(BaseModel):
    keywords: list[str]
    enabled: bool


class DeleteKeywordsBody(BaseModel):
    keywords: list[str]
