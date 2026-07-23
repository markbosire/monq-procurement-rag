import { describe, it, expect } from 'vitest'
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/documents' },
  { path: '/documents', name: 'documents', component: { template: '<div>Grid</div>' } },
  { path: '/documents/:id', name: 'document-chat', component: { template: '<div>Chat {{ $props.id }}</div>' }, props: true },
]

describe('router', () => {
  it('redirects / to /documents', async () => {
    const router = createRouter({ history: createWebHistory(), routes })
    await router.push('/')
    await router.isReady()
    expect(router.currentRoute.value.path).toBe('/documents')
  })

  it('resolves /documents route', async () => {
    const router = createRouter({ history: createWebHistory(), routes })
    await router.push('/documents')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('documents')
    expect(router.currentRoute.value.path).toBe('/documents')
  })

  it('resolves /documents/:id route with params', async () => {
    const router = createRouter({ history: createWebHistory(), routes })
    await router.push('/documents/doc-123')
    await router.isReady()
    expect(router.currentRoute.value.name).toBe('document-chat')
    expect(router.currentRoute.value.params.id).toBe('doc-123')
  })

  it('has props: true on :id route definition', () => {
    const routeDef = routes.find(r => r.path === '/documents/:id')
    expect(routeDef?.props).toBe(true)
  })
})
