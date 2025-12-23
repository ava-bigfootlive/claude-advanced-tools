"""
Semantic Tool Search - Custom embeddings-based tool discovery.

This is an optional enhancement to the built-in BM25 search.
Uses sentence embeddings for semantic similarity matching,
which can understand intent better than keyword matching.

Example:
    Query: "start broadcasting"
    BM25 might miss: "start_event" (no keyword match)
    Semantic: finds "start_event" (understands broadcasting = live event)
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from .tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

# Default cache directory
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "claude-advanced-tools"


class SemanticToolSearch:
    """
    Custom semantic search for tool discovery using embeddings.

    Uses SentenceTransformer for encoding tool descriptions and queries
    into vector space, then finds similar tools via cosine similarity.

    Benefits over BM25:
    - Understands synonyms and related concepts
    - Better with natural language queries
    - Can find tools even without exact keyword matches

    Trade-offs:
    - Requires sentence-transformers package (~400MB model)
    - Slower initial indexing (one-time cost)
    - Higher memory usage
    """

    def __init__(
        self,
        registry: "ToolRegistry",
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        cache_dir: Path | str | None = None,
        use_cache: bool = True
    ):
        """
        Initialize semantic search.

        Args:
            registry: ToolRegistry instance
            model_name: SentenceTransformer model to use
                - all-MiniLM-L6-v2: Fast, 384 dimensions, good quality
                - all-mpnet-base-v2: Slower, 768 dimensions, best quality
            cache_dir: Directory for embedding cache (default: ~/.cache/claude-advanced-tools)
            use_cache: Whether to use disk caching for embeddings
        """
        self.registry = registry
        self.model_name = model_name
        self.model = None
        self.embeddings: np.ndarray | None = None
        self.tool_names: list[str] = []
        self._initialized = False

        # Cache configuration
        self.use_cache = use_cache
        self.cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
        self._cache_hash: str | None = None

    def _load_model(self):
        """Lazy load the embedding model."""
        if self.model is not None:
            return

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers required: pip install sentence-transformers"
            )

        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        logger.info("Model loaded successfully")

    def _compute_tools_hash(self) -> str:
        """Compute a hash of tools for cache validation."""
        # Create a stable representation of tools
        tool_data = []
        for name in sorted(self.registry.tools.keys()):
            tool = self.registry.tools[name]
            tool_data.append({
                "name": name,
                "description": tool.get("description", ""),
                "input_schema": tool.get("input_schema", {})
            })

        # Hash the JSON representation
        data_str = json.dumps(tool_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]

    def _get_cache_paths(self) -> tuple[Path, Path]:
        """Get paths for cache files."""
        # Use model name in cache path for different model support
        model_slug = self.model_name.replace("/", "_")
        embeddings_path = self.cache_dir / f"embeddings_{model_slug}.npy"
        metadata_path = self.cache_dir / f"embeddings_{model_slug}_meta.json"
        return embeddings_path, metadata_path

    def _save_cache(self):
        """Save embeddings to disk cache."""
        if not self.use_cache or self.embeddings is None:
            return

        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            embeddings_path, metadata_path = self._get_cache_paths()

            # Save embeddings
            np.save(embeddings_path, self.embeddings)

            # Save metadata
            metadata = {
                "tool_names": self.tool_names,
                "tools_hash": self._cache_hash,
                "model_name": self.model_name,
                "embedding_shape": list(self.embeddings.shape)
            }
            with open(metadata_path, "w") as f:
                json.dump(metadata, f)

            logger.info(f"Saved embedding cache to {self.cache_dir}")
        except Exception as e:
            logger.warning(f"Failed to save embedding cache: {e}")

    def _load_cache(self) -> bool:
        """
        Load embeddings from disk cache.

        Returns:
            True if cache was loaded successfully, False otherwise
        """
        if not self.use_cache:
            return False

        embeddings_path, metadata_path = self._get_cache_paths()

        if not embeddings_path.exists() or not metadata_path.exists():
            logger.debug("No embedding cache found")
            return False

        try:
            # Load and validate metadata
            with open(metadata_path) as f:
                metadata = json.load(f)

            # Check if cache matches current tools
            current_hash = self._compute_tools_hash()
            if metadata.get("tools_hash") != current_hash:
                logger.info("Embedding cache invalidated (tools changed)")
                return False

            if metadata.get("model_name") != self.model_name:
                logger.info("Embedding cache invalidated (model changed)")
                return False

            # Load embeddings
            self.embeddings = np.load(embeddings_path)
            self.tool_names = metadata["tool_names"]
            self._cache_hash = metadata["tools_hash"]
            self._initialized = True

            logger.info(
                f"Loaded embedding cache: {len(self.tool_names)} tools, "
                f"shape {self.embeddings.shape}"
            )
            return True

        except Exception as e:
            logger.warning(f"Failed to load embedding cache: {e}")
            return False

    def _clear_cache(self):
        """Delete cache files from disk."""
        try:
            embeddings_path, metadata_path = self._get_cache_paths()
            if embeddings_path.exists():
                embeddings_path.unlink()
            if metadata_path.exists():
                metadata_path.unlink()
            logger.debug("Embedding cache cleared")
        except Exception as e:
            logger.warning(f"Failed to clear embedding cache: {e}")

    def build_index(self, force_rebuild: bool = False):
        """
        Pre-compute embeddings for all tools.

        This should be called after registering tools.
        Embeddings are cached to disk and reloaded on subsequent runs.

        Args:
            force_rebuild: If True, rebuild index even if cache exists
        """
        # Compute hash for cache validation
        self._cache_hash = self._compute_tools_hash()

        # Try to load from cache first
        if not force_rebuild and self._load_cache():
            return  # Successfully loaded from cache

        # Need to build fresh - load model
        self._load_model()

        texts = []
        self.tool_names = []

        for name, tool in self.registry.tools.items():
            # Combine name, description, and parameter info for richer embeddings
            text = f"{name}: {tool['description']}"

            # Add parameter names and descriptions
            if "input_schema" in tool:
                props = tool["input_schema"].get("properties", {})
                param_texts = []
                for param_name, param_info in props.items():
                    param_desc = param_info.get("description", "")
                    param_texts.append(f"{param_name}: {param_desc}")
                if param_texts:
                    text += " Parameters: " + ", ".join(param_texts)

            texts.append(text)
            self.tool_names.append(name)

        if texts:
            self.embeddings = self.model.encode(texts, convert_to_numpy=True)
            logger.info(f"Built embedding index for {len(texts)} tools")
            # Save to cache for next time
            self._save_cache()
        else:
            self.embeddings = np.array([])
            logger.warning("No tools to index")

        self._initialized = True

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Find most relevant tools using cosine similarity.

        Args:
            query: Natural language search query
            top_k: Number of results to return

        Returns:
            List of tool_reference blocks with similarity scores
        """
        if not self._initialized:
            self.build_index()

        if self.embeddings is None or len(self.embeddings) == 0:
            return []

        # Ensure model is loaded for query encoding (may have loaded from cache)
        self._load_model()

        # Encode query
        query_embedding = self.model.encode(query, convert_to_numpy=True)

        # Compute cosine similarities
        # embeddings are already normalized by SentenceTransformer
        similarities = np.dot(self.embeddings, query_embedding)

        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        results = [
            {
                "type": "tool_reference",
                "tool_name": self.tool_names[i],
                "score": float(similarities[i])
            }
            for i in top_indices
            if similarities[i] > 0  # Only positive similarities
        ]

        logger.debug(f"Semantic search '{query}' found {len(results)} tools")
        return results

    def invalidate(self, clear_cache: bool = True):
        """
        Invalidate the embedding index. Will be rebuilt on next search.

        Args:
            clear_cache: If True, also delete disk cache files
        """
        self.embeddings = None
        self.tool_names = []
        self._initialized = False
        self._cache_hash = None

        if clear_cache:
            self._clear_cache()

        logger.debug("Embedding index invalidated")

    def get_stats(self) -> dict:
        """Get statistics about the semantic search."""
        embeddings_path, metadata_path = self._get_cache_paths()
        cache_exists = embeddings_path.exists() and metadata_path.exists()

        return {
            "model_name": self.model_name,
            "model_loaded": self.model is not None,
            "index_built": self._initialized,
            "indexed_tools": len(self.tool_names),
            "embedding_dimensions": (
                self.embeddings.shape[1] if self.embeddings is not None
                and len(self.embeddings) > 0 else 0
            ),
            "cache_enabled": self.use_cache,
            "cache_dir": str(self.cache_dir),
            "cache_exists": cache_exists,
            "tools_hash": self._cache_hash
        }


