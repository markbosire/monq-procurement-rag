import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import PdfToolbar from '../PdfToolbar.vue'

function createWrapper(props: Record<string, unknown> = {}) {
  return mount(PdfToolbar, {
    props: {
      currentPage: 1,
      totalPages: 5,
      viewingMetadata: false,
      hasMetadata: true,
      docTitle: 'Test Doc',
      ...props,
    },
  })
}

describe('PdfToolbar', () => {
  it('shows Document Info button when hasMetadata is true', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('Document Info')
  })

  it('shows Document Info button when docTitle is set', () => {
    const wrapper = createWrapper({ hasMetadata: false })
    expect(wrapper.text()).toContain('Document Info')
  })

  it('hides Document Info when no metadata and no title', () => {
    const wrapper = createWrapper({ hasMetadata: false, docTitle: null })
    expect(wrapper.text()).not.toContain('Document Info')
  })

  it('shows page indicator when not viewing metadata', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('Page 1 of 5')
  })

  it('hides page indicator when viewing metadata', () => {
    const wrapper = createWrapper({ viewingMetadata: true })
    expect(wrapper.text()).not.toContain('Page 1 of 5')
  })

  it('emits toggle-metadata when Document Info is clicked', async () => {
    const wrapper = createWrapper()
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('toggle-metadata')).toBeTruthy()
  })

  it('disables prev button on first page', () => {
    const wrapper = createWrapper({ currentPage: 1 })
    const prev = wrapper.findAll('button').filter(b => b.attributes('aria-label') === 'Previous page')
    expect(prev[0].attributes('disabled')).toBeDefined()
  })

  it('disables next button on last page', () => {
    const wrapper = createWrapper({ currentPage: 5, totalPages: 5 })
    const next = wrapper.findAll('button').filter(b => b.attributes('aria-label') === 'Next page')
    expect(next[0].attributes('disabled')).toBeDefined()
  })

  it('emits go-to-page with currentPage - 1 on prev click', async () => {
    const wrapper = createWrapper({ currentPage: 3 })
    const prev = wrapper.findAll('button').filter(b => b.attributes('aria-label') === 'Previous page')
    await prev[0].trigger('click')
    expect(wrapper.emitted('go-to-page')?.[0]).toEqual([2])
  })

  it('emits go-to-page with currentPage + 1 on next click', async () => {
    const wrapper = createWrapper({ currentPage: 3 })
    const next = wrapper.findAll('button').filter(b => b.attributes('aria-label') === 'Next page')
    await next[0].trigger('click')
    expect(wrapper.emitted('go-to-page')?.[0]).toEqual([4])
  })
})
