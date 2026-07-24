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

import { useToast } from '../composables/useToast'

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

/** Common phrases in backend error messages that indicate a bad Groq API key. */
const GROQ_KEY_ERRORS = [
  'GROQ_API_KEY',
  'Invalid API Key',
  'invalid_api_key',
]

/**
 * Show a persistent toast if the error message indicates a bad Groq API key.
 *
 * Called once per session – subsequent calls are no-ops after the first toast.
 */
let _groqKeyToastShown = false
function _warnIfGroqKeyError(message: string) {
  if (_groqKeyToastShown) return
  const isKeyError = GROQ_KEY_ERRORS.some(kw => message.includes(kw))
  if (isKeyError) {
    _groqKeyToastShown = true
    useToast().show(
      'Invalid or missing GROQ_API_KEY. Set your real key in backend/.env and restart the server.',
      'error',
    )
  }
}

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
    const msg = body.detail || `Request failed with status ${res.status}`
    _warnIfGroqKeyError(msg)
    throw new ApiError(res.status, msg)
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
    const msg = body.detail || `Request failed with status ${res.status}`
    _warnIfGroqKeyError(msg)
    throw new ApiError(res.status, msg)
  }
  return res
}
