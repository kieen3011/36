const COLORS = ["#1dd3b0", "#ffb703", "#7c83fd"];

function buildSeries(timeline, metric) {
  const ids = [...new Set(timeline.flatMap((step) => step.readings.map((item) => item.sensor_id)))];
  return ids.map((sensorId, index) => ({
    sensorId,
    color: COLORS[index % COLORS.length],
    values: timeline.map((step) => {
      const reading = step.readings.find((item) => item.sensor_id === sensorId);
      const isCurrent = reading?.status === "ACTIVE" && reading.timestamp === step.timestamp;
      return isCurrent ? reading?.[metric] ?? null : null;
    }),
  }));
}
function splitSegments(values) {
  const segments = [];
  let current = [];
  values.forEach((value, index) => {
    if (value === null) {
      if (current.length) segments.push(current);
      current = [];
    } else {
      current.push({ index, value });
    }
  });
  if (current.length) segments.push(current);
  return segments;
}

export default function TrendChart({ timeline, metric, title, unit }) {
  if (!timeline.length) {
    return <div className="chart-empty">Chưa có dữ liệu chuỗi thời gian.</div>;
  }

  const series = buildSeries(timeline, metric);
  const values = series.flatMap((item) => item.values).filter((value) => value !== null);
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const spread = maximum - minimum || 1;
  const width = 720;
  const height = 260;
  const padding = 34;
  const x = (index) => padding + (index * (width - padding * 2)) / Math.max(timeline.length - 1, 1);
  const y = (value) => height - padding - ((value - minimum) / spread) * (height - padding * 2);

  return (
    <div className="chart-card">
      <div className="chart-heading">
        <div>
          <span className="eyebrow">Theo time-step</span>
          <h3>{title}</h3>
        </div>
        <strong>{unit}</strong>
      </div>
      <svg role="img" aria-label={`${title} theo time-step`} viewBox={`0 0 ${width} ${height}`}>
        <title>{title}</title>
        {[0, 1, 2, 3].map((line) => {
          const lineY = padding + (line * (height - padding * 2)) / 3;
          return <line key={line} x1={padding} x2={width - padding} y1={lineY} y2={lineY} className="grid-line" />;
        })}
        {series.map((item) => (
          <g key={item.sensorId} data-sensor-id={item.sensorId}>
            {splitSegments(item.values).filter((segment) => segment.length > 1).map((segment, index) => (
              <polyline key={index} points={segment.map((point) => `${x(point.index)},${y(point.value)}`).join(" ")} fill="none" stroke={item.color} strokeWidth="4" strokeLinejoin="round" strokeLinecap="round" />
            ))}
            {item.values.map((value, index) => value === null ? null : <circle key={index} cx={x(index)} cy={y(value)} r="4" fill={item.color} />)}
          </g>
        ))}
      </svg>
      <div className="legend">
        {series.map((item) => (
          <span key={item.sensorId}><i style={{ background: item.color }} />{item.sensorId}</span>
        ))}
      </div>
      <div className="chart-range">Min {minimum.toFixed(2)} · Max {maximum.toFixed(2)}</div>
    </div>
  );
}
