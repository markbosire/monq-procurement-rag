import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { nextTick } from 'vue'
import { activeHighlight, useSourceViewer } from '../composables/useSourceViewer'

beforeEach(() => {
  activeHighlight.value = null
  vi.clearAllMocks()
})

afterEach(() => {
  activeHighlight.value = null
})

describe('Source Highlight → PDF Viewer Sync', () => {
  it('sets activeHighlight via showHighlight and clears via clearHighlight', () => {
    const { showHighlight, clearHighlight } = useSourceViewer()
    expect(activeHighlight.value).toBeNull()

    showHighlight({ chunkId: 42, bbox: [{ page: 3, x0: 100, y0: 200, x1: 400, y1: 220 }] })
    expect(activeHighlight.value).toEqual({ chunkId: 42, bbox: [{ page: 3, x0: 100, y0: 200, x1: 400, y1: 220 }] })

    clearHighlight()
    expect(activeHighlight.value).toBeNull()
  })

  it('sets activeHighlight with multiple bboxes across pages', () => {
    const { showHighlight } = useSourceViewer()
    const bboxes = [
      { page: 1, x0: 0, y0: 0, x1: 100, y1: 50 },
      { page: 3, x0: 200, y0: 300, x1: 500, y1: 350 },
    ]
    showHighlight({ chunkId: 7, bbox: bboxes })
    expect(activeHighlight.value).toEqual({ chunkId: 7, bbox: bboxes })
  })

  it('shared activeHighlight ref is updated by any component calling showHighlight', () => {
    const { showHighlight: show1 } = useSourceViewer()
    const { showHighlight: show2 } = useSourceViewer()
    const { activeHighlight: hl1 } = useSourceViewer()
    const { activeHighlight: hl2 } = useSourceViewer()

    expect(hl1.value).toBeNull()
    expect(hl2.value).toBeNull()

    show1({ chunkId: 1, bbox: [{ page: 1, x0: 0, y0: 0, x1: 10, y1: 10 }] })
    expect(hl1.value).not.toBeNull()
    expect(hl2.value).not.toBeNull()
    expect(hl1.value?.chunkId).toBe(1)
    expect(hl2.value?.chunkId).toBe(1)

    show2({ chunkId: 2, bbox: [{ page: 2, x0: 0, y0: 0, x1: 20, y1: 20 }] })
    expect(hl1.value?.chunkId).toBe(2)
    expect(hl2.value?.chunkId).toBe(2)
  })
})
