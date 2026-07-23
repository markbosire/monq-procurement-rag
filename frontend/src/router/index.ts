/**
 * Application router configuration.
 *
 * Uses Vue Router in HTML5 history mode. Defines three routes:
 * - `/` redirects to `/documents`
 * - `/documents` lists all documents
 * - `/documents/:id` opens the chat + PDF viewer for a specific document
 *
 * @packageDocumentation
 * @since 1.0.0
 */

import { createRouter, createWebHistory } from 'vue-router'

// ── Routes ─────────────────────────────────────────────────────────

/** Route definitions. */
const routes = [
  {
    path: '/',
    redirect: '/documents',
  },
  {
    path: '/documents',
    name: 'documents',
    component: () => import('../pages/DocumentGridPage.vue'),
  },
  {
    path: '/documents/:id',
    name: 'document-chat',
    component: () => import('../pages/DocumentChatPage.vue'),
    props: true,
  },
]

// ── Instance ───────────────────────────────────────────────────────

/** Router instance with HTML5 history mode. */
const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
