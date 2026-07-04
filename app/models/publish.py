from pydantic import BaseModel


class PublishResult(BaseModel):
    post_id: str
    web_url: str
    status: str
