import { useMemo, useRef, useState } from "react";

import { downloadText, simulateWarehouse } from "./api";
import TrendChart from "./TrendChart";
import "./styles.css";

const LOCATION_NAMES = { A: "Kho lạnh", B: "Kho khô", C: "Phòng máy chủ" };

function KpiCard({ label, value, tone = "default" }) {
  return (
    <article className={`kpi-card tone-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  );
}
function StatusBadge({ value }) {
  return <span className={`status status-${value.toLowerCase()}`}>{value}</span>;
}

export default function App({ apiClient = simulateWarehouse }) {
  const [mssv, setMssv] = useState("2312345");
  const [steps, setSteps] = useState(10);
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const requestGeneration = useRef(0);

  const kpis = useMemo(() => {
    const alerts = result?.alerts ?? [];
    return {
      sensors: result?.sensors.length ?? 0,
      locations: new Set((result?.sensors ?? []).map((item) => item.location_id)).size,
      warning: alerts.filter((item) => item.severity === "WARNING").length,
      critical: alerts.filter((item) => item.severity === "CRITICAL").length,
      errors: result?.errors.length ?? 0,
    };
  }, [result]);

  async function handleSubmit(event) {
    event.preventDefault();
    const currentGeneration = ++requestGeneration.current;
    setStatus("loading");
    setError("");
    try {
      const data = await apiClient({ mssv: mssv.trim(), steps: Number(steps) });
      if (currentGeneration !== requestGeneration.current) return;
      setResult(data);
      setStatus("success");
    } catch (requestError) {
      if (currentGeneration !== requestGeneration.current) return;
      setResult(null);
      setError(requestError.message || "Không thể kết nối API.");
      setStatus("error");
    }
  }

  function handleReset() {
    requestGeneration.current += 1;
    setResult(null);
    setError("");
    setStatus("idle");
    setMssv("2312345");
    setSteps(10);
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#main"><span className="brand-mark">W</span><span>Warehouse <b>Pulse</b></span></a>
        <div className="live-pill"><i /> Dữ liệu mô phỏng deterministic</div>
      </header>

      <main id="main">
        <section className="hero">
          <div className="hero-copy">
            <span className="eyebrow">Chủ đề 36 · Python OOP Core</span>
            <h1>Giám sát nhà kho,<br /><em>nhìn thấy bất thường ngay.</em></h1>
            <p>Điều khiển phiên mô phỏng từ MSSV, theo dõi cảm biến theo từng bước và tách bạch cảnh báo môi trường với lỗi thiết bị.</p>
          </div>
          <form className="control-panel" onSubmit={handleSubmit}>
            <div className="panel-heading"><span>Thiết lập phiên</span><small>Tối đa 200 bước</small></div>
            <label>Mã số sinh viên<input value={mssv} maxLength="64" onChange={(event) => setMssv(event.target.value)} required /></label>
            <label>Số bước mô phỏng<input type="number" min="1" max="200" value={steps} onChange={(event) => setSteps(event.target.value)} required /></label>
            <div className="form-actions">
              <button className="primary-button" disabled={status === "loading"}>{status === "loading" ? "Đang mô phỏng…" : "Bắt đầu mô phỏng"}</button>
              <button type="button" className="secondary-button" onClick={handleReset}>Đặt lại</button>
            </div>
            {error && <div role="alert" className="error-box">{error}</div>}
          </form>
        </section>

        {!result ? (
          <section className="empty-state">
            <div className="empty-icon">⌁</div>
            <h2>Chưa có phiên mô phỏng</h2>
            <p>Nhập MSSV và chọn số bước để nhận dữ liệu thực từ Python API.</p>
          </section>
        ) : (
          <div className="dashboard">
            <section className="section-heading"><div><span className="eyebrow">Phiên {result.session.mssv}</span><h2>Tổng quan vận hành</h2></div><span>{result.session.steps} time-step</span></section>
            <section className="kpi-grid">
              <KpiCard label="Cảm biến" value={kpis.sensors} />
              <KpiCard label="Khu vực" value={kpis.locations} />
              <KpiCard label="Warning" value={kpis.warning} tone="warning" />
              <KpiCard label="Critical" value={kpis.critical} tone="critical" />
              <KpiCard label="Lỗi thiết bị" value={kpis.errors} tone="error" />
            </section>

            <section className="sensor-section">
              <div className="section-heading"><div><span className="eyebrow">Snapshot cuối phiên</span><h2>Trạng thái cảm biến</h2></div></div>
              <div className="sensor-grid">
                {result.sensors.map((sensor) => (
                  <article className="sensor-card" key={sensor.sensor_id}>
                    <div className="sensor-title"><div><small>{LOCATION_NAMES[sensor.location_id] ?? sensor.location_id}</small><h3>{sensor.sensor_id}</h3></div><StatusBadge value={sensor.status} /></div>
                    <div className="reading-row"><div><span>Nhiệt độ</span><strong>{sensor.temperature ?? "—"}<small> °C</small></strong></div><div><span>Độ ẩm</span><strong>{sensor.humidity ?? "—"}<small> %</small></strong></div></div>
                    <footer>{sensor.sensor_type.replaceAll("_", " ")}</footer>
                  </article>
                ))}
              </div>
            </section>

            <section className="location-section">
              <div className="section-heading"><div><span className="eyebrow">Phân bố cảnh báo</span><h2>Thống kê theo vị trí</h2></div></div>
              <div className="location-grid">
                {[...new Set(result.sensors.map((sensor) => sensor.location_id))].map((locationId) => {
                  const counts = result.summary.by_location[locationId] ?? { WARNING: 0, CRITICAL: 0, total: 0 };
                  return (
                    <article className="location-card" key={locationId}>
                      <strong>{LOCATION_NAMES[locationId] ?? "Khu vực"} ({locationId})</strong>
                      <span>WARNING <b>{counts.WARNING}</b></span>
                      <span>CRITICAL <b>{counts.CRITICAL}</b></span>
                      <span>Tổng <b>{counts.total}</b></span>
                    </article>
                  );
                })}
              </div>
            </section>

            <section className="charts-grid">
              <TrendChart timeline={result.timeline} metric="temperature" title="Nhiệt độ" unit="°C" />
              <TrendChart timeline={result.timeline} metric="humidity" title="Độ ẩm" unit="%" />
            </section>

            <section className="event-grid">
              <article className="event-panel">
                <div className="panel-heading"><div><span className="eyebrow">Môi trường</span><h2>Cảnh báo</h2></div><b>{result.alerts.length}</b></div>
                {result.alerts.length ? result.alerts.map((alert, index) => (
                  <div className="event-row" key={`${alert.sensor_id}-${alert.timestamp}-${index}`}>
                    <StatusBadge value={alert.severity} />
                    <div><strong>{alert.sensor_id} · {LOCATION_NAMES[alert.location_id]}</strong><span>{alert.violated_metrics.join(", ")} · {alert.timestamp}</span></div>
                  </div>
                )) : <p className="quiet-state">Không có cảnh báo môi trường.</p>}
              </article>
              <article className="event-panel">
                <div className="panel-heading"><div><span className="eyebrow">Thiết bị & dữ liệu</span><h2>Lỗi hệ thống</h2></div><b>{result.errors.length}</b></div>
                {result.errors.length ? result.errors.map((item, index) => (
                  <div className="event-row" key={`${item.sensor_id}-${item.timestamp}-${index}`}>
                    <StatusBadge value="ERROR" />
                    <div><strong>{item.sensor_id} · {item.error_type}</strong><span>{item.message} · {item.timestamp}</span></div>
                  </div>
                )) : <p className="quiet-state">Không có lỗi thiết bị hoặc dữ liệu.</p>}
              </article>
            </section>

            <section className="report-panel">
              <div><span className="eyebrow">Báo cáo phiên</span><h2>Tải dữ liệu đã hiển thị</h2><p>CSV chứa cảnh báo môi trường; JSON chứa toàn bộ timeline, snapshot, alerts, errors và summary.</p></div>
              <div className="download-actions">
                <button onClick={() => downloadText("alert_logs.csv", result.downloads.csv, "text/csv;charset=utf-8")}>Tải CSV</button>
                <button onClick={() => downloadText("report.json", JSON.stringify(result.downloads.json, null, 2), "application/json")}>Tải JSON</button>
              </div>
            </section>
          </div>
        )}
      </main>
      <footer className="page-footer">IoT Warehouse Monitoring System · Dữ liệu chỉ dùng cho mô phỏng học tập</footer>
    </div>
  );
}
