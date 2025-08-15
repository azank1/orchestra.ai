from pydantic import BaseSettings, Field
from typing import Optional


class VoiceSettings(BaseSettings):
    deepgram_api_key: str = Field(..., env="DEEPGRAM_API_KEY")
    elevenlabs_api_key: str = Field(..., env="ELEVENLABS_API_KEY")
    vapi_api_key: Optional[str] = Field(None, env="VAPI_API_KEY")

    class Config:
        env_prefix = "VOICE_"


class OrchestrationSettings(BaseSettings):
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    model_name: str = Field("gpt-4", env="LLM_MODEL_NAME")
    temperature: float = Field(0.1, env="LLM_TEMPERATURE")

    class Config:
        env_prefix = "ORCHESTRA_"


class Settings(BaseSettings):
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")

    voice: VoiceSettings = VoiceSettings()
    orchestration: OrchestrationSettings = OrchestrationSettings()

    class Config:
        env_file = ".env"


settings = Settings()
