from pydantic import BaseModel


class getInput(BaseModel):
    user_id: str
    query: str
    groq_api_key: str
