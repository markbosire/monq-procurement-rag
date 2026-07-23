import { describe, it, expect, beforeEach } from 'vitest'
import { useSourceViewer, activeHighlight } from '../useSourceViewer'

beforeEach(() => {
  activeHighlight.value = null
})

describe('useSourceViewer', () => {
  it('starts with null activeHighlight', () => {
    const { activeHighlight: ah } = useSourceViewer()
    expect(ah.value).toBeNull()
  })

  it('showHighlight sets the active highlight', () => {
    const { showHighlight, activeHighlight: ah } = useSourceViewer()
    const highlight = { chunkId: 42, bbox: [{ page: 1, x0: 0, y0: 0, x1: 100, y1: 50 }] }
    showHighlight(highlight)
    expect(ah.value).toEqual(highlight)
  })

  it('clearHighlight resets to null', () => {
    const { showHighlight, clearHighlight, activeHighlight: ah } = useSourceViewer()
    showHighlight({ chunkId: 1, bbox: [] })
    clearHighlight()
    expect(ah.value).toBeNull()
  })
})
