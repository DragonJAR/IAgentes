import os

class Config:
    GROQ_API_URL = os.getenv("GROQ_API_URL", "https://api.groq.com/openai/v1/chat/completions")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "AQUI-PONES-LA-API")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "AQUI-PONES-LA-API")
    LOGS_EN_CONSOLA = os.getenv("LOGS_EN_CONSOLA", "True").lower() in ["true", "1", "t"]
