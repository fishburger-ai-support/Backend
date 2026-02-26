from .base import BaseKnowledgeBase


class MockKnowledgeBase(BaseKnowledgeBase):

    async def search(self, query: str):
        return []