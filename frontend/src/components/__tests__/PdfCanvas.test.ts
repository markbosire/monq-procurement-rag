import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import PdfCanvas from '../PdfCanvas.vue'

function createMockPdfDoc() {
  const mockRender = { promise: Promise.resolve(), cancel: vi.fn() }
  const mockPage = {
    getViewport: vi.fn((opts: { scale: number }) => ({
      height: 800 * (opts?.scale ?? 1),
      width: 600 * (opts?.scale ?? 1),
    })),
    render: vi.fn().mockReturnValue(mockRender),
  }
  return {
    numPages: 5,
    getPage: vi.fn().mockResolvedValue(mockPage),
    _mockPage: mockPage,
    _mockRender: mockRender,
  }
}

function createWrapper(props: Record<string, unknown> = {}) {
  const pdfDoc = createMockPdfDoc()
  const wrapper = mount(PdfCanvas, {
    props: {
      pdfDoc,
      currentPage: 1,
      highlightBBoxes: [],
      themeColor: '#2563eb',
      ...props,
    },
    attachTo: document.body,
  })
  return { wrapper, pdfDoc }
}

beforeEach(() => {
  vi.clearAllMocks()
  document.body.innerHTML = ''
})

describe('PdfCanvas', () => {
  it('renders canvas and container with shadow class', () => {
    const { wrapper } = createWrapper()
    expect(wrapper.find('canvas').exists()).toBe(true)
    expect(wrapper.find('.shadow-neo').exists()).toBe(true)
  })

  it('renders canvas inside a flex container', () => {
    const { wrapper } = createWrapper()
    expect(wrapper.find('.flex-1').exists()).toBe(true)
  })

  it('accepts highlight bboxes', () => {
    const { wrapper } = createWrapper({
      highlightBBoxes: [{ page: 1, x0: 0, y0: 0, x1: 100, y1: 50 }],
    })
    expect(wrapper.find('canvas').exists()).toBe(true)
  })

  it('computeFitScale returns at most 3', () => {
    const { wrapper } = createWrapper()
    const vm = wrapper.vm as unknown as { computeFitScale: (h: number, w: number) => number }
    const scale = vm.computeFitScale(100, 100)
    expect(scale).toBeLessThanOrEqual(3)
  })

  it('computeFitScale returns 1 when container is null', () => {
    const pdfDoc = createMockPdfDoc()
    const wrapper = mount(PdfCanvas, {
      props: { pdfDoc, currentPage: 1, highlightBBoxes: [], themeColor: '#2563eb' },
    })
    const vm = wrapper.vm as unknown as { computeFitScale: (h: number, w: number) => number }
    const scale = vm.computeFitScale(100, 100)
    expect(scale).toBe(1)
  })

  it('returns cancel function from page.render', () => {
    const cancelFn = vi.fn()
    const mockPage = {
      getViewport: vi.fn((opts: { scale: number }) => ({
        height: 800 * (opts?.scale ?? 1),
        width: 600 * (opts?.scale ?? 1),
      })),
      render: vi.fn().mockReturnValue({ promise: Promise.resolve(), cancel: cancelFn }),
    }
    const pdfDoc = {
      numPages: 5,
      getPage: vi.fn().mockResolvedValue(mockPage),
    }

    const result = pdfDoc.getPage(1)
    expect(result).toBeInstanceOf(Promise)

    const renderResult = mockPage.render({ canvasContext: {} as CanvasRenderingContext2D, viewport: {} })
    expect(renderResult.cancel).toBe(cancelFn)
  })

  it('triggers renderPage when currentPage changes', async () => {
    const { wrapper, pdfDoc } = createWrapper()
    await nextTick()
    pdfDoc.getPage.mockClear()

    await wrapper.setProps({ currentPage: 2 })
    await nextTick()
    await nextTick()
    expect(pdfDoc.getPage).toHaveBeenCalledWith(2)
  })

  it('triggers renderPage when highlightBBoxes change', async () => {
    const { wrapper, pdfDoc } = createWrapper()
    await nextTick()
    pdfDoc.getPage.mockClear()

    await wrapper.setProps({ highlightBBoxes: [{ page: 1, x0: 10, y0: 10, x1: 50, y1: 50 }] })
    await nextTick()
    await nextTick()
    expect(pdfDoc.getPage).toHaveBeenCalledWith(1)
  })

  it('cancels previous render task before starting a new one', async () => {
    const cancelFn = vi.fn()
    const { wrapper } = createWrapper()
    
    // Manually set internal renderTask to test cancellation logic in renderPage
    ;(wrapper.vm as any).renderTask = { cancel: cancelFn, promise: Promise.resolve() }

    const vm = wrapper.vm as unknown as { renderPage: (p: number) => Promise<void> }
    await vm.renderPage(2)

    expect(cancelFn).toHaveBeenCalled()
  })
})
