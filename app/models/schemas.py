from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any

class VapiCustomer(BaseModel):
    number: Optional[str] = None
    model_config = ConfigDict(extra="ignore")

class VapiCall(BaseModel):
    id: str
    customer: Optional[VapiCustomer] = None
    model_config = ConfigDict(extra="ignore")

class VapiMessage(BaseModel):
    type: str
    call: Optional[VapiCall] = None
    transcript: Optional[str] = None
    model_config = ConfigDict(extra="ignore")

class VapiWebhookRequest(BaseModel):
    message: VapiMessage
    model_config = ConfigDict(extra="ignore")

class VapiWebhookResponse(BaseModel):
    # Standard empty response expected by Vapi (or optionally populated with instructions)
    model_config = ConfigDict(extra="allow")

class ProcessRequest(BaseModel):
    transcript: str
    phone_number: str = "+10000000000"
