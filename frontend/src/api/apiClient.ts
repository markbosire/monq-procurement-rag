/**
 * Centralised HTTP client for all API calls.
 *
 * Wraps the native fetch API with consistent error handling and typed
 * response parsing. Every module-level function raises {@link ApiError}
 * on non-2xx responses so that callers can rely on a single error shape.
 *
 * @packageDocumentation
 * @since 1.0.0
 */

// ── Errors ──────────────────────────────────────────────────────────

/**
 * Structured error thrown by all API functions when the server returns
 * a non-2xx status code.
 */
export class ApiError extends Error {
  /** HTTP status code returned by the server. */
  status: number

  /**
   * @param status  - HTTP status code.
   * @param message - Human-readable error detail.
   */
  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// ── Client ─────────────────────────────────────────────────────────

/**
 * Perform a typed GET or POST request and parse the JSON response.
 *
 * @typeParam T - Expected shape of the response body.
 * @param url     - Full or relative URL to fetch.
 * @param options - Optional fetch overrides (method, headers, body, etc.).
 * @returns       Parsed response body of type T.
 * @throws {ApiError} When the server responds with a non-2xx status.
 */
export async function apiFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(res.status, body.detail || `Request failed with status ${res.status}`)
  }
  return res.json() as Promise<T>
}

/**
 * Perform a fetch request and return the raw {@link Response} object.
 *
 * Useful for endpoints that return non-JSON payloads (e.g. binary PDF data).
 *
 * @param url     - Full or relative URL to fetch.
 * @param options - Optional fetch overrides.
 * @returns       The raw Response object.
 * @throws {ApiError} When the server responds with a non-2xx status.
 */
export async function apiFetchRaw(url: string, options?: RequestInit): Promise<Response> {
  const res = await fetch(url, options)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(res.status, body.detail || `Request failed with status ${res.status}`)
  }
  return res
}
