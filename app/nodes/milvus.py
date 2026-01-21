from __future__ import annotations

import logging
from typing import Any, Optional

from pymilvus import Collection, CollectionSchema, DataType, FieldSchema, connections, utility

from app.config import MilvusConfig


logger = logging.getLogger(__name__)
_CONNECT_TIMEOUT_SECONDS = 10
_DEFAULT_INDEX_PARAMS = {
    "index_type": "IVF_FLAT",
    "metric_type": "L2",
    "params": {"nlist": 128},
}


def _serialize_search_result(result: Any) -> Any:
    if hasattr(result, "to_dict"):
        try:
            return result.to_dict()
        except Exception:
            return result
    return result


def _ensure_collection(name: Optional[str], *, dim: int) -> Collection:
    if not name:
        raise ValueError("MILVUS_COLLECTION is required")
    if utility.has_collection(name):
        return Collection(name)
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim),
    ]
    schema = CollectionSchema(fields, description="agent vectors")
    return Collection(name, schema)


def _ensure_index(collection: Collection, *, field_name: str) -> None:
    has_index = None
    has_index_method = getattr(collection, "has_index", None)
    if callable(has_index_method):
        has_index = has_index_method()
    if has_index is True:
        return
    create_index = getattr(collection, "create_index", None)
    if not callable(create_index):
        return
    create_index(field_name, _DEFAULT_INDEX_PARAMS)


def run_milvus_node(
    vector: list[float],
    *,
    config: MilvusConfig,
    query_vector: Optional[list[float]] = None,
    top_k: int = 3,
) -> dict[str, Any]:
    logger.info("milvus node started")
    try:
        if not config.host or config.port is None:
            raise ValueError("MILVUS_HOST and MILVUS_PORT are required")
        connections.connect(
            alias="default",
            host=config.host,
            port=config.port,
            user=config.username,
            password=config.password,
            db_name=config.db_name,
            timeout=_CONNECT_TIMEOUT_SECONDS,
        )
        collection = _ensure_collection(config.collection, dim=len(vector))

        insert_kwargs: dict[str, object] = {}
        if config.partition:
            insert_kwargs["partition_name"] = config.partition

        insert_result = collection.insert([{"embedding": vector}], **insert_kwargs)
        collection.flush()
        _ensure_index(collection, field_name="embedding")
        collection.load()

        search_vector = query_vector or vector
        search_kwargs: dict[str, object] = {}
        if config.partition:
            search_kwargs["partition_names"] = [config.partition]

        search_result = collection.search(
            data=[search_vector],
            anns_field="embedding",
            param={"metric_type": "L2", "params": {"nprobe": 10}},
            limit=top_k,
            **search_kwargs,
        )

        write_id = None
        if hasattr(insert_result, "primary_keys"):
            keys = insert_result.primary_keys
            if isinstance(keys, (list, tuple)) and keys:
                write_id = keys[0]

        logger.info("milvus node succeeded")
        return {
            "status": "success",
            "write_id": write_id,
            "query_result": _serialize_search_result(search_result),
        }
    except Exception as exc:  # noqa: BLE001 - want node to surface errors as data.
        logger.exception("milvus node failed")
        return {
            "status": "failed",
            "write_id": None,
            "query_result": None,
            "error": str(exc),
        }
