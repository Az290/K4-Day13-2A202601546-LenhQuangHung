# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: HQD
- Repository URL: https://github.com/Az290/K4-Day13-2A202601546-LenhQuangHung
- Commit SHA cuối: 043ffc5f59f91a45b2cf1e72f5b690faf4f472aa
- Thành viên và vai trò:
  - Lệnh Quang Hưng - 2A202601546: Role A - Logging & Middleware & PII.
  - Nguyễn Minh Quang - 2A202601730: Role B - Langfuse config, SLO/Alert Rules, Alert Runbook.
  - Lê Minh Đạt - 2A202601088: Role C - Dashboard/QA, load test, Practice/Challenge Incident CP3, tổng hợp báo cáo nhóm.

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100. Evidence: `submission/evidence/cp1_validate_logs_result.txt` và `submission/evidence/cp1_validate_logs.png`.
- Tổng số traces: 10. Đã xác nhận qua Langfuse API `client.api.trace.list()` sau khi cấu hình `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY`; `/health` trả `tracing_enabled=true`.
- Số PII leak còn lại: 0 theo `validate_logs.py`; đã kiểm tra thêm email/card mẫu không xuất hiện nguyên văn trong `data/logs.jsonl`.
- Link/đường dẫn dashboard: `submission/evidence/dashboard_runtime.html`; dashboard contract đã hợp lệ theo `config/dashboard.yaml`, log runtime đã có tại `data/logs.jsonl` để dựng đủ 6 panel.

## 3. Logging và tracing

- Evidence correlation ID: `submission/evidence/cp1_log_sample.png` và `submission/evidence/cp1_sample_logs.json`. Mỗi log có `correlation_id` dạng `req-<8hex>`, sinh tại `app/middleware.py`, lấy từ header `x-request-id` nếu client gửi, ngược lại tự tạo mới; response trả lại header `x-request-id`.
- Evidence PII redaction: `submission/evidence/cp1_log_sample.png` và `submission/evidence/cp1_sample_logs.json`. Trường `payload.message_preview` hiển thị token redact như `[REDACTED_EMAIL]` thay vì email thật. Bộ lọc PII nằm ở `app/pii.py` và được áp dụng qua processor `scrub_event` trong `app/logging_config.py`.
- Evidence trace waterfall: `submission/evidence/waterfall.png` và `submission/evidence/trace.png`.
- Giải thích một span đáng chú ý: Log `request_received` trong `app/main.py` được enrich bằng `bind_contextvars(user_id_hash, session_id, feature, model, env)` ngay khi vào endpoint `/chat`, trước khi gọi agent. Nhờ vậy các log trong cùng request có đủ metadata mà không cần truyền thủ công qua từng hàm.

## 4. Prompt versioning

- Prompt name: `day13-chat` theo contract trong `docs/PROMPT_VERSIONING.md`.
- Version/label baseline: Chờ evidence Langfuse.
- Version/label candidate: Chờ evidence Langfuse.
- Trace ID của mỗi version: Chờ evidence Langfuse.
- Bằng chứng đổi label hoặc rollback: Chờ ảnh/evidence từ Langfuse.

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: `HỢP LỆ: 6/6 panel có trong dashboard contract.` Evidence: `submission/evidence/validate_dashboard.txt` và `submission/evidence/cp2_validate_dashboard_result.txt`.
- Evidence dashboard: `submission/evidence/dashboard_runtime.png` và `submission/evidence/dashboard_runtime.html`. Evidence text hiện có: `submission/evidence/cp3_challenge_summary.txt`.
- SLO đã chọn và lý do: Giữ 4 SLI chính trong `config/slo.yaml` (`latency_p95_ms` <= 3000ms, `error_rate_pct` <= 2%, `daily_cost_usd` <= 2.5 USD, `quality_score_avg` >= 0.75) vì khớp threshold của `config/dashboard.yaml`; baseline/practice thực tế cho thấy còn dư địa hợp lý để phát hiện incident thay vì báo động giả, đồng thời bao phủ trải nghiệm người dùng, độ ổn định, chi phí vận hành và proxy chất lượng.
- Alert rules và runbook: 3 alert symptom-based trong `config/alert_rules.yaml`, chi tiết đầy đủ trong `docs/alerts.md`:
  1. `high_latency_p95` (warning) - `latency_p95_ms > 3000` duy trì 5 phút. Practice `rag_slow`: `/metrics` cho latency_p95 tăng từ 152ms lên 2651ms khi bật incident, giảm lại sau khi tắt.
  2. `elevated_error_rate` (critical) - `error_rate_pct > 2%` duy trì 5 phút. Practice `tool_fail`: 10/10 request trả `500 RuntimeError` khi bật incident.
  3. `daily_cost_budget_burn` (warning) - `daily_cost_usd > 2.5` trong cửa sổ rolling 24h. Practice `cost_spike`: avg cost/request tăng từ 0.0020 USD lên 0.0037 USD.

