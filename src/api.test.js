import { afterEach, describe, expect, it, vi } from "vitest";

import { downloadText, simulateWarehouse } from "./api";

describe("Web API client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("posts the exact simulation payload", async () => {
    const responseBody = { session: { mssv: "2312345", steps: 3 } };
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue(responseBody),
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(simulateWarehouse({ mssv: "2312345", steps: 3 })).resolves.toEqual(responseBody);
    expect(fetchMock).toHaveBeenCalledWith("/api/simulate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mssv: "2312345", steps: 3 }),
    });
  });

  it("shows the safe API error detail", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: false,
      json: vi.fn().mockResolvedValue({ detail: "Dữ liệu không hợp lệ" }),
    }));

    await expect(simulateWarehouse({ mssv: "", steps: 0 })).rejects.toThrow("Dữ liệu không hợp lệ");
  });

  it("downloads exactly the provided session content", () => {
    const createObjectURL = vi.fn().mockReturnValue("blob:session");
    const revokeObjectURL = vi.fn();
    vi.stubGlobal("URL", { createObjectURL, revokeObjectURL });
    const click = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

    downloadText("report.json", '{"mssv":"2312345"}', "application/json");

    const blob = createObjectURL.mock.calls[0][0];
    expect(blob.type).toBe("application/json");
    expect(click).toHaveBeenCalledOnce();
    expect(revokeObjectURL).toHaveBeenCalledWith("blob:session");
  });
});
