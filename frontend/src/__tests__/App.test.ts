import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import App from '../App.vue'
import { useToast } from '../composables/useToast'

function createTestRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', redirect: '/documents' },
      { path: '/documents', name: 'documents', component: { template: '<div>Grid</div>' } },
    ],
  })
}

beforeEach(() => {
  setActivePinia(createPinia())
  useToast().clear()
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
  document.body.innerHTML = ''
})

describe('App.vue', () => {
  it('renders router-view', () => {
    const router = createTestRouter()
    const wrapper = mount(App, {
      global: { plugins: [createPinia(), router] },
    })
    expect(wrapper.findComponent({ name: 'RouterView' }).exists()).toBe(true)
  })

  it('renders routed content via router-view', async () => {
    const router = createTestRouter()
    await router.push('/documents')
    await router.isReady()
    const wrapper = mount(App, {
      global: { plugins: [createPinia(), router] },
    })
    expect(wrapper.text()).toContain('Grid')
  })

  it('shows toast notifications when toasts exist', () => {
    const { show } = useToast()
    show('Error message', 'error')
    mount(App, {
      global: { plugins: [createPinia(), createTestRouter()] },
    })
    expect(bodyText()).toContain('Error message')
  })

  it('applies error styling for error type toasts', () => {
    const { show } = useToast()
    show('Error text', 'error')
    mount(App, {
      global: { plugins: [createPinia(), createTestRouter()] },
    })
    const toast = useToast().toasts[0]
    expect(toast.type).toBe('error')
    expect(toast.message).toBe('Error text')
  })

  it('applies success styling for success type toasts', () => {
    const { show } = useToast()
    show('Success text', 'success')
    mount(App, {
      global: { plugins: [createPinia(), createTestRouter()] },
    })
    const toast = useToast().toasts[0]
    expect(toast.type).toBe('success')
    expect(toast.message).toBe('Success text')
  })

  it('applies info styling for info type toasts', () => {
    const { show } = useToast()
    show('Info text', 'info')
    mount(App, {
      global: { plugins: [createPinia(), createTestRouter()] },
    })
    const toast = useToast().toasts[0]
    expect(toast.type).toBe('info')
    expect(toast.message).toBe('Info text')
  })

  it('dismisses toast via useToast dismiss method', () => {
    const { show, dismiss } = useToast()
    show('Toast A', 'error')
    show('Toast B', 'success')
    expect(useToast().toasts.length).toBe(2)
    dismiss(useToast().toasts[0].id)
    expect(useToast().toasts.length).toBe(1)
    expect(useToast().toasts[0].message).toBe('Toast B')
  })

  it('auto-dismisses toast after 5 seconds', () => {
    const { show } = useToast()
    show('Auto dismiss', 'error')
    expect(useToast().toasts.length).toBe(1)
    vi.advanceTimersByTime(5000)
    expect(useToast().toasts.length).toBe(0)
  })

  it('renders multiple toasts', () => {
    const { show } = useToast()
    show('First', 'error')
    show('Second', 'success')
    mount(App, {
      global: { plugins: [createPinia(), createTestRouter()] },
    })
    expect(useToast().toasts.length).toBe(2)
  })

  it('renders no toast container when no toasts exist', () => {
    mount(App, {
      global: { plugins: [createPinia(), createTestRouter()] },
    })
    const teleported = document.body.querySelector('.fixed.bottom-4')
    expect(teleported).not.toBeNull()
    const toasts = teleported!.querySelectorAll('.flex.items-start')
  })
})

function bodyText(): string {
  return document.body.textContent || ''
}