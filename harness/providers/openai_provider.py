"""OpenAI 兼容 Provider（支持 GPT-4o / DeepSeek / Qwen 等）"""
import os
from .base import BaseProvider


class OpenAIProvider(BaseProvider):
    def __init__(self, model: str = "gpt-4o", base_url: str = ""):
        import openai
        self.model = model
        self.client = openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            base_url=base_url or None,
        )

    def complete(self, prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=2048,
        )
        return resp.choices[0].message.content or ""
