from __future__ import annotations

import logging
from typing import Any, Optional

from pymilvus import Collection, connections

from app.config import MilvusConfig


logger = logging.getLogger(__name__)


def _serialize_search_result(result: Any) -> Any:
    if hasattr(result, "to_dict"):
        try:
            return result.to_dict()
        except Exception:
            return result
    return result


def run_milvus_node(
    vector: list[float],
    *,
    config: MilvusConfig,
    query_vector: Optional[list[float]] = None,
    top_k: int = 3,
) -> dict[str, Any]:
    logger.info("milvus node started")
    try:
        connections.connect(
            alias="default",
            host=config.host,
            port=config.port,
            user=config.username,
            password=config.password,
            db_name=config.db_name,
        )

        collection = Collection(config.collection)

        insert_kwargs: dict[str, object] = {}
        if config.partition:
            insert_kwargs["partition_name"] = config.partition

        insert_result = collection.insert([{"embedding": vector}], **insert_kwargs)
        collection.flush()
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
