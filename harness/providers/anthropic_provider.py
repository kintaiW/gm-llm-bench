"""Anthropic Claude Provider"""
import os
from .base import BaseProvider


class AnthropicProvider(BaseProvider):
    def __init__(self, model: str = "claude-sonnet-4-6"):
        import anthropic
        self.model = model
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))

    def complete(self, prompt: str) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text if resp.content else ""
