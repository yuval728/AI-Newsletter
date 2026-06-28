from pydantic import BaseModel


class ImageAsset(BaseModel):
    file_path: str
    prompt: str
    width: int
    height: int
    size_bytes: int