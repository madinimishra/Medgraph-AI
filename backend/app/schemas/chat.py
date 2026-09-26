from typing import Any, Optional

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    advanced: bool = False


class DocumentMatch(BaseModel):
    text: str
    metadata: dict[str, Any]
    distance: float


class ChatResponse(BaseModel):
    question: str
    cypher: Optional[str] = None
    graph_results: list[dict[str, Any]] = []
    graph_error: Optional[str] = None
    graph_attempts: Optional[int] = None
    document_matches: list[DocumentMatch] = []
    answer: str
    subquestions: Optional[list[str]] = None
    sub_results: Optional[list[dict[str, Any]]] = None


class CompareRequest(BaseModel):
    question: str


class CompareResponse(BaseModel):
    question: str
    graph_answer: str
    graph_cypher: Optional[str] = None
    graph_results: list[dict[str, Any]] = []
    vector_answer: str
    vector_document_matches: list[DocumentMatch] = []
