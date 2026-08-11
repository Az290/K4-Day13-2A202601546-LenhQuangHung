# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: (điền tên nhóm)
- Repository URL: (điền sau khi push)
- Commit SHA cuối: (điền sau khi push)
- Thành viên và vai trò:
  - Lệnh Quang Hưng - 2A202601546 — Role A: Logging & Middleware & PII (correlation ID, enrichment, PII scrubbing)
  - (thành viên B) — Role B: Tracing & Prompt Version, SLO/Alert
  - (thành viên C) — Role C: Dashboard/QA, Challenge Investigation, tổng hợp báo cáo

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100 (đã xác nhận qua `submission/evidence/cp1_validate_logs_result.txt`; vượt mục tiêu ≥80/100). Xem thêm `submission/evidence/cp1_validate_logs_result.txt` và `cp1_validate_logs.png`.
- Tổng số traces: (điền bởi Role B sau khi cấu hình Langfuse)
- Số PII leak còn lại: 0 (theo `validate_logs.py`); đã tự kiểm tay bằng `grep -i "@"` và `grep "4111"` trên `data/logs.jsonl` — không có kết quả nguyên văn nào lộ ra.
- Link/đường dẫn dashboard: (điền bởi Role C)

## 3. Logging và tracing

- Evidence correlation ID: `submission/evidence/cp1_log_sample.png` và `cp1_sample_logs.json` — mỗi log có `correlation_id` dạng `req-<8hex>` (ví dụ `req-860c3b42`), sinh tại [app/middleware.py](../app/middleware.py) (`CorrelationIdMiddleware`), lấy từ header `x-request-id` nếu client gửi, ngược lại tự tạo mới; trả lại trong response header `x-request-id`.
- Evidence PII redaction: cùng ảnh trên — trường `payload.message_preview` hiển thị `[REDACTED_EMAIL]` thay vì email thật. Bộ lọc PII nằm ở [app/pii.py](../app/pii.py) (`PII_PATTERNS`: email, phone_vn, cccd, credit_card, passport, address_vn) và được áp dụng qua processor `scrub_event` trong [app/logging_config.py](../app/logging_config.py), đặt sau `TimeStamper` và trước `JsonlFileProcessor`/`JSONRenderer` để đảm bảo dữ liệu được che trước khi ghi xuống file. `scrub_event` quét mọi trường string/dict top-level (không chỉ `payload`) để tránh lộ PII qua các trường khác.
- Evidence trace waterfall: (điền bởi Role B)
- Giải thích một span đáng chú ý: Log `request_received` trong `app/main.py` được enrich bằng `bind_contextvars(user_id_hash, session_id, feature, model, env)` ngay khi vào endpoint `/chat`, trước khi gọi agent — nhờ vậy mọi log phát sinh trong cùng request (kể cả log lỗi `request_failed`) tự động mang đủ metadata mà không cần truyền tham số thủ công qua từng hàm.

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract.` (2026-08-11)
- Evidence dashboard: TODO — ảnh dashboard runtime (6 panel, time range/threshold hiển thị) chưa chụp, cần dựng dashboard (Streamlit/notebook/Grafana) rồi lưu vào `submission/evidence/` theo [docs/DASHBOARD_SETUP.md](../docs/DASHBOARD_SETUP.md).
- SLO đã chọn và lý do: Giữ nguyên 4 SLI mặc định trong `config/slo.yaml` (`latency_p95_ms` ≤ 3000ms, `error_rate_pct` ≤ 2%, `daily_cost_usd` ≤ $2.5, `quality_score_avg` ≥ 0.75) vì đã khớp threshold của `config/dashboard.yaml` (contract dùng chung, không tự đổi) và baseline thực tế trong `data/logs.jsonl` (latency ~150ms, cost ~0.002 USD/request, 0 lỗi) cho thấy còn dư địa hợp lý để phát hiện incident thay vì báo động giả.
- Alert rules và runbook: 3 alert symptom-based trong `config/alert_rules.yaml`, chi tiết đầy đủ trong [docs/alerts.md](../docs/alerts.md):
  1. `high_latency_p95` (warning) — `latency_p95_ms > 3000` duy trì 5 phút. Verify bằng practice `rag_slow`: `/metrics` cho latency_p95 tăng từ **152ms → 2651ms** (~17 lần) khi bật incident, giảm lại sau khi tắt.
  2. `elevated_error_rate` (critical) — `error_rate_pct > 2%` duy trì 5 phút. Verify bằng practice `tool_fail`: 10/10 request trả `500 RuntimeError` (100% lỗi) khi bật incident, `error_breakdown={}` khi tắt.
  3. `daily_cost_budget_burn` (warning) — `daily_cost_usd > 2.5` trong cửa sổ rolling 24h. Verify bằng practice `cost_spike`: avg cost/request tăng từ **$0.0020 → $0.0037** (~1.8 lần), tổng cost cộng dồn từ $0.0604 → $0.1464 sau 10 request.

## 6. Điều tra challenge

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Lệnh Quang Hưng - 2A202601546 | Role A — Logging & Middleware & PII: hoàn thiện `app/middleware.py` (correlation ID `req-<8hex>`, bind/clear contextvars, response headers), `app/main.py` (enrich context `user_id_hash/session_id/feature/model/env`), `app/logging_config.py` (bật và nâng cấp `scrub_event` quét toàn bộ trường), `app/pii.py` (thêm pattern `passport`, `address_vn`). Kết quả: `validate_logs.py` 100/100, `pytest -q` 22/22 pass, không còn PII thô trong log. | (điền link sau khi commit/push) | Hiểu vì sao phải `clear_contextvars()` đầu middleware để tránh context của request trước rò sang request sau (do server dùng chung thread/task pool); hiểu thứ tự processor trong structlog quyết định dữ liệu được scrub trước hay sau khi ghi log — đặt sai thứ tự thì PII vẫn lọt xuống file dù code scrub "trông đúng". |
| | | | |
