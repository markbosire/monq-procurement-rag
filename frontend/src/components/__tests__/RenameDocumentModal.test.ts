import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import RenameDocumentModal from '../RenameDocumentModal.vue'

function createWrapper(props: Record<string, unknown> = {}) {
  return mount(RenameDocumentModal, {
    props: { modelValue: true, initialName: 'old.pdf', ...props },
  })
}

describe('RenameDocumentModal', () => {
  it('shows when modelValue is true', () => {
    const wrapper = createWrapper()
    expect(wrapper.find('input').exists()).toBe(true)
  })

  it('hidden when modelValue is false', () => {
    const wrapper = createWrapper({ modelValue: false })
    expect(wrapper.find('input').exists()).toBe(false)
  })

  it('input is pre-filled with initialName', () => {
    const wrapper = createWrapper()
    expect(wrapper.find('input').element.value).toBe('old.pdf')
  })

  it('emits confirm with trimmed name on Save click', async () => {
    const wrapper = createWrapper()
    const input = wrapper.find('input')
    await input.setValue('new-name.pdf')
    const saveBtn = wrapper.findAll('button').filter(b => b.text() === 'Save')
    await saveBtn[0].trigger('click')
    expect(wrapper.emitted('confirm')?.[0]).toEqual(['new-name.pdf'])
  })

  it('emits confirm with trimmed name on Enter key', async () => {
    const wrapper = createWrapper()
    const input = wrapper.find('input')
    await input.setValue('   trimmed-name.pdf   ')
    await input.trigger('keyup.enter')
    expect(wrapper.emitted('confirm')?.[0]).toEqual(['trimmed-name.pdf'])
  })

  it('emits update:modelValue(false) on Cancel click', async () => {
    const wrapper = createWrapper()
    const cancelBtn = wrapper.findAll('button').filter(b => b.text() === 'Cancel')
    await cancelBtn[0].trigger('click')
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([false])
  })

  it('emits update:modelValue(false) on Escape key', async () => {
    const wrapper = createWrapper()
    const input = wrapper.find('input')
    await input.trigger('keyup.escape')
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([false])
  })

  it('does not emit confirm when input is empty', async () => {
    const wrapper = createWrapper()
    const input = wrapper.find('input')
    await input.setValue('')
    const saveBtn = wrapper.findAll('button').filter(b => b.text() === 'Save')
    await saveBtn[0].trigger('click')
    expect(wrapper.emitted('confirm')).toBeFalsy()
  })
})
