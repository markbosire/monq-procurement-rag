/**
 * Source highlight composable.
 *
 * Provides a singleton reactive reference that allows any component to
 * broadcast or observe the currently active highlight (chunk + bbox).
 * Used by ChatPanel (setter) and DocumentViewerPanel (watcher) to keep
 * the PDF viewer in sync with the chat source selection.
 *
 * @packageDocumentation
 * @since 1.0.0
 */

import { shallowRef } from 'vue'
import type { BBox } from '../api/chat'

/** Describes a highlight to be drawn on the PDF canvas. */
export interface SourceViewerHighlight {
  /** Database id of the chunk being highlighted. */
  chunkId: number
  /** Bounding boxes across all pages for this chunk. */
  bbox: BBox[]
}

/**
 * Global reactive reference to the currently active source highlight.
 *
 * Components can watch this ref to react when the user clicks a source
 * chunk in the chat panel.
 */
export const activeHighlight = shallowRef<SourceViewerHighlight | null>(null)

/**
 * Composable that exposes methods to manage the active PDF highlight.
 *
 * @returns An object with the activeHighlight ref, showHighlight, and
 *   clearHighlight actions.
 */
export function useSourceViewer() {
  /**
   * Set the active highlight, which causes the PDF viewer to navigate
   * to the relevant page and draw bounding boxes.
   *
   * @param highlight - The highlight data (chunk id + bbox array).
   */
  function showHighlight(highlight: SourceViewerHighlight) {
    activeHighlight.value = { ...highlight }
  }

  /** Clear the active highlight, removing all overlays from the PDF view. */
  function clearHighlight() {
    activeHighlight.value = null
  }

  return { activeHighlight, showHighlight, clearHighlight }
}
