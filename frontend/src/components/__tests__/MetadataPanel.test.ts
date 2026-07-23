import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MetadataPanel from '../MetadataPanel.vue'

function createWrapper(props: Record<string, unknown> = {}) {
  return mount(MetadataPanel, {
    props: {
      extractions: null,
      docTitle: null,
      docSummary: null,
      themeColor: '#2563eb',
      ...props,
    },
  })
}

describe('MetadataPanel', () => {
  it('shows document title', () => {
    const wrapper = createWrapper({ docTitle: 'Test RFP' })
    expect(wrapper.text()).toContain('Test RFP')
  })

  it('shows document summary', () => {
    const wrapper = createWrapper({ docSummary: 'A test summary.' })
    expect(wrapper.text()).toContain('A test summary.')
  })

  it('hides summary when not provided', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).not.toContain('undefined')
  })

  it('shows View PDF button', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('View PDF')
  })

  it('emits view-pdf on button click', async () => {
    const wrapper = createWrapper()
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('view-pdf')).toBeTruthy()
  })

  it('renders extractions in grouped sections', () => {
    const wrapper = createWrapper({
      extractions: {
        parties: { value: 'ACME Corp', chunk_id: 1, bbox: [] },
        effective_date: { value: '2025-01-01', chunk_id: 2, bbox: [{ page: 1, x0: 0, y0: 0, x1: 10, y1: 10 }] },
      },
    })
    expect(wrapper.text()).toContain('ACME Corp')
    expect(wrapper.text()).toContain('2025-01-01')
  })

  it('emits jump-to-field when a clickable field is clicked', async () => {
    const wrapper = createWrapper({
      extractions: {
        parties: { value: 'ACME Corp', chunk_id: 1, bbox: [{ page: 1, x0: 0, y0: 0, x1: 10, y1: 10 }] },
      },
    })
    const fieldEl = wrapper.find('.cursor-pointer')
    await fieldEl.trigger('click')
    expect(wrapper.emitted('jump-to-field')?.[0]).toBeTruthy()
  })

  it('shows section header labels', () => {
    const wrapper = createWrapper({
      extractions: {
        parties: { value: 'ACME Corp', chunk_id: 1, bbox: [] },
        effective_date: { value: '2025-01-01', chunk_id: 2, bbox: [] },
      },
    })
    expect(wrapper.text()).toContain('Agreement')
  })

  it('handles null extractions gracefully', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).not.toContain('null')
  })
})
