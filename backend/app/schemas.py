from pydantic import BaseModel, Field


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=40, pattern=r"^[A-Za-z0-9_\-]+$")
    password: str = Field(min_length=6, max_length=100)


class TokenOut(BaseModel):
    token: str
    username: str


class CommentIn(BaseModel):
    file: str
    line: int = Field(ge=1)
    text: str = Field(min_length=1, max_length=1000)


class SubmitIn(BaseModel):
    comments: list[CommentIn] = Field(max_length=40)
    use_ai: bool = True
