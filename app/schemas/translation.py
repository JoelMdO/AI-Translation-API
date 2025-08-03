"""
Pydantic schemas for request/response models
Defines the structure of data that comes in and goes out of the API
"""
from pydantic import BaseModel, Field


class TranslationRequest(BaseModel):
    """Request schema for translation endpoint"""
    title: str = Field(..., description="Title text to translate")
    body: str = Field(..., description="Body text to translate") 
    section: str = Field(..., description="Section text to translate")
    target_language: str = Field(default="Spanish", description="Target language for translation")
    model: str = Field(default="llama3.2", description="Ollama model to use")


class TranslationResponse(BaseModel):
    """Response schema for translation endpoint"""
    translated_text: dict[str, str] = Field(..., description="The translated text as a JSON object with keys: title, body, section")
    success: bool = Field(..., description="Whether translation was successful")
    model_used: str = Field(..., description="Model used for translation")

    class Config:
        protected_namespaces = ()


class HealthResponse(BaseModel):
    """Response schema for health check endpoint"""
    status: str = Field(..., description="API status")
    ollama_connected: bool = Field(..., description="Whether Ollama is accessible")
    api_version: str = Field(..., description="API version")


class TokenRequest(BaseModel):
    """Request schema for token generation (if needed)"""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")
