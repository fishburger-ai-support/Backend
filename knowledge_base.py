import json
import os
import numpy as np
from sentence_transformers import SentenceTransformer

class KnowledgeBase:
    def __init__(self, kb_path='knowledge_base.json'):
        self.kb_path = kb_path
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.documents = []
        self.embeddings = []
        self.load_knowledge_base()
    
    def load_knowledge_base(self):
        """Загрузка базы знаний из JSON"""
        if os.path.exists(self.kb_path):
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.documents = data.get('documents', [])
                
                if self.documents:
                    # Создаём эмбеддинги
                    texts = [f"{doc['title']}\n{doc['content']}" for doc in self.documents]
                    self.embeddings = self.model.encode(texts)
                    print(f"📚 Загружено {len(self.documents)} документов в базу знаний")
    
    def search(self, query, top_k=3):
        """Поиск похожих документов"""
        if not self.documents or not self.embeddings:
            return []
        
        # Эмбеддинг запроса
        query_emb = self.model.encode([query])
        
        # Косинусное сходство
        scores = np.dot(self.embeddings, query_emb.T).flatten()
        
        # Берём top_k результатов
        top_indices = np.argsort(scores)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0.3:  # Порог сходства
                results.append({
                    'title': self.documents[idx]['title'],
                    'content': self.documents[idx]['content'],
                    'score': float(scores[idx])
                })
        
        return results
    
    def add_document(self, title, content):
        """Добавление документа в базу знаний"""
        self.documents.append({'title': title, 'content': content})
        
        # Обновляем эмбеддинги
        texts = [f"{doc['title']}\n{doc['content']}" for doc in self.documents]
        self.embeddings = self.model.encode(texts)
        
        # Сохраняем в файл
        with open(self.kb_path, 'w', encoding='utf-8') as f:
            json.dump({'documents': self.documents}, f, ensure_ascii=False, indent=2)