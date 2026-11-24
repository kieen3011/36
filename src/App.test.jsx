import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import App from "./App";

const result = {
  session: {
    mssv: "2312345",
    steps: 1,
    started_at: "2026-11-23T00:00:00+07:00",
    ended_at: "2026-11-23T00:00:00+07:00",
  },
  sensors: [
    {
      sensor_id: "COLD-01",
      sensor_type: "COLD_STORAGE",
      location_id: "A",
      status: "ACTIVE",
      temperature: 11,
      humidity: 90,
      timestamp: "2026-11-23T00:00:00+07:00",
    },
  ],
  timeline: [],
  alerts: [
    {
      sensor_id: "COLD-01",
      location_id: "A",
      timestamp: "2026-11-23T00:00:00+07:00",
      severity: "CRITICAL",
      violated_metrics: ["temperature"],
      temperature: 11,
      humidity: 90,
    },
  ],
  errors: [],
  summary: {
    total_alerts: 1,
    total_errors: 0,
    by_location: { A: { WARNING: 0, CRITICAL: 1, total: 1 } },
    errors_by_type: {},
  },
  downloads: { csv: "sensor_id\nCOLD-01\n", json: {} },
};

describe("Warehouse dashboard", () => {
  it("shows an empty state before the first simulation", () => {
    render(<App apiClient={vi.fn()} />);

    expect(screen.getByText(/chưa có phiên mô phỏng/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /bắt đầu mô phỏng/i })).toBeEnabled();
  });

  it("shows loading and then real session data", async () => {
    let resolveRequest;
    const apiClient = vi.fn(
      () => new Promise((resolve) => { resolveRequest = resolve; }),
    );
    render(<App apiClient={apiClient} />);

    fireEvent.click(screen.getByRole("button", { name: /bắt đầu mô phỏng/i }));
    expect(screen.getByRole("button", { name: /đang mô phỏng/i })).toBeDisabled();

    resolveRequest(result);
    expect(await screen.findByText("COLD-01")).toBeInTheDocument();
    expect(screen.getAllByText(/CRITICAL/).length).toBeGreaterThan(0);
    expect(screen.getByRole("heading", { name: /thống kê theo vị trí/i })).toBeInTheDocument();
    expect(screen.getByText("Kho lạnh (A)")).toBeInTheDocument();
  });

  it("shows an API error and can reset the dashboard", async () => {
    const apiClient = vi.fn().mockRejectedValue(new Error("API unavailable"));
    render(<App apiClient={apiClient} />);

    fireEvent.click(screen.getByRole("button", { name: /bắt đầu mô phỏng/i }));
    expect(await screen.findByRole("alert")).toHaveTextContent("API unavailable");

    fireEvent.click(screen.getByRole("button", { name: /đặt lại/i }));
    await waitFor(() => {
      expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    });
    expect(screen.getByText(/chưa có phiên mô phỏng/i)).toBeInTheDocument();
  });

  it("does not restore stale data when reset wins a pending request", async () => {
    let resolveRequest;
    const apiClient = vi.fn(
      () => new Promise((resolve) => { resolveRequest = resolve; }),
    );
    render(<App apiClient={apiClient} />);

    fireEvent.click(screen.getByRole("button", { name: /bắt đầu mô phỏng/i }));
    fireEvent.click(screen.getByRole("button", { name: /đặt lại/i }));
    resolveRequest(result);

    await waitFor(() => {
      expect(screen.queryByText("COLD-01")).not.toBeInTheDocument();
    });
    expect(screen.getByText(/chưa có phiên mô phỏng/i)).toBeInTheDocument();
  });
});
