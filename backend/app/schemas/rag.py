from pydantic import BaseModel, Field


class RagSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    crop: str | None = None
    topic: str | None = None
    k: int = Field(default=5, ge=1, le=20)


class RagChunkOut(BaseModel):
    content: str
    crop: str | None
    topic: str | None
    section_heading: str | None
    page_number: int | None
    source_title: str
    similarity: float


class RagSearchResponse(BaseModel):
    query: str
    results: list[RagChunkOut]


class RagAskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    k: int = Field(default=5, ge=1, le=20)


class RagAskResponse(BaseModel):
    query: str
    answer: str
    sources: list[RagChunkOut]
