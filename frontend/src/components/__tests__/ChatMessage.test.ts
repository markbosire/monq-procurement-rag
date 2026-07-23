import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ChatMessage from '../ChatMessage.vue'

const DEFAULT_THEME = { icon: 'File', color: '#6b7280', bg: '#f9fafb', bgLight: '#f3f4f6', border: '#e5e7eb', accent: '#4b5563' }

function createWrapper(props: Record<string, unknown> = {}) {
  return mount(ChatMessage, {
    props: {
      role: 'assistant',
      content: 'Test answer',
      documentId: 'doc-123',
      theme: DEFAULT_THEME,
      ...props,
    },
  })
}

describe('ChatMessage', () => {
  it('renders YOU badge for user messages', () => {
    const wrapper = createWrapper({ role: 'user', content: 'User question' })
    expect(wrapper.text()).toContain('YOU')
  })

  it('renders AI badge for assistant messages', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('AI')
  })

  it('displays message content', () => {
    const wrapper = createWrapper({ content: 'Hello world' })
    expect(wrapper.text()).toContain('Hello world')
  })

  it('shows copy button with aria-label', () => {
    const wrapper = createWrapper()
    const copyBtn = wrapper.find('button[aria-label="Copy response text"]')
    expect(copyBtn.exists()).toBe(true)
  })

  it('shows sources toggle when sourceChunks provided', () => {
    const wrapper = createWrapper({
      sourceChunks: [{ id: 1, text: 'source text', page_numbers: [1] }],
    })
    expect(wrapper.text()).toContain('SOURCES')
  })

  it('hides sources toggle when sourceChunks is empty', () => {
    const wrapper = createWrapper({ sourceChunks: [] })
    expect(wrapper.text()).not.toContain('SOURCES')
  })

  it('shows chunk text when sources are expanded', async () => {
    const wrapper = createWrapper({
      sourceChunks: [{ id: 1, text: 'chunk content', page_numbers: [1] }],
    })
    const toggle = wrapper.find('.neo-src-toggle')
    await toggle.trigger('click')
    expect(wrapper.text()).toContain('chunk content')
  })

  it('shows CHUNK label for each source', async () => {
    const wrapper = createWrapper({
      sourceChunks: [
        { id: 1, text: 'first', page_numbers: [1] },
        { id: 2, text: 'second', page_numbers: [2] },
      ],
    })
    const toggle = wrapper.find('.neo-src-toggle')
    await toggle.trigger('click')
    expect(wrapper.text()).toContain('CHUNK 1')
    expect(wrapper.text()).toContain('CHUNK 2')
  })

  it('emits source-click when chunk with bbox is clicked', async () => {
    const bbox = [{ page: 1, x0: 0, y0: 0, x1: 100, y1: 50 }]
    const wrapper = createWrapper({
      sourceChunks: [{ id: 42, text: 'source', page_numbers: [1], bbox }],
    })
    const toggle = wrapper.find('.neo-src-toggle')
    await toggle.trigger('click')
    const chip = wrapper.find('.neo-chip')
    await chip.trigger('click')
    expect(wrapper.emitted('source-click')?.[0]).toEqual([{ chunkId: 42, bbox }])
  })
})
