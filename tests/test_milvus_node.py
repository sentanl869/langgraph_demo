from types import SimpleNamespace

from app.config import MilvusConfig
from app.nodes.milvus import run_milvus_node


class FakeSearchResult:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return self._payload


class FakeCollection:
    def __init__(self, name, calls, search_result):
        self.name = name
        self._calls = calls
        self._search_result = search_result
        self._calls["collection_name"] = name

    def insert(self, data, partition_name=None):
        self._calls["insert"] = {
            "data": data,
            "partition_name": partition_name,
        }
        return SimpleNamespace(primary_keys=["pk-1"])

    def flush(self):
        self._calls["flush"] = True

    def load(self):
        self._calls["load"] = True

    def search(self, data, anns_field, param, limit, partition_names=None):
        self._calls["search"] = {
            "data": data,
            "anns_field": anns_field,
            "param": param,
            "limit": limit,
            "partition_names": partition_names,
        }
        return self._search_result


def test_milvus_node_success(monkeypatch):
    calls = {}
    search_result = FakeSearchResult({"hits": ["ok"]})

    def _fake_connect(**kwargs):
        calls["connect"] = kwargs

    def _fake_collection(name):
        return FakeCollection(name, calls, search_result)

    monkeypatch.setattr("app.nodes.milvus.connections.connect", _fake_connect)
    monkeypatch.setattr("app.nodes.milvus.Collection", _fake_collection)
    monkeypatch.setattr("app.nodes.milvus.utility.has_collection", lambda _name: True)

    config = MilvusConfig(
        host="127.0.0.1",
        port=19530,
        username="user",
        password="pass",
        collection="test_collection",
        partition="test_partition",
        db_name="default",
    )

    result = run_milvus_node(
        [0.1, 0.2, 0.3],
        config=config,
        query_vector=[0.2, 0.1, 0.0],
        top_k=2,
    )

    assert calls["connect"] == {
        "alias": "default",
        "host": "127.0.0.1",
        "port": 19530,
        "user": "user",
        "password": "pass",
        "db_name": "default",
        "timeout": 10,
    }
    assert calls["collection_name"] == "test_collection"
    assert calls["insert"] == {
        "data": [{"embedding": [0.1, 0.2, 0.3]}],
        "partition_name": "test_partition",
    }
    assert calls["flush"] is True
    assert calls["load"] is True
    assert calls["search"] == {
        "data": [[0.2, 0.1, 0.0]],
        "anns_field": "embedding",
        "param": {"metric_type": "L2", "params": {"nprobe": 10}},
        "limit": 2,
        "partition_names": ["test_partition"],
    }
    assert result == {
        "status": "success",
        "write_id": "pk-1",
        "query_result": {"hits": ["ok"]},
    }


def test_milvus_node_failure(monkeypatch):
    def _fake_connect(**_kwargs):
        raise RuntimeError("milvus down")

    monkeypatch.setattr("app.nodes.milvus.connections.connect", _fake_connect)

    config = MilvusConfig(
        host="127.0.0.1",
        port=19530,
        username=None,
        password=None,
        collection="test_collection",
        partition=None,
        db_name=None,
    )

    result = run_milvus_node([0.1, 0.2, 0.3], config=config)

    assert result["status"] == "failed"
    assert result["write_id"] is None
    assert result["query_result"] is None
    assert "milvus down" in result["error"]


def test_serialize_search_result_handles_error():
    from app.nodes.milvus import _serialize_search_result

    class BadResult:
        def to_dict(self):
            raise RuntimeError("boom")

    result = _serialize_search_result(BadResult())

    assert result == {}


def test_serialize_search_result_passthrough():
    from app.nodes.milvus import _serialize_search_result

    payload = {"hits": []}

    assert _serialize_search_result(payload) == payload
