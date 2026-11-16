"""Q07：来源精确定位、真实 MySQL 版本事务、隔离与并发重复导入。"""

from concurrent.futures import ThreadPoolExecutor
import hashlib
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from backend.app.main import app
from backend.app.ai.rag.splitter import preview_document
from backend.app.schemas.knowledge import KnowledgeInput, SplitOptions
from backend.app.db.session import SessionLocal
from backend.app.models import (
    AccessToken,
    User,
    KnowledgeDocument as Document,
    KnowledgeDocumentVersion as Version,
    KnowledgeChunk as Chunk,
)
from backend.app.services import knowledge as service
from backend.app.repositories import knowledge as repository


def body(text, size=64, overlap=12, title="规则"):
    return KnowledgeInput(
        title=title,
        text=text,
        options=SplitOptions(chunk_size=size, chunk_overlap=overlap),
    )


@pytest.mark.parametrize(
    "text",
    [
        "\ufeff# 标题\r\n\r\n" + "😀商品破损请保留包装。" * 40,
        "重复规则" * 200,
        " # 标题\n尾部包含空格 \n",
        "# " + "长标题" * 1800,
    ],
)
def test_chunks_are_exact_normalized_source_slices(text):
    result = preview_document(body(text))
    assert result.chunks
    covered = set()
    for chunk in result.chunks:
        assert 0 <= chunk.start < chunk.end <= len(result.normalized_text)
        assert result.normalized_text[chunk.start : chunk.end] == chunk.text
        assert len(chunk.text) <= 64
        assert (
            chunk.start_line == result.normalized_text.count("\n", 0, chunk.start) + 1
        )
        covered.update(range(chunk.start, chunk.end))
    assert covered == set(
        range(len(result.normalized_text))
    )  # 包括空白与标点，不丢源字符。
    assert "\r" not in result.normalized_text and not result.normalized_text.startswith(
        "\ufeff"
    )


def test_overlap_and_fingerprint_have_explicit_units():
    text = "甲" * 160
    a = preview_document(body(text, overlap=0))
    b = preview_document(body(text, overlap=12))
    assert a.chunks[0].end == a.chunks[1].start
    assert b.chunks[0].end - b.chunks[1].start == 12
    assert a.content_hash == b.content_hash and a.fingerprint != b.fingerprint
    assert (
        preview_document(body(text.replace("甲", "乙"))).content_hash != a.content_hash
    )


@pytest.fixture
def knowledge_case():
    title = "knowledge-test-" + uuid.uuid4().hex
    tokens = []
    with TestClient(app) as client:
        for name in ("alice", "bob"):
            response = client.post(
                "/api/login", json={"username": name, "password": "Learn123!"}
            )
            assert response.status_code == 200
            tokens.append(response.json()["token"])
        with SessionLocal() as db:
            user_id = db.scalar(select(User.id).where(User.username == "alice"))
        try:
            yield (
                client,
                title,
                user_id,
                {"Authorization": "Bearer " + tokens[0]},
                {"Authorization": "Bearer " + tokens[1]},
            )
        finally:
            with SessionLocal.begin() as db:
                ids = list(
                    db.scalars(select(Document.id).where(Document.title == title))
                )
                if ids:
                    versions = list(
                        db.scalars(
                            select(Version.id).where(Version.document_id.in_(ids))
                        )
                    )
                    if versions:
                        db.execute(delete(Chunk).where(Chunk.version_id.in_(versions)))
                    db.execute(delete(Version).where(Version.document_id.in_(ids)))
                    db.execute(delete(Document).where(Document.id.in_(ids)))
                for token in tokens:
                    db.execute(
                        delete(AccessToken).where(
                            AccessToken.token_hash
                            == hashlib.sha256(token.encode()).hexdigest()
                        )
                    )


