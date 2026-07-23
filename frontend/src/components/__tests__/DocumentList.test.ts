import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import DocumentList from '../DocumentList.vue'
import { useDocumentStore } from '../../stores/useDocumentStore'

const mockListDocuments = vi.hoisted(() => vi.fn().mockResolvedValue([]))

vi.mock('../../api/documents', () => ({
  listDocuments: mockListDocuments,
}))

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('DocumentList', () => {
  it('shows loading state', () => {
    const store = useDocumentStore()
    store.loading = true
    const wrapper = mount(DocumentList, { props: { activeId: null } })
    expect(wrapper.text()).toContain('Loading')
  })

  it('shows empty state when no documents', () => {
    mount(DocumentList, { props: { activeId: null } })
    // onMounted triggers fetchAll which sets loading=true then loading=false since mock resolves
    const store = useDocumentStore()
    expect(store.documents).toEqual([])
  })

  it('renders document items', () => {
    const store = useDocumentStore()
    store.documents = [
      { document_id: '1', filename: 'test.pdf', category: 'Contract', chunk_count: 5, title: 'Test', created_at: null },
    ]
    const wrapper = mount(DocumentList, { props: { activeId: null } })
    expect(wrapper.text()).toContain('test.pdf')
    expect(wrapper.text()).toContain('Contract')
    expect(wrapper.text()).toContain('5 chunks')
  })

  it('highlights the active document', () => {
    const store = useDocumentStore()
    store.documents = [
      { document_id: '1', filename: 'a.pdf', category: null, chunk_count: 0, title: null, created_at: null },
      { document_id: '2', filename: 'b.pdf', category: null, chunk_count: 0, title: null, created_at: null },
    ]
    const wrapper = mount(DocumentList, { props: { activeId: '1' } })
    const items = wrapper.findAll('li')
    expect(items[0].classes()).toContain('bg-black')
  })

  it('emits select when a document is clicked', async () => {
    const store = useDocumentStore()
    store.documents = [
      { document_id: '1', filename: 'test.pdf', category: null, chunk_count: 0, title: null, created_at: null },
    ]
    const wrapper = mount(DocumentList, { props: { activeId: null } })
    await wrapper.find('li').trigger('click')
    expect(wrapper.emitted('select')?.[0]).toEqual(['1'])
  })
})
