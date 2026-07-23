import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import DeleteConfirmModal from '../DeleteConfirmModal.vue'

function createWrapper(props: Record<string, unknown> = {}) {
  return mount(DeleteConfirmModal, {
    props: { modelValue: true, ...props },
  })
}

describe('DeleteConfirmModal', () => {
  it('shows when modelValue is true', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('Delete document?')
  })

  it('hidden when modelValue is false', () => {
    const wrapper = createWrapper({ modelValue: false })
    expect(wrapper.find('div.fixed').exists()).toBe(false)
  })

  it('emits update:modelValue(false) on Cancel click', async () => {
    const wrapper = createWrapper()
    const cancelBtn = wrapper.findAll('button').filter(b => b.text() === 'Cancel')
    await cancelBtn[0].trigger('click')
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([false])
  })

  it('emits confirm on Delete click', async () => {
    const wrapper = createWrapper()
    const deleteBtn = wrapper.findAll('button').filter(b => b.text() === 'Delete')
    await deleteBtn[0].trigger('click')
    expect(wrapper.emitted('confirm')).toBeTruthy()
  })

  it('emits update:modelValue(false) on backdrop click', async () => {
    const wrapper = createWrapper()
    await wrapper.find('div.fixed').trigger('click')
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([false])
  })

  it('shows warning text', () => {
    const wrapper = createWrapper()
    expect(wrapper.text()).toContain('permanently delete')
  })
})