def test_preview_is_read_only_and_routes_reject_invalid_input(knowledge_case):
    client, title, _, alice, _ = knowledge_case
    payload = body("示例规则" * 40, title=title).model_dump()
    assert client.post("/api/knowledge/preview", json=payload).status_code == 401
    assert client.post("/api/knowledge/import", json=payload).status_code == 401
    assert client.get("/api/knowledge/documents").status_code == 401
    assert (
        client.post("/api/knowledge/preview", headers=alice, json=payload).status_code
        == 200
    )
    assert all(
        row["title"] != title
        for row in client.get("/api/knowledge/documents", headers=alice).json()
    )
    for change in (
        {"text": " "},
        {"text": "a" * 20001},
        {"title": " "},
        {"options": {"chunk_size": 64, "chunk_overlap": 64}},
        {"options": {"chunk_size": "64"}},
        {"text": "\x00"},
    ):
        assert (
            client.post(
                "/api/knowledge/preview", headers=alice, json={**payload, **change}
            ).status_code
            == 422
        )
    too_many = body("甲" * 20000, overlap=63, title=title).model_dump()
    assert (
        client.post("/api/knowledge/import", headers=alice, json=too_many).status_code
        == 422
    )
    example = client.get("/api/knowledge/example", headers=alice)
    assert example.status_code == 200 and "合成" in example.json()["text"]


def test_mysql_dedup_versions_source_and_user_isolation(knowledge_case):
    client, title, _, alice, bob = knowledge_case
    payload = body("# 规则\n" + "破损请提供照片。" * 30, title=title).model_dump()
    first = client.post("/api/knowledge/import", headers=alice, json=payload).json()
    assert not first["reused"] and first["version"]["revision"] == 1
    document_id = first["version"]["document_id"]
    repeated = client.post("/api/knowledge/import", headers=alice, json=payload).json()
    assert repeated["reused"] and repeated["version"]["revision"] == 1
    payload["options"]["chunk_overlap"] = 0
    second = client.post("/api/knowledge/import", headers=alice, json=payload).json()
    assert not second["reused"] and second["version"]["revision"] == 2
    payload["text"] += "新版本追加说明。"
    third = client.post("/api/knowledge/import", headers=alice, json=payload).json()
    assert third["version"]["revision"] == 3
    url = f"/api/knowledge/documents/{document_id}"
    assert client.get(url, headers=alice).json()["revision"] == 3
    history = client.get(url + "/versions/1", headers=alice).json()
    assert history["active"] is False and history["normalized_text"] != payload["text"]
    for chunk in history["chunks"]:
        assert (
            history["normalized_text"][chunk["start"] : chunk["end"]] == chunk["text"]
        )
    versions = client.get(url + "/versions", headers=alice).json()
    assert len(versions) == 3 and sum(row["active"] for row in versions) == 1
    for suffix in ("", "/versions", "/versions/1"):
        assert client.get(url + suffix, headers=bob).status_code == 404
    assert all(
        row["id"] != document_id
        for row in client.get("/api/knowledge/documents", headers=bob).json()
    )
    # 另一个用户同标题创建的是自己的独立文档。
    own = client.post("/api/knowledge/import", headers=bob, json=payload).json()
    assert (
        own["version"]["document_id"] != document_id and own["version"]["revision"] == 1
    )


def test_failed_version_rolls_back_active_pointer_and_chunks(
    knowledge_case, monkeypatch
):
    _, title, user_id, _, _ = knowledge_case
    with SessionLocal() as db:
        original = service.import_document(
            db, user_id, body("原规则" * 30, title=title)
        )
    original_add = repository.add_version

    def fail_after_write(db, document, preview):
        original_add(db, document, preview)
        raise RuntimeError("故意模拟提交前故障")

    monkeypatch.setattr(repository, "add_version", fail_after_write)
    with SessionLocal() as db, pytest.raises(RuntimeError):
        service.import_document(db, user_id, body("新规则" * 30, title=title))
    with SessionLocal() as db:
        versions = service.list_versions(db, user_id, original.version.document_id)
        current = service.read_version(db, user_id, original.version.document_id)
        assert len(versions) == 1 and current.revision == 1 and current.active
        assert current.normalized_text == "原规则" * 30


def test_concurrent_duplicate_import_has_one_current_version(knowledge_case):
    _, title, user_id, _, _ = knowledge_case
    payload = body("并发规则" * 50, title=title)

    def run(_):
        with SessionLocal() as db:
            # 模拟认证读取提前建立快照；Service 必须先释放旧快照。
            db.scalar(select(User).where(User.id == user_id))
            return service.import_document(db, user_id, payload)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, range(2)))
    assert {r.version.document_id for r in results} == {results[0].version.document_id}
    assert sum(not r.reused for r in results) == 1
    assert [r.version.revision for r in results] == [1, 1]
