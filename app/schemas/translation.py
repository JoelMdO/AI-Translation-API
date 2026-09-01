"""
Pydantic schemas for request/response models
Defines the structure of data that comes in and goes out of the API
"""
from typing import ClassVar, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TranslationRequest(BaseModel):
    """Request schema for translation endpoint"""
    title: str = Field(..., description="Title text to translate")
    body: str = Field(..., description="Body text to translate") 
    section: str = Field(..., description="Section text to translate")
    target_language: str = Field(default="Spanish", description="Target language for translation")
    model: str = Field(default="llama3.2", description="Ollama model to use")


class TranslatedSegment(BaseModel):

    id: int = Field(..., description="Stable segment identifier")
    tag: str | None = Field(default=None, description="Source HTML tag")
    text: Optional[str] | None = Field(default=None, description="Translated text, when present")
    src: Optional[str]  | None = Field(default=None, description="Image source URL")
    alt: Optional[str]  | None = Field(default=None, description="Image alternative text")
    href: Optional[str]  | None = Field(default=None, description="Anchor destination URL")

    @field_validator("text", "src", "alt", "href", mode="before")
    @classmethod
    def empty_optional_values_as_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value


class TranslatedText(BaseModel):

    title: str | list[TranslatedSegment] = Field(..., description="Translated title")
    body: str | list[TranslatedSegment] = Field(..., description="Translated body")
    section: str | list[TranslatedSegment] = Field(..., description="Translated section")


class TranslationResponse(BaseModel):
    """Response schema for translation endpoint"""
    translated_text: TranslatedText = Field(..., description="Translated text segments")
    status: int = Field(..., description="HTTP status code of the translation operation")
    model_used: str = Field(..., description="Model used for translation")
    model_config: ClassVar[ConfigDict] = ConfigDict(protected_namespaces=())



class HealthResponse(BaseModel):
    """Response schema for health check endpoint"""
    status: str = Field(..., description="API status")
    ollama_connected: bool = Field(..., description="Whether Ollama is accessible")
    # chroma_connected: bool = Field(..., description="Whether ChromaDB is accessible")
    api_version: str = Field(..., description="API version")


class TokenRequest(BaseModel):
    """Request schema for token generation (if needed)"""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")

class ResumeRequest(BaseModel):
    """Request schema for resume generation"""
    title: str = Field(..., description="Title of the article for resume")
    body: str = Field(..., description="Body of the article for resume")
    language: str = Field(default="en", description="Language of the article")

class ResumeResponse(BaseModel):
    """Response schema for resume generation"""
    article: str = Field(..., description="Resume of the Article text")
    success: bool = Field(..., description="Whether resume generation was successful")
