"""Cache danh sách /api/courses và /api/documents: phục vụ từ cache khi đọc
lặp lại, và PHẢI invalidate ngay khi có ghi (tạo/xóa/upload) — người dùng
không bao giờ thấy dữ liệu cũ sau thao tác của chính mình."""


def _create_course(client, headers, name: str) -> int:
    res = client.post(
        "/api/courses", json={"name": name, "description": ""}, headers=headers
    )
    assert res.status_code == 200, res.text
    return res.json()["id"]


def test_courses_list_served_from_cache(client, lecturer_headers, monkeypatch):
    """GET lần 2 trả từ cache — không chạm DB."""
    _create_course(client, lecturer_headers, "Môn cache hit")
    r1 = client.get("/api/courses", headers=lecturer_headers)
    assert r1.status_code == 200

    from app.modules.courses.repository import CourseRepository

    def boom(self):
        raise AssertionError("Cache miss: GET lần 2 vẫn query DB")

    monkeypatch.setattr(CourseRepository, "list", boom)
    r2 = client.get("/api/courses", headers=lecturer_headers)
    assert r2.status_code == 200
    assert r2.json() == r1.json()


def test_courses_list_fresh_after_create_and_delete(client, lecturer_headers):
    """Tạo/xóa môn phải thấy ngay trong danh sách (invalidate đúng)."""
    client.get("/api/courses", headers=lecturer_headers)  # nạp cache
    cid = _create_course(client, lecturer_headers, "Môn invalidate")

    names = [c["name"] for c in client.get(
        "/api/courses", headers=lecturer_headers
    ).json()]
    assert "Môn invalidate" in names

    res = client.delete(f"/api/courses/{cid}", headers=lecturer_headers)
    assert res.status_code == 204
    ids = [c["id"] for c in client.get(
        "/api/courses", headers=lecturer_headers
    ).json()]
    assert cid not in ids


def test_documents_list_fresh_after_upload_and_delete(client, lecturer_headers):
    """Upload (kể cả ingest lỗi vẫn tạo bản ghi FAILED) và xóa tài liệu phải
    thấy ngay trong danh sách."""
    cid = _create_course(client, lecturer_headers, "Môn docs cache")
    client.get("/api/documents", headers=lecturer_headers)  # nạp cache

    # PDF rác: ingest thất bại (500) nhưng Document vẫn được tạo (FAILED)
    # -> danh sách thay đổi -> cache phải được invalidate cả khi lỗi.
    files = {"file": ("rac.pdf", b"%PDF-1.4 junk", "application/pdf")}
    res = client.post(
        "/api/documents",
        data={"course_id": str(cid)},
        files=files,
        headers=lecturer_headers,
    )
    assert res.status_code == 500, res.text

    docs = client.get(
        "/api/documents", params={"course_id": cid}, headers=lecturer_headers
    ).json()
    assert [d["filename"] for d in docs] == ["rac.pdf"]
    doc_id = docs[0]["id"]

    res = client.delete(f"/api/documents/{doc_id}", headers=lecturer_headers)
    assert res.status_code == 204
    docs = client.get(
        "/api/documents", params={"course_id": cid}, headers=lecturer_headers
    ).json()
    assert docs == []
