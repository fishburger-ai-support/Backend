from abc import ABC, abstractmethod


class BaseKnowledgeBase(ABC):

    @abstractmethod
    async def search(self, query: str):
        pass