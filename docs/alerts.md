# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: `high_latency_p95`
- Severity: Warning
- SLI/SLO liên quan: `latency_p95_ms` trong `config/slo.yaml`, objective ≤ 3000ms (target 99.5%). Tương ứng panel Latency trong `config/dashboard.yaml`.
- Điều kiện và thời gian duy trì: P95 latency của `response_sent` vượt 3000ms, duy trì liên tục 5 phút (tránh cảnh báo do một request đơn lẻ chậm bất thường).
- Ảnh hưởng tới người dùng: Người dùng chờ phản hồi chat lâu bất thường, trải nghiệm giống ứng dụng bị treo; có thể kéo theo timeout ở phía client.
- Ba bước kiểm tra đầu tiên:
  1. Metrics: mở panel Latency trên dashboard, xác nhận P95/P99 đang vượt threshold và thời điểm bắt đầu tăng.
  2. Traces: trên Langfuse, lọc trace trong cùng khung giờ theo `latency`, mở waterfall của trace chậm nhất để xác định span nào (RAG, LLM call, tool call) chiếm phần lớn thời gian.
  3. Logs: lấy `correlation_id` của trace đó, tìm trong `data/logs.jsonl` để xem `feature`, `model`, `error_type` (nếu có) và log ngay trước/sau để xác nhận không có lỗi hạ tầng khác đi kèm.
- Mitigation tạm thời: Nếu span chậm nằm ở RAG/tool call, giảm concurrency của load test hoặc tạm chuyển traffic sang fallback nhanh hơn; theo dõi tới khi P95 về dưới ngưỡng trước khi mở lại traffic đầy đủ.
- Owner: Optics

## Alert 2

- Tên: `elevated_error_rate`
- Severity: Critical
- SLI/SLO liên quan: `error_rate_pct` trong `config/slo.yaml`, objective ≤ 2% (target 99.0%). Tương ứng panel Errors trong `config/dashboard.yaml`.
- Điều kiện và thời gian duy trì: Tỷ lệ `request_failed`/`request_received` vượt 2%, duy trì liên tục 5 phút.
- Ảnh hưởng tới người dùng: Một phần request bị lỗi, người dùng nhận thông báo lỗi hoặc không có phản hồi thay vì câu trả lời.
- Ba bước kiểm tra đầu tiên:
  1. Metrics: mở panel Errors, xem error rate hiện tại và breakdown theo `error_type` để biết lỗi nào chiếm đa số.
  2. Traces: trên Langfuse, lọc trace có status lỗi trong cùng khung giờ, mở một trace lỗi để xem span/tool call nào ném exception.
  3. Logs: dùng `correlation_id` của trace lỗi để tra `data/logs.jsonl`, đọc `error_type` và message kèm theo để xác nhận nguyên nhân (vd. tool/dependency fail).
- Mitigation tạm thời: Nếu lỗi tập trung ở một loại tool/dependency cụ thể, tạm thời disable tool đó hoặc trả fallback response; thông báo mức độ ảnh hưởng cho nhóm trước khi điều tra sâu.
- Owner: Optics

## Alert 3

- Tên: `daily_cost_budget_burn`
- Severity: Warning
- SLI/SLO liên quan: `daily_cost_usd` trong `config/slo.yaml`, objective ≤ $2.5/ngày (target 100%). Tương ứng panel Cost trong `config/dashboard.yaml`.
- Điều kiện và thời gian duy trì: Tổng `cost_usd` cộng dồn trong cửa sổ rolling 24h vượt $2.5, hoặc tốc độ chi tiêu theo phút tăng đột biến so với baseline.
- Ảnh hưởng tới người dùng: Không ảnh hưởng trực tiếp tới trải nghiệm ngay lập tức, nhưng báo hiệu rủi ro vượt ngân sách vận hành hoặc dấu hiệu bị lạm dụng (spam request, prompt quá dài).
- Ba bước kiểm tra đầu tiên:
  1. Metrics: mở panel Cost, xác nhận tổng cost theo phút/toàn cửa sổ và so với threshold; đối chiếu panel Tokens xem tokens_in/tokens_out có tăng bất thường không.
  2. Traces: trên Langfuse, sắp xếp trace theo cost hoặc token cao nhất trong khung giờ để tìm request đắt nhất.
  3. Logs: dùng `correlation_id` của trace đó để tra `data/logs.jsonl`, kiểm tra `feature`, độ dài prompt/`tokens_in` để xác nhận có phải do input bất thường hay do lặp request.
- Mitigation tạm thời: Giới hạn tạm thời độ dài input hoặc rate limit theo `session_id`/`user_id_hash` cho tới khi xác định nguyên nhân; nếu do một feature cụ thể, có thể tạm tắt feature đó.
- Owner: Optics
