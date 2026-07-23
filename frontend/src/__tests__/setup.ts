import { vi } from 'vitest'

vi.mock('pdfjs-dist', () => {
  const mockRender = vi.fn().mockReturnValue({ promise: Promise.resolve(), cancel: vi.fn() })
  const mockGetPage = vi.fn().mockResolvedValue({
    getViewport: vi.fn((opts: { scale: number }) => ({ height: 800 * (opts?.scale ?? 1), width: 600 * (opts?.scale ?? 1) })),
    render: mockRender,
  })
  const getDocument = vi.fn().mockReturnValue({
    promise: Promise.resolve({
      numPages: 5,
      getPage: mockGetPage,
    }),
  })
  return {
    default: { GlobalWorkerOptions: { workerSrc: '' }, getDocument },
    GlobalWorkerOptions: { workerSrc: '' },
    getDocument,
  }
})

vi.mock('pdfjs-dist/build/pdf.worker.mjs', () => ({}))
