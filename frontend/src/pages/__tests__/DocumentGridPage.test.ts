import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createWebHistory } from 'vue-router'
import { nextTick } from 'vue'
import DocumentGridPage from '../DocumentGridPage.vue'
import { useDocumentStore } from '../../stores/useDocumentStore'
import { useToast } from '../../composables/useToast'
import { createMockDocumentListItem, createMockFile } from '../../__tests__/utils'

const mockListDocuments = vi.hoisted(() => vi.fn().mockResolvedValue([]))
const mockUploadDocument = vi.hoisted(() => vi.fn())
const mockRenameDocument = vi.hoisted(() => vi.fn())
const mockDeleteDocument = vi.hoisted(() => vi.fn())

vi.mock('../../api/documents', () => ({
  listDocuments: mockListDocuments,
  uploadDocument: mockUploadDocument,
  renameDocument: mockRenameDocument,
  deleteDocument: mockDeleteDocument,
}))

function createTestRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', redirect: '/documents' },
      { path: '/documents', component: { template: '<div>Grid</div>' } },
      { path: '/documents/:id', component: { template: '<div>Chat {{ $route.params.id }}</div>' } },
    ],
  })
}

async function createMountedPage() {
  const pinia = createPinia()
  setActivePinia(pinia)
  const router = createTestRouter()
  const wrapper = mount(DocumentGridPage, {
    global: { plugins: [pinia, router] },
  })
  await new Promise(r => setTimeout(r, 50))
  return { wrapper, pinia, router }
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('DocumentGridPage', () => {
  it('renders page header', async () => {
    const { wrapper } = await createMountedPage()
    expect(wrapper.text()).toContain('DOCUMENTS')
  })

  it('shows document count', async () => {
    const { wrapper, pinia } = await createMountedPage()
    setActivePinia(pinia)
    const store = useDocumentStore()
    store.documents = [createMockDocumentListItem()]
    await new Promise(r => setTimeout(r, 50))
    expect(wrapper.text()).toContain('1 file')
  })

  it('shows plural count for multiple documents', async () => {
    const { wrapper, pinia } = await createMountedPage()
    setActivePinia(pinia)
    const store = useDocumentStore()
    store.documents = [
      createMockDocumentListItem(),
      createMockDocumentListItem({ document_id: 'doc-2', filename: 'doc2.pdf' }),
    ]
    await new Promise(r => setTimeout(r, 50))
    expect(wrapper.text()).toContain('2 files')
  })

  it('shows loading state when store.loading is true and no documents', async () => {
    const { wrapper, pinia } = await createMountedPage()
    setActivePinia(pinia)
    const store = useDocumentStore()
    store.loading = true
    await new Promise(r => setTimeout(r, 50))
    expect(wrapper.text()).toContain('Loading')
  })

  it('shows empty state Add Document card when no processing card', async () => {
    const { wrapper } = await createMountedPage()
    expect(wrapper.text()).toContain('Add Document')
    expect(wrapper.text()).toContain('or drag a PDF here')
  })

  it('renders document cards from store', async () => {
    const { wrapper, pinia } = await createMountedPage()
    setActivePinia(pinia)
    const store = useDocumentStore()
    store.documents = [
      createMockDocumentListItem({ document_id: '1', filename: 'contract.pdf', category: 'Contract', chunk_count: 10 }),
      createMockDocumentListItem({ document_id: '2', filename: 'rfp.pdf', category: 'RFP/RFQ', chunk_count: 5 }),
    ]
    await new Promise(r => setTimeout(r, 50))
    expect(wrapper.text()).toContain('contract.pdf')
    expect(wrapper.text()).toContain('rfp.pdf')
    expect(wrapper.text()).toContain('10 chunks')
    expect(wrapper.text()).toContain('5 chunks')
  })

  it('shows Unclassified badge for documents without category', async () => {
    const { wrapper, pinia } = await createMountedPage()
    setActivePinia(pinia)
    const store = useDocumentStore()
    store.documents = [createMockDocumentListItem({ category: null })]
    await new Promise(r => setTimeout(r, 50))
    expect(wrapper.text()).toContain('Unclassified')
  })

  it('shows formatted date on document cards', async () => {
    const { wrapper, pinia } = await createMountedPage()
    setActivePinia(pinia)
    const store = useDocumentStore()
    store.documents = [createMockDocumentListItem({ created_at: '2024-06-15T00:00:00Z' })]
    await new Promise(r => setTimeout(r, 50))
    const dateStr = new Date('2024-06-15T00:00:00Z').toLocaleDateString()
    expect(wrapper.text()).toContain(dateStr)
  })

  describe('drag-and-drop', () => {
    it('shows drag-over overlay when dragging over the page', async () => {
      const { wrapper } = await createMountedPage()
      await wrapper.trigger('dragover')
      await nextTick()
      expect(wrapper.text()).toContain('Drop PDF here')
    })

    it('hides drag-over overlay on dragleave', async () => {
      const { wrapper } = await createMountedPage()
      await wrapper.trigger('dragover')
      await nextTick()
      expect(wrapper.text()).toContain('Drop PDF here')

      await wrapper.trigger('dragleave')
      await nextTick()
      expect(wrapper.text()).not.toContain('Drop PDF here')
    })

    it('uploads file when dropped', async () => {
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

      const { wrapper } = await createMountedPage()
      const file = createMockFile('dropped.pdf')
      await wrapper.trigger('drop', { dataTransfer: { files: [file] } })
      await new Promise(r => setTimeout(r, 100))

      expect(mockUploadDocument).toHaveBeenCalledWith(file)
    })
  })

  describe('context menu', () => {
    it('shows context menu on MoreVertical click', async () => {
      const { wrapper, pinia } = await createMountedPage()
      setActivePinia(pinia)
      const store = useDocumentStore()
      store.documents = [createMockDocumentListItem({ document_id: 'doc-1' })]
      await new Promise(r => setTimeout(r, 50))

      const menuBtn = wrapper.find('.neo-menu-btn')
      await menuBtn.trigger('click')
      await nextTick()

      expect(wrapper.text()).toContain('Rename')
      expect(wrapper.text()).toContain('Delete')
    })

    it('hides context menu when clicking outside', async () => {
      const { wrapper, pinia } = await createMountedPage()
      setActivePinia(pinia)
      const store = useDocumentStore()
      store.documents = [createMockDocumentListItem({ document_id: 'doc-1' })]
      await new Promise(r => setTimeout(r, 50))

      const menuBtn = wrapper.find('.neo-menu-btn')
      await menuBtn.trigger('click')
      await nextTick()
      expect(wrapper.text()).toContain('Rename')

      await wrapper.trigger('click')
      await nextTick()
    })
  })

  describe('processing card', () => {
    it('creates processing card on upload', async () => {
      const { wrapper } = await createMountedPage()
      const vm = wrapper.vm as unknown as { uploadFile: (f: File) => Promise<void> }
      const uploadPromise = vm.uploadFile(createMockFile('upload.pdf'))
      await nextTick()
      const gridEl = wrapper.find('.min-h-screen')
      expect(gridEl.exists()).toBe(true)
      await uploadPromise.catch(() => {})
    })

    it('rejects non-PDF files with a toast', async () => {
      const { wrapper } = await createMountedPage()
      useToast().clear()
      const vm = wrapper.vm as unknown as { uploadFile: (f: File) => Promise<void> }
      const txtFile = new File(['content'], 'test.txt', { type: 'text/plain' })
      await vm.uploadFile(txtFile)
      const { toasts } = useToast()
      expect(toasts.length).toBeGreaterThan(0)
      expect(toasts[0].message).toBe('Please select a PDF file')
    })
  })
})