## 6. Điều tra challenge

- Challenge ID: `day13-k4-observability-v1`.
- Triệu chứng từ metrics: Challenge chính thức đã chạy với incident `rag_slow`, feature `monitoring`. Từ `data/logs.jsonl`, baseline non-monitoring có P95 1246 ms; challenge monitoring có P95 3778 ms, vượt `latency_threshold_ms=2000` trong `config/challenge.json` và vượt SLO latency P95 3000 ms. `/metrics` sau challenge ghi `latency_p95=3778`, `traffic=15`, `error_breakdown={}`, `quality_avg=0.8667`.
- Evidence terminal challenge: `submission/evidence/cp3_challenge_terminal.png`.
- Trace ID liên quan: `5ca44c966168c26f54b39955c7c4d365` tương ứng query `Explain why metrics traces and logs work together.`; các trace challenge khác: `a1a4166368e2646e14dbcb8860b48d7c`, `59acda004a68e42e40fd77e85e528bf7`, `6aa5a7a75a0d6f172a2096600a639bd8`, `ab46836e6effc2bdfbad6c1b25f8dcbe`. Evidence: `submission/evidence/cp3_trace_ids.txt`.
- Log line/correlation ID liên quan: `req-87ff605a` trong event `response_sent`, `feature=monitoring`, `latency_ms=3778`; log điều khiển `req-33b3113a` ghi `incident_enabled` với payload `rag_slow`. Evidence: `submission/evidence/cp3_log_evidence.jsonl`.
- Root cause: Metrics cho thấy latency tăng tập trung ở feature `monitoring`; trace cùng query xác nhận request thuộc luồng agent/RAG; log cùng correlation ID chứng minh request hoàn thành thành công nhưng chậm, không phải lỗi HTTP. Đối chiếu challenge config và incident flag cho thấy root cause là incident `rag_slow`: tầng RAG/retrieval bị làm chậm.
- Fix action: Đã tắt incident sau khi lấy evidence bằng `python scripts/inject_incident.py --disable`, kết quả `rag_slow=False`. Trong production, fix tương ứng là rollback cấu hình RAG chậm hoặc bật timeout/cache/fallback cho retrieval.
- Preventive measure: Alert `high_latency_p95`, runbook mở trace chậm và tìm log cùng correlation ID.

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Lê Minh Đạt - 2A202601088 | Role C - Validate dashboard contract, phụ trách dashboard spec, load test, Practice/Challenge Incident CP3 và tổng hợp report nhóm | `043ffc5` | Hiểu cách chuyển dashboard contract thành 6 panel quan sát latency, traffic, errors, cost, tokens và quality; biết quy trình CP3 Metrics -> Traces -> Logs. |
| Nguyễn Minh Quang - 2A202601730 | Role B - Langfuse config, SLO/Alert, alert runbook; định nghĩa 3 alert symptom-based và verify practice incident `rag_slow`, `tool_fail`, `cost_spike` | `4e3c5f0`, `7d3ec71`, `2cc2bbe`, `9cd6371` (điền link GitHub sau khi push) | Hiểu cách tách lỗi kết nối Langfuse với lỗi thiếu prompt object; alert nên gắn với triệu chứng/SLO thay vì tên hàm nội bộ. |
| Lệnh Quang Hưng - 2A202601546 | Role A - Hoàn thiện `app/middleware.py`, `app/main.py`, `app/logging_config.py`, `app/pii.py`; kết quả `validate_logs.py` 100/100 và không còn PII thô trong log mẫu | `eb45027` | Hiểu vai trò của `clear_contextvars()`, correlation ID và thứ tự processor trong structlog để đảm bảo PII được che trước khi ghi log. |
