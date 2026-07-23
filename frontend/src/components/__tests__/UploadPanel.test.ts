import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { nextTick } from 'vue'
import UploadPanel from '../UploadPanel.vue'
import { useDocumentStore } from '../../stores/useDocumentStore'
import { useToast } from '../../composables/useToast'

const mockUploadDocument = vi.hoisted(() => vi.fn())
const mockListDocuments = vi.hoisted(() => vi.fn())

vi.mock('../../api/documents', () => ({
  uploadDocument: mockUploadDocument,
  listDocuments: mockListDocuments,
}))

beforeEach(() => {
  setActivePinia(createPinia())
  useToast().clear()
  vi.clearAllMocks()
})

describe('UploadPanel', () => {
  it('renders upload button', () => {
    const wrapper = mount(UploadPanel)
    expect(wrapper.text()).toContain('Upload PDF')
  })

  it('shows drop zone text', () => {
    const wrapper = mount(UploadPanel)
    expect(wrapper.text()).toContain('or drop a PDF here')
  })

  it('shows Uploading... when store.uploading is true', () => {
    const store = useDocumentStore()
    store.uploading = true
    const wrapper = mount(UploadPanel)
    expect(wrapper.text()).toContain('Uploading...')
  })

  it('disables button during upload', () => {
    const store = useDocumentStore()
    store.uploading = true
    const wrapper = mount(UploadPanel)
    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
  })

  it('emits document-ready on successful upload', async () => {
    mockUploadDocument.mockResolvedValue({
      document_id: 'new-doc-1',
      classification: { category: 'RFP', confidence: 0.9, reasoning: 'R' },
      chunk_count: 0,
      status: 'processing',
      title: null,
      summary: null,
      extractions: null,
    })
    mockListDocuments.mockResolvedValue([])

    const wrapper = mount(UploadPanel)
    const file = new File(['content'], 'test.pdf', { type: 'application/pdf' })
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [file] })
    await input.trigger('change')

    // Wait for async store operations (upload + fetchAll) to complete
    await new Promise(r => setTimeout(r, 50))

    expect(wrapper.emitted('document-ready')?.[0]).toEqual(['new-doc-1'])
    expect(wrapper.emitted('uploaded')).toBeTruthy()
  })

  it('shows toast for non-PDF file', async () => {
    const wrapper = mount(UploadPanel)
    const file = new File(['content'], 'test.txt', { type: 'text/plain' })
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [file] })
    await input.trigger('change')

    const { toasts } = useToast()
    expect(toasts.length).toBeGreaterThan(0)
    expect(toasts[0].message).toBe('Please select a PDF file')
  })

  it('handles drag-drop', async () => {
    mockUploadDocument.mockResolvedValue({
      document_id: 'drop-doc',
      classification: { category: 'RFP', confidence: 0.9, reasoning: 'R' },
      chunk_count: 0,
      status: 'processing',
      title: null,
      summary: null,
      extractions: null,
    })
    mockListDocuments.mockResolvedValue([])

    const wrapper = mount(UploadPanel)
    const file = new File(['content'], 'dropped.pdf', { type: 'application/pdf' })
    await wrapper.find('.border-dashed').trigger('drop', {
      dataTransfer: { files: [file] },
    })

    await new Promise(r => setTimeout(r, 50))

    expect(wrapper.emitted('document-ready')?.[0]).toEqual(['drop-doc'])
  })
})
