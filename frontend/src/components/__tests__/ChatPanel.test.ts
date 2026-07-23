import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { nextTick } from 'vue'
import ChatPanel from '../ChatPanel.vue'
import { useChatStore } from '../../stores/useChatStore'

const mockGetChatHistory = vi.hoisted(() => vi.fn().mockResolvedValue({ messages: [] }))
const mockPostChatMessage = vi.hoisted(() => vi.fn())

vi.mock('../../api/documents', () => ({
  getDocument: vi.fn(),
}))

vi.mock('../../api/chat', () => ({
  getChatHistory: mockGetChatHistory,
  postChatMessage: mockPostChatMessage,
}))

const DEFAULT_THEME = { icon: 'File', color: '#6b7280', bg: '#f9fafb', bgLight: '#f3f4f6', border: '#e5e7eb', accent: '#4b5563' }

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('ChatPanel', () => {
  it('shows empty state message', () => {
    const wrapper = mount(ChatPanel, {
      props: { documentId: 'doc-1', theme: DEFAULT_THEME },
    })
    expect(wrapper.text()).toContain('Ask a question about this document')
  })

  it('renders input with placeholder', () => {
    const wrapper = mount(ChatPanel, {
      props: { documentId: 'doc-1', theme: DEFAULT_THEME },
    })
    const input = wrapper.find('input')
    expect(input.exists()).toBe(true)
    expect(input.attributes('placeholder')).toBe('Type your question...')
  })

  it('renders Send button', () => {
    const wrapper = mount(ChatPanel, {
      props: { documentId: 'doc-1', theme: DEFAULT_THEME },
    })
    expect(wrapper.text()).toContain('Send')
  })

  it('disables Send button when loading', () => {
    const store = useChatStore()
    store.loading = true
    const wrapper = mount(ChatPanel, {
      props: { documentId: 'doc-1', theme: DEFAULT_THEME },
    })
    const sendBtn = wrapper.find('button')
    expect(sendBtn.attributes('disabled')).toBeDefined()
  })

  it('disables Send button when input is empty', () => {
    useChatStore().loading = false
    const wrapper = mount(ChatPanel, {
      props: { documentId: 'doc-1', theme: DEFAULT_THEME },
    })
    expect(wrapper.find('button').attributes('disabled')).toBeDefined()
  })

  it('enables Send button when input is not empty and not loading', async () => {
    useChatStore().loading = false
    const wrapper = mount(ChatPanel, {
      props: { documentId: 'doc-1', theme: DEFAULT_THEME },
    })
    const input = wrapper.find('input')
    await input.setValue('a question')
    await nextTick()
    expect(wrapper.find('button').attributes('disabled')).toBeUndefined()
  })

  it('shows THINKING indicator when loading', () => {
    useChatStore().loading = true
    const wrapper = mount(ChatPanel, {
      props: { documentId: 'doc-1', theme: DEFAULT_THEME },
    })
    expect(wrapper.text()).toContain('THINKING')
  })

  it('shows error message when store has error', () => {
    useChatStore().error = 'Something went wrong'
    const wrapper = mount(ChatPanel, {
      props: { documentId: 'doc-1', theme: DEFAULT_THEME },
    })
    expect(wrapper.text()).toContain('Something went wrong')
  })

  it('clears input after sending a message', async () => {
    mockPostChatMessage.mockResolvedValue({ answer: 'test', source_chunks: [] })
    const store = useChatStore()
    store.loading = false
    const wrapper = mount(ChatPanel, {
      props: { documentId: 'doc-1', theme: DEFAULT_THEME },
    })

    const input = wrapper.find('input')
    await input.setValue('my question')
    await nextTick()
    expect((input.element as HTMLInputElement).value).toBe('my question')

    const sendBtn = wrapper.find('button')
    await sendBtn.trigger('click')
    await new Promise(r => setTimeout(r, 50))
    await nextTick()

    expect((input.element as HTMLInputElement).value).toBe('')
  })

  it('sends message on Enter key', async () => {
    mockPostChatMessage.mockResolvedValue({ answer: 'response', source_chunks: [] })
    useChatStore().loading = false
    const wrapper = mount(ChatPanel, {
      props: { documentId: 'doc-1', theme: DEFAULT_THEME },
    })

    const input = wrapper.find('input')
    await input.setValue('question')
    await input.trigger('keyup.enter')
    await new Promise(r => setTimeout(r, 50))

    expect(mockPostChatMessage).toHaveBeenCalled()
  })
})
