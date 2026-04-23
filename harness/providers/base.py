"""LLM Provider 基类"""
from abc import ABC, abstractmethod


class BaseProvider(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> str:
        """调用 LLM，返回文本响应"""
        ...
