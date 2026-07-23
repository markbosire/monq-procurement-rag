import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { mount } from '@vue/test-utils'
import type { Component } from 'vue'
import type { MountingOptions, Router } from '@vue/test-utils'
import type { DocumentListItem, DocumentResponse } from '../api/documents'
import type { ChatResponse, SourceChunk } from '../api/chat'
import type { ChatMessage } from '../stores/useChatStore'

export function createMockDocumentListItem(overrides?: Partial<DocumentListItem>): DocumentListItem {
  return {
    document_id: 'doc-001',
    filename: 'test-document.pdf',
    category: 'RFP/RFQ',
    chunk_count: 5,
    title: 'Test Document',
    created_at: '2025-01-01T00:00:00Z',
    ...overrides,
  }
}

export function createMockDocumentResponse(overrides?: Partial<DocumentResponse>): DocumentResponse {
  return {
    document_id: 'doc-001',
    classification: { category: 'RFP/RFQ', confidence: 0.95, reasoning: 'High confidence match' },
    chunk_count: 5,
    status: 'ready',
    title: 'Test Document',
    summary: 'A test document summary.',
    extractions: null,
    ...overrides,
  }
}

export function createMockSourceChunk(overrides?: Partial<SourceChunk>): SourceChunk {
  return {
    id: 1,
    text: 'Relevant chunk text for the answer.',
    page_numbers: [1, 2],
    bbox: [{ page: 1, x0: 0, y0: 0, x1: 100, y1: 50 }],
    ...overrides,
  }
}

export function createMockChatMessage(overrides?: Partial<ChatMessage>): ChatMessage {
  return {
    role: 'assistant',
    content: 'This is a test answer.',
    source_chunks: [createMockSourceChunk()],
    ...overrides,
  }
}

export function createMockChatResponse(overrides?: Partial<ChatResponse>): ChatResponse {
  return {
    answer: 'This is a test answer.',
    source_chunks: [createMockSourceChunk()],
    ...overrides,
  }
}

export function createMockFile(name = 'test.pdf', size = 1024, type = 'application/pdf'): File {
  const blob = new Blob(['fake pdf content'], { type })
  return new File([blob], name, { type })
}

export function createTestRouter(): Router {
  const routes = [
    { path: '/', redirect: '/documents' },
    { path: '/documents', name: 'documents', component: { template: '<div>Document Grid</div>' } },
    { path: '/documents/:id', name: 'document-chat', component: { template: '<div>Document Chat</div>' }, props: true },
  ]
  return createRouter({ history: createWebHistory(), routes })
}

export function createMockPdfDocument(numPages = 5) {
  const mockRender = { promise: Promise.resolve(), cancel: vi.fn() }
  const mockPage = {
    getViewport: vi.fn((opts: { scale: number }) => ({
      height: 800 * (opts?.scale ?? 1),
      width: 600 * (opts?.scale ?? 1),
    })),
    render: vi.fn().mockReturnValue(mockRender),
  }
  return {
    numPages,
    getPage: vi.fn().mockResolvedValue(mockPage),
    _mockPage: mockPage,
    _mockRender: mockRender,
  }
}

export function renderWithSetup(
  component: Component,
  options: MountingOptions<Record<string, unknown>> = {},
) {
  const pinia = createPinia()
  setActivePinia(pinia)
  const router = createTestRouter()
  const wrapper = mount(component, {
    global: { plugins: [pinia, router] },
    ...options,
  })
  return { wrapper, pinia, router }
}

export function setupCommonMocks() {
  if (typeof window !== 'undefined' && !window.matchMedia) {
    Object.defineProperty(window, 'matchMedia', {
      writable: true,
      value: vi.fn().mockImplementation((query: string) => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: vi.fn(),
        removeListener: vi.fn(),
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        dispatchEvent: vi.fn(),
      })),
    })
  }
  if (typeof window !== 'undefined' && !window.ResizeObserver) {
    Object.defineProperty(window, 'ResizeObserver', {
      writable: true,
      value: vi.fn().mockImplementation(() => ({
        observe: vi.fn(),
        unobserve: vi.fn(),
        disconnect: vi.fn(),
      })),
    })
  }
}

export function flushPromises(): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, 0))
}
