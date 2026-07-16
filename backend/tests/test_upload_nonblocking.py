"""Hồi quy: upload phải là endpoint SYNC để FastAPI chạy trong threadpool.

Trước đây endpoint là `async def` nhưng gọi DocumentService.ingest (đồng bộ,
parse + chunk + embed hàng chục giây) ngay trên event loop — trong lúc một
Giảng viên upload, MỌI request khác (chat, đăng nhập...) bị treo theo."""
import asyncio


def test_upload_endpoint_is_sync_so_it_runs_in_threadpool():
    from app.modules.documents.router import upload_document

    assert not asyncio.iscoroutinefunction(upload_document), (
        "upload_document phải là `def` (sync) — `async def` gọi ingest đồng bộ "
        "sẽ chặn event loop, treo toàn bộ app khi có người upload"
    )