class HybridToolSearch:
    """
    Combines BM25 and semantic search for best results.

    Uses a weighted combination of both search methods:
    - BM25 for exact keyword matching
    - Semantic for conceptual understanding

    This provides the speed of BM25 with the understanding of embeddings.
    """

    def __init__(
        self,
        registry: "ToolRegistry",
        bm25_weight: float = 0.4,
        semantic_weight: float = 0.6,
        cache_dir: Path | str | None = None,
        use_cache: bool = True
    ):
        """
        Initialize hybrid search.

        Args:
            registry: ToolRegistry instance
            bm25_weight: Weight for BM25 scores (0-1)
            semantic_weight: Weight for semantic scores (0-1)
            cache_dir: Directory for embedding cache
            use_cache: Whether to use disk caching for embeddings
        """
        from .tool_search import ToolSearchProvider

        self.registry = registry
        self.bm25_search = ToolSearchProvider(registry, search_type="bm25")
        self.semantic_search = SemanticToolSearch(
            registry,
            cache_dir=cache_dir,
            use_cache=use_cache
        )
        self.bm25_weight = bm25_weight
        self.semantic_weight = semantic_weight

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Search using both methods and combine results.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            Combined and re-ranked results
        """
        # Get results from both methods
        bm25_results = self.bm25_search.search(query, top_k * 2)
        semantic_results = self.semantic_search.search(query, top_k * 2)

        # Combine scores
        scores: dict[str, float] = {}

        # Add BM25 scores (normalized by rank)
        for i, result in enumerate(bm25_results):
            name = result["tool_name"]
            rank_score = 1.0 / (i + 1)  # Higher rank = higher score
            scores[name] = scores.get(name, 0) + rank_score * self.bm25_weight

        # Add semantic scores
        for result in semantic_results:
            name = result["tool_name"]
            sim_score = result.get("score", 0.5)
            scores[name] = scores.get(name, 0) + sim_score * self.semantic_weight

        # Sort by combined score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        return [
            {
                "type": "tool_reference",
                "tool_name": name,
                "score": score
            }
            for name, score in ranked[:top_k]
        ]

    def build_indices(self):
        """Build both search indices."""
        self.bm25_search._build_bm25_index()
        self.semantic_search.build_index()

    def invalidate(self):
        """Invalidate both search indices."""
        self.bm25_search.invalidate_index()
        self.semantic_search.invalidate()
