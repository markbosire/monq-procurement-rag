import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiFetch, apiFetchRaw, ApiError } from '../apiClient'

beforeEach(() => {
  vi.restoreAllMocks()
})

function mockFetch(status: number, body: unknown, ok?: boolean) {
  const isOk = ok ?? (status >= 200 && status < 300)
  return vi.spyOn(globalThis, 'fetch').mockResolvedValue({
    ok: isOk,
    status,
    json: () => Promise.resolve(body),
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(0)),
  } as Response)
}

describe('apiFetch', () => {
  it('returns parsed JSON on successful GET', async () => {
    mockFetch(200, { key: 'value' })
    const result = await apiFetch<{ key: string }>('/api/test')
    expect(result).toEqual({ key: 'value' })
  })

  it('passes options to fetch', async () => {
    const spy = mockFetch(201, { id: 1 })
    const body = JSON.stringify({ name: 'test' })
    await apiFetch('/api/test', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body })
    expect(spy).toHaveBeenCalledWith('/api/test', expect.objectContaining({ method: 'POST', body }))
  })

  it('throws ApiError on non-2xx response', async () => {
    mockFetch(404, { detail: 'Not found' }, false)
    await expect(apiFetch('/api/test')).rejects.toThrow(ApiError)
  })

  it('throws ApiError with status and detail from body', async () => {
    mockFetch(400, { detail: 'Bad request' }, false)
    try {
      await apiFetch('/api/test')
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError)
      expect((e as ApiError).status).toBe(400)
      expect((e as ApiError).message).toBe('Bad request')
    }
  })

  it('falls back to status message when no detail in body', async () => {
    mockFetch(500, {}, false)
    try {
      await apiFetch('/api/test')
    } catch (e) {
      expect((e as ApiError).message).toBe('Request failed with status 500')
    }
  })
})

describe('apiFetchRaw', () => {
  it('returns raw Response on success', async () => {
    const spy = mockFetch(200, {})
    const res = await apiFetchRaw('/api/test')
    expect(res).toBeDefined()
    expect(spy).toHaveBeenCalledWith('/api/test', undefined)
  })

  it('throws ApiError on non-2xx response', async () => {
    mockFetch(403, { detail: 'Forbidden' }, false)
    await expect(apiFetchRaw('/api/test')).rejects.toThrow(ApiError)
  })
})
