import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useToast } from '../useToast'

beforeEach(() => {
  vi.useFakeTimers()
  useToast().clear()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('useToast', () => {
  it('returns empty toasts initially', () => {
    expect(useToast().toasts).toEqual([])
  })

  it('adds a toast with show()', () => {
    const { toasts, show } = useToast()
    show('Test message', 'success')
    expect(toasts).toHaveLength(1)
    expect(toasts[0].message).toBe('Test message')
    expect(toasts[0].type).toBe('success')
    expect(toasts[0]).toHaveProperty('id')
  })

  it('defaults type to error', () => {
    const { toasts, show } = useToast()
    show('Something broke')
    expect(toasts[0].type).toBe('error')
  })

  it('auto-dismisses after 5 seconds', () => {
    const { show } = useToast()
    show('Auto dismiss')
    expect(useToast().toasts).toHaveLength(1)
    vi.advanceTimersByTime(5000)
    expect(useToast().toasts).toHaveLength(0)
  })

  it('dismisses a specific toast by id', () => {
    const { show, dismiss } = useToast()
    show('First')
    show('Second')
    const id = useToast().toasts[0].id
    dismiss(id)
    expect(useToast().toasts).toHaveLength(1)
    expect(useToast().toasts[0].message).toBe('Second')
  })

  it('clears all toasts', () => {
    const { show } = useToast()
    show('A')
    show('B')
    expect(useToast().toasts).toHaveLength(2)
    useToast().clear()
    expect(useToast().toasts).toHaveLength(0)
  })
})
