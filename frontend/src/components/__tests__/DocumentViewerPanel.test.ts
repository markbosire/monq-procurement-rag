import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { nextTick } from 'vue'
import DocumentViewerPanel from '../DocumentViewerPanel.vue'
import { activeHighlight } from '../../composables/useSourceViewer'

const mockGetDocument = vi.hoisted(() => vi.fn())
const mockGetDocumentPdf = vi.hoisted(() => vi.fn())

vi.mock('../../api/documents', () => ({
  getDocument: mockGetDocument,
  getDocumentPdf: mockGetDocumentPdf,
}))

beforeEach(() => {
  setActivePinia(createPinia())
  activeHighlight.value = null
  vi.clearAllMocks()
})

afterEach(() => {
  activeHighlight.value = null
})

describe('DocumentViewerPanel', () => {
  it('shows loading state initially', () => {
    mockGetDocumentPdf.mockReturnValue(new Promise(() => {}))
    mockGetDocument.mockResolvedValue({
      document_id: '1',
      classification: { category: 'Contract', confidence: 0.9, reasoning: 'R' },
      chunk_count: 5,
      status: 'ready',
      title: 'Test Doc',
      summary: 'A summary.',
      extractions: null,
    })

    const wrapper = mount(DocumentViewerPanel, {
      props: { documentId: 'doc-1' },
    })
    expect(wrapper.text()).toContain('Loading PDF')
  })

  it('renders toolbar container', () => {
    mockGetDocumentPdf.mockReturnValue(new Promise(() => {}))
    mockGetDocument.mockResolvedValue({
      document_id: '1',
      classification: { category: 'Contract', confidence: 0.9, reasoning: 'R' },
      chunk_count: 5,
      status: 'ready',
      title: 'Test Doc',
      summary: 'A summary.',
      extractions: null,
    })

    const wrapper = mount(DocumentViewerPanel, {
      props: { documentId: 'doc-1' },
    })
    expect(wrapper.find('.flex-col').exists()).toBe(true)
  })

  it('shows error state when PDF loading fails', async () => {
    mockGetDocumentPdf.mockRejectedValue(new Error('Not found'))
    mockGetDocument.mockResolvedValue({
      document_id: '1',
      classification: { category: 'Contract', confidence: 0.9, reasoning: 'R' },
      chunk_count: 5,
      status: 'ready',
      title: 'Test Doc',
      summary: 'A summary.',
      extractions: null,
    })

    const wrapper = mount(DocumentViewerPanel, {
      props: { documentId: 'doc-1' },
    })
    await new Promise(r => setTimeout(r, 50))
    await nextTick()
    expect(wrapper.text()).toContain('Not found')
  })

  it('navigates page and passes bboxes to PdfCanvas when activeHighlight changes', async () => {
    const mockPage = {
      getViewport: vi.fn(() => ({ height: 800, width: 600 })),
      render: vi.fn().mockReturnValue({ promise: Promise.resolve(), cancel: vi.fn() }),
    }
    mockGetDocumentPdf.mockResolvedValue({
      numPages: 5,
      getPage: vi.fn().mockResolvedValue(mockPage),
    })
    mockGetDocument.mockResolvedValue({
      document_id: 'doc-1',
      classification: { category: 'Contract', confidence: 0.9, reasoning: 'R' },
      chunk_count: 5,
      status: 'ready',
      title: 'Test Doc',
      summary: 'A summary.',
      extractions: { field1: { value: 'val', chunk_id: 1, bbox: [{ page: 2, x0: 10, y0: 10, x1: 50, y1: 50 }] } },
    })

    const wrapper = mount(DocumentViewerPanel, {
      props: { documentId: 'doc-1' },
    })
    await new Promise(r => setTimeout(r, 50))
    await nextTick()

    // Trigger activeHighlight
    activeHighlight.value = { chunkId: 1, bbox: [{ page: 2, x0: 10, y0: 10, x1: 50, y1: 50 }] }
    await nextTick()
    await nextTick()

    const pdfCanvas = wrapper.findComponent({ name: 'PdfCanvas' })
    expect(pdfCanvas.exists()).toBe(true)
    expect(pdfCanvas.props('currentPage')).toBe(2)
    expect(pdfCanvas.props('highlightBBoxes')).toEqual([{ page: 2, x0: 10, y0: 10, x1: 50, y1: 50 }])
  })

  it('handles 404 fallback state when PDF is missing', async () => {
    mockGetDocumentPdf.mockRejectedValue(new Error('Document not found (404)'))
    mockGetDocument.mockRejectedValue(new Error('404 Not Found'))

    const wrapper = mount(DocumentViewerPanel, {
      props: { documentId: 'doc-404' },
    })
    await new Promise(r => setTimeout(r, 50))
    await nextTick()

    expect(wrapper.text()).toContain('Document not found (404)')
  })

  it('toggles viewingMetadata and preserves page state', async () => {
    const mockPage = {
      getViewport: vi.fn(() => ({ height: 800, width: 600 })),
      render: vi.fn().mockReturnValue({ promise: Promise.resolve(), cancel: vi.fn() }),
    }
    mockGetDocumentPdf.mockResolvedValue({
      numPages: 5,
      getPage: vi.fn().mockResolvedValue(mockPage),
    })
    mockGetDocument.mockResolvedValue({
      document_id: 'doc-1',
      classification: { category: 'Contract', confidence: 0.9, reasoning: 'R' },
      chunk_count: 5,
      status: 'ready',
      title: 'Test Doc',
      summary: 'A summary.',
      extractions: { field1: { value: 'val', chunk_id: 1, bbox: [{ page: 3, x0: 10, y0: 10, x1: 50, y1: 50 }] } },
    })

    const wrapper = mount(DocumentViewerPanel, {
      props: { documentId: 'doc-1' },
    })
    await new Promise(r => setTimeout(r, 50))
    await nextTick()

    // Initially metadata is visible
    expect(wrapper.findComponent({ name: 'MetadataPanel' }).exists()).toBe(true)

    // Jump to field -> switches to PDF view on page 3
    const metadataPanel = wrapper.findComponent({ name: 'MetadataPanel' })
    metadataPanel.vm.$emit('jump-to-field', { chunk_id: 1, bbox: [{ page: 3, x0: 10, y0: 10, x1: 50, y1: 50 }] })
    await nextTick()
    await nextTick()

    expect(wrapper.findComponent({ name: 'PdfCanvas' }).exists()).toBe(true)
    expect(wrapper.findComponent({ name: 'PdfCanvas' }).props('currentPage')).toBe(3)

    // Toggle metadata back on via toolbar event
    const toolbar = wrapper.findComponent({ name: 'PdfToolbar' })
    toolbar.vm.$emit('toggle-metadata')
    await nextTick()

    expect(wrapper.findComponent({ name: 'MetadataPanel' }).exists()).toBe(true)
  })
})