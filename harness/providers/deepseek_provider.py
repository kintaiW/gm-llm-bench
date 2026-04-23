"""DeepSeek Provider（OpenAI 兼容接口）"""
import os
from .openai_provider import OpenAIProvider


class DeepSeekProvider(OpenAIProvider):
    def __init__(self, model: str = "deepseek-chat"):
        import openai
        self.model = model
        self.client = openai.OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY", ""),
            base_url="https://api.deepseek.com/v1",
        )
