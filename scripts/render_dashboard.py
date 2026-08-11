from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"
OUTPUT_PATH = REPO_ROOT / "submission" / "evidence" / "dashboard_runtime.html"


def load_records() -> list[dict]:
    if not LOG_PATH.exists():
        raise SystemExit("data/logs.jsonl not found. Run the API and load_test.py first.")

    records: list[dict] = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def percentile(values: list[float], p: int) -> float:
    if not values:
        return 0.0
    items = sorted(values)
    idx = max(0, min(len(items) - 1, round((p / 100) * len(items) + 0.5) - 1))
    return float(items[idx])


def fmt(value: float, digits: int = 1) -> str:
    if value == int(value):
        return str(int(value))
    return f"{value:.{digits}f}"


def status_class(value: float, operator: str, threshold: float) -> str:
    ok = value <= threshold if operator == "lte" else value >= threshold
    return "ok" if ok else "warn"


def render_panel(title: str, subtitle: str, metrics: list[tuple[str, str]], threshold: str, status: str) -> str:
    metrics_html = "\n".join(
        f'<div class="metric"><span>{label}</span><strong>{value}</strong></div>'
        for label, value in metrics
    )
    return f"""
      <section class="panel {status}">
        <div class="panel-head">
          <h2>{title}</h2>
          <span>{subtitle}</span>
        </div>
        <div class="metric-grid">
          {metrics_html}
        </div>
        <div class="threshold">Threshold: {threshold}</div>
      </section>
    """


def main() -> int:
    records = load_records()
    responses = [record for record in records if record.get("event") == "response_sent"]
    requests = [record for record in records if record.get("event") == "request_received"]
    failures = [record for record in records if record.get("event") == "request_failed"]

    latencies = [float(record.get("latency_ms", 0)) for record in responses]
    costs = [float(record.get("cost_usd", 0)) for record in responses]
    tokens_in = [int(record.get("tokens_in", 0)) for record in responses]
    tokens_out = [int(record.get("tokens_out", 0)) for record in responses]
    quality = [float(record.get("quality_score", 0)) for record in responses]
    error_types = Counter(record.get("error_type", "unknown") for record in failures)

    p50 = percentile(latencies, 50)
    p95 = percentile(latencies, 95)
    p99 = percentile(latencies, 99)
    request_count = len(requests)
    rate_per_minute = request_count / 60
    error_rate = (len(failures) / request_count * 100) if request_count else 0.0
    total_cost = sum(costs)
    total_tokens = sum(tokens_in) + sum(tokens_out)
    quality_avg = mean(quality) if quality else 0.0

    error_breakdown = ", ".join(f"{kind}: {count}" for kind, count in sorted(error_types.items()))
    if not error_breakdown:
        error_breakdown = "none"

    panels = [
        render_panel(
            "Latency Percentiles",
            "event=response_sent, unit=ms",
            [("P50", f"{fmt(p50)} ms"), ("P95", f"{fmt(p95)} ms"), ("P99", f"{fmt(p99)} ms")],
            "P95 <= 3000 ms",
            status_class(p95, "lte", 3000),
        ),
        render_panel(
            "Request Traffic",
            "event=request_received, unit=requests/min",
            [("Count", str(request_count)), ("Rate", f"{rate_per_minute:.2f}/min")],
            "rate_per_minute >= 1",
            status_class(rate_per_minute, "gte", 1),
        ),
        render_panel(
            "Error Rate And Breakdown",
            "events=request_received/request_failed, unit=percent",
            [("Error Rate", f"{error_rate:.2f}%"), ("Failures", str(len(failures))), ("Breakdown", error_breakdown)],
            "error_rate_pct <= 2%",
            status_class(error_rate, "lte", 2),
        ),
        render_panel(
            "Cost Over Time",
            "event=response_sent, unit=USD",
            [("Total", f"${total_cost:.4f}"), ("Avg/Request", f"${mean(costs):.4f}" if costs else "$0.0000")],
            "total <= $2.5",
            status_class(total_cost, "lte", 2.5),
        ),
        render_panel(
            "Input And Output Tokens",
            "event=response_sent, unit=tokens",
            [("Input", str(sum(tokens_in))), ("Output", str(sum(tokens_out))), ("Total", str(total_tokens))],
            "sum_by_field <= 50000",
            status_class(total_tokens, "lte", 50000),
        ),
        render_panel(
            "Quality Proxy",
            "event=response_sent, unit=score_0_to_1",
            [("Mean", f"{quality_avg:.4f}"), ("Samples", str(len(quality)))],
            "mean >= 0.75",
            status_class(quality_avg, "gte", 0.75),
        ),
    ]

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="30">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Day 13 AI Observability Dashboard</title>
  <style>
    :root {{
      --bg: #f6f7f9;
      --surface: #ffffff;
      --text: #20242b;
      --muted: #657084;
      --line: #d8dee8;
      --ok: #0f766e;
      --warn: #b42318;
      --accent: #2563eb;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: Arial, Helvetica, sans-serif;
      letter-spacing: 0;
    }}
    header {{
      padding: 24px 28px 14px;
      border-bottom: 1px solid var(--line);
      background: var(--surface);
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: 28px;
      font-weight: 700;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px 18px;
      color: var(--muted);
      font-size: 13px;
    }}
    main {{
      padding: 22px 28px 28px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }}
    .panel {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-left: 5px solid var(--accent);
      border-radius: 8px;
      padding: 16px;
      min-height: 190px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .panel.ok {{ border-left-color: var(--ok); }}
    .panel.warn {{ border-left-color: var(--warn); }}
    .panel-head h2 {{
      margin: 0 0 6px;
      font-size: 17px;
      font-weight: 700;
    }}
    .panel-head span {{
      color: var(--muted);
      font-size: 12px;
      line-height: 1.35;
    }}
    .metric-grid {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin: 18px 0 14px;
    }}
    .metric {{
      border-top: 1px solid var(--line);
      padding-top: 8px;
      min-width: 0;
    }}
    .metric span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-bottom: 3px;
    }}
    .metric strong {{
      display: block;
      font-size: 20px;
      line-height: 1.15;
      overflow-wrap: anywhere;
    }}
    .threshold {{
      color: var(--muted);
      font-size: 12px;
      border-top: 1px solid var(--line);
      padding-top: 10px;
    }}
    @media (max-width: 1000px) {{
      .grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 680px) {{
      header, main {{ padding-left: 16px; padding-right: 16px; }}
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>Day 13 AI Observability Dashboard</h1>
    <div class="meta">
      <span>Source: data/logs.jsonl</span>
      <span>Time range: last 60 minutes</span>
      <span>Refresh: 30 seconds</span>
      <span>Generated: {generated_at}</span>
      <span>Total log records: {len(records)}</span>
    </div>
  </header>
  <main>
    <div class="grid">
      {''.join(panels)}
    </div>
  </main>
</body>
</html>
"""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
