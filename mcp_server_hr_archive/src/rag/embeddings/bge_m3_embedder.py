from __future__ import annotations
import asyncio
from typing import List, TypedDict

from logger import get_logger

log = get_logger(__name__)


class EmbeddingResult(TypedDict):
    dense: List[float]
    sparse: dict[int, float]


class BGEM3Embedder:
    """Wrapper bge-m3 thật (dense 1024 chiều + sparse lexical weights) qua FlagEmbedding.

    Model tải lần đầu ~vài trăm MB — nên cache volume khi Dockerize.
    """

    def __init__(self, model_name: str = "BAAI/bge-m3", use_fp16: bool = True) -> None:
        self._model_name = model_name
        self._use_fp16 = use_fp16
        self._model = None  # lazy load, tránh tải model khi chưa cần (vd unit test)

    def _load(self):
        if self._model is None:
            from FlagEmbedding import BGEM3FlagModel
            log.info("Loading embedding model %s ...", self._model_name)
            self._model = BGEM3FlagModel(self._model_name, use_fp16=self._use_fp16)
        return self._model

    async def embed(self, texts: List[str]) -> List[EmbeddingResult]:
        # model.encode là sync + nặng CPU/GPU -> chạy trong executor để không block event loop
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._embed_sync, texts)

    def _embed_sync(self, texts: List[str]) -> List[EmbeddingResult]:
        model = self._load()
        out = model.encode(texts, return_dense=True, return_sparse=True, return_colbert_vecs=False)
        results: List[EmbeddingResult] = []
        for i in range(len(texts)):
            dense = out["dense_vecs"][i].tolist()
            sparse = {int(k): float(v) for k, v in out["lexical_weights"][i].items()}
            results.append({"dense": dense, "sparse": sparse})
        return results