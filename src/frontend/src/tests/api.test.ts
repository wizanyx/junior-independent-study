import { describe, expect, test, vi, beforeEach, afterEach } from 'vitest';
// We'll import the module under test dynamically after stubbing env

describe('lib/api', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.resetModules();
    // Provide Vite-style env for the module import
    vi.stubEnv('VITE_API_BASE_URL', 'http://api.test');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  test('fetchMetrics builds URL and returns JSON', async () => {
    const { fetchMetrics } = await import('../lib/api.ts');
    const params = new URLSearchParams({ a: '1', b: '2' });

    const payload = { ok: true };
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => payload,
    } as unknown as Response);

    const res = await fetchMetrics(params);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledWith('http://api.test/metrics?a=1&b=2');
    expect(res).toEqual(payload);
  });

  test('fetchMetrics throws on non-ok response', async () => {
    const { fetchMetrics } = await import('../lib/api.ts');
    const params = new URLSearchParams();

    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => ({}),
    } as unknown as Response);

    await expect(fetchMetrics(params)).rejects.toThrow('Metrics error: 500');
  });
});
