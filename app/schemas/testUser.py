from pydantic import BaseModel

class GoogleUser(BaseModel):
    user_id: str
    email: str
    name: str
    verified: bool