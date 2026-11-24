import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import TrendChart from "./TrendChart";

describe("TrendChart", () => {
  it("does not draw stale readings or bridge a disconnected interval", () => {
    const timeline = [
      { step_index: 0, timestamp: "2026-11-23T00:00:00+07:00", readings: [{ sensor_id: "COLD-01", status: "ACTIVE", timestamp: "2026-11-23T00:00:00+07:00", temperature: 4.8 }] },
      { step_index: 1, timestamp: "2026-11-23T00:01:00+07:00", readings: [{ sensor_id: "COLD-01", status: "ERROR", timestamp: "2026-11-23T00:00:00+07:00", temperature: 4.8 }] },
      { step_index: 2, timestamp: "2026-11-23T00:02:00+07:00", readings: [{ sensor_id: "COLD-01", status: "ACTIVE", timestamp: "2026-11-23T00:00:00+07:00", temperature: 4.8 }] },
      { step_index: 3, timestamp: "2026-11-23T00:03:00+07:00", readings: [{ sensor_id: "COLD-01", status: "ACTIVE", timestamp: "2026-11-23T00:03:00+07:00", temperature: 5.1 }] },
    ];

    render(<TrendChart timeline={timeline} metric="temperature" title="Nhiệt độ" unit="°C" />);

    const chart = screen.getByRole("img", { name: /nhiệt độ theo time-step/i });
    expect(chart.querySelectorAll("polyline")).toHaveLength(0);
    expect(chart.querySelectorAll("circle")).toHaveLength(2);
  });
});
