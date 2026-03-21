"""ChromaDB-backed retrieval, deduplication, and memory for the content factory."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.utils import embedding_functions
from loguru import logger

from .config import AppConfig
from .market_researcher import ResearchItem

COLLECTION_POST_HISTORY = "post_history"
COLLECTION_MARKET = "market_insights"
COLLECTION_TOPIC_IDEAS = "topic_ideas"

# Cosine distance on normalized embeddings: lower is more similar.
DUPLICATE_TOPIC_DISTANCE_MAX = 0.22


class RAGEngine:
    """Vector store with three logical collections for posts, news, and ideas."""

    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._embed_fn = embedding_functions.DefaultEmbeddingFunction()
        self._client = chromadb.PersistentClient(path=config.chroma_persist_dir)
        self._posts = self._client.get_or_create_collection(
            name=COLLECTION_POST_HISTORY,
            embedding_function=self._embed_fn,
            metadata={"hnsw:space": "cosine"},
        )
        self._market = self._client.get_or_create_collection(
            name=COLLECTION_MARKET,
            embedding_function=self._embed_fn,
            metadata={"hnsw:space": "cosine"},
        )
        self._ideas = self._client.get_or_create_collection(
            name=COLLECTION_TOPIC_IDEAS,
            embedding_function=self._embed_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def add_post(self, post_text: str, topic: str, date: Optional[str] = None) -> None:
        """Persist a published post for similarity search and deduplication."""
        when = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        doc_id = f"post_{when}_{abs(hash(post_text)) % (10**12)}"
        self._posts.add(
            ids=[doc_id],
            documents=[post_text],
            metadatas=[{"topic": topic[:512], "date": when, "type": "post"}],
        )
        logger.debug("RAG: stored post snapshot {}", doc_id)

    def add_market_insight(self, item: ResearchItem) -> None:
        """Store a market research item for retrieval."""
        body = f"{item.title}\n{item.summary}\n{item.url}"
        doc_id = f"news_{abs(hash(body)) % (10**12)}"
        self._market.add(
            ids=[doc_id],
            documents=[body],
            metadatas=[
                {
                    "source": item.source[:256],
                    "date": item.date[:32],
                    "url": item.url[:512],
                }
            ],
        )

    def add_topic_idea(self, idea_text: str, label: str = "idea") -> None:
        """Optional backlog of topic ideas."""
        doc_id = f"idea_{abs(hash(idea_text)) % (10**12)}"
        self._ideas.add(
            ids=[doc_id],
            documents=[idea_text],
            metadatas=[{"label": label[:256]}],
        )

    def get_similar_posts(self, query: str, n: int = 5) -> List[Dict[str, Any]]:
        """Return the most similar prior posts with distances."""
        if not query.strip():
            return []
        res = self._posts.query(
            query_texts=[query],
            n_results=max(1, min(n, 50)),
            include=["documents", "distances", "metadatas"],
        )
        out: List[Dict[str, Any]] = []
        docs = (res.get("documents") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        for doc, dist, meta in zip(docs, dists, metas):
            out.append({"text": doc, "distance": dist, "metadata": meta or {}})
        return out

    def get_relevant_insights(self, topic: str, n: int = 3) -> List[Dict[str, Any]]:
        """Return market insights most relevant to `topic`."""
        if not topic.strip():
            return []
        res = self._market.query(
            query_texts=[topic],
            n_results=max(1, min(n, 30)),
            include=["documents", "distances", "metadatas"],
        )
        out: List[Dict[str, Any]] = []
        docs = (res.get("documents") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        for doc, dist, meta in zip(docs, dists, metas):
            out.append({"text": doc, "distance": dist, "metadata": meta or {}})
        return out

    def topic_already_posted(self, topic: str) -> bool:
        """Return True if a very similar topic was already published recently."""
        similar = self.get_similar_posts(topic, n=3)
        if not similar:
            return False
        best = min(s["distance"] for s in similar if s.get("distance") is not None)
        logger.info("RAG: best duplicate-check distance for topic: {:.4f}", float(best))
        return float(best) <= DUPLICATE_TOPIC_DISTANCE_MAX
