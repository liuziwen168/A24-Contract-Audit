from pydantic import BaseModel


class ContractRequest(BaseModel):
    text: str