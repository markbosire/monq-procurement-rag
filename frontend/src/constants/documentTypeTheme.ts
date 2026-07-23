/**
 * Document-type theming constants.
 *
 * Maps each procurement category to a visual theme (icon, colour palette)
 * used throughout the UI for badges, cards, headers, and highlights.
 *
 * @packageDocumentation
 * @since 1.0.0
 */

import {
  FileSignature, FileSearch, Receipt, Lock, ClipboardList,
  ShieldCheck, FileText, FileEdit, File,
  type LucideIcon,
} from 'lucide-vue-next'

/** Visual theme for a document category. */
export interface TypeTheme {
  /** Lucide icon component to display. */
  icon: LucideIcon
  /** Primary accent colour (hex). */
  color: string
  /** Light background colour. */
  bg: string
  /** Slightly darker background for hover states. */
  bgLight: string
  /** Border colour. */
  border: string
  /** Darker accent for interactive elements. */
  accent: string
}

/** Mapping of category names to their visual themes. */
export const DOCUMENT_TYPE_THEME: Record<string, TypeTheme> = {
  'Contract':       { icon: FileSignature, color: '#2563eb', bg: '#eff6ff', bgLight: '#dbeafe', border: '#bfdbfe', accent: '#1d4ed8' },
  'RFP/RFQ':        { icon: FileSearch,    color: '#7c3aed', bg: '#f5f3ff', bgLight: '#ede9fe', border: '#e9d5ff', accent: '#6d28d9' },
  'Invoice':        { icon: Receipt,       color: '#059669', bg: '#ecfdf5', bgLight: '#d1fae5', border: '#a7f3d0', accent: '#047857' },
  'NDA':            { icon: Lock,          color: '#dc2626', bg: '#fef2f2', bgLight: '#fee2e2', border: '#fecaca', accent: '#b91c1c' },
  'Purchase Order': { icon: ClipboardList, color: '#d97706', bg: '#fffbeb', bgLight: '#fef3c7', border: '#fde68a', accent: '#b45309' },
  'SLA':            { icon: ShieldCheck,   color: '#0891b2', bg: '#ecfeff', bgLight: '#cffafe', border: '#a5f3fc', accent: '#0e7490' },
  'Quote/Proposal': { icon: FileText,      color: '#4f46e5', bg: '#eef2ff', bgLight: '#e0e7ff', border: '#c7d2fe', accent: '#4338ca' },
  'Amendment':      { icon: FileEdit,      color: '#db2777', bg: '#fdf2f8', bgLight: '#fce7f3', border: '#fbcfe8', accent: '#be185d' },
  'Other':          { icon: File,          color: '#6b7280', bg: '#f9fafb', bgLight: '#f3f4f6', border: '#e5e7eb', accent: '#4b5563' },
}

/**
 * Resolve the theme for a document category.
 *
 * Falls back to the "Other" theme when the category is null, undefined,
 * or not found in the theme map.
 *
 * @param category - The document's classification category.
 * @returns The matching TypeTheme object.
 */
export function getTypeTheme(category: string | null | undefined): TypeTheme {
  return DOCUMENT_TYPE_THEME[category || ''] || DOCUMENT_TYPE_THEME['Other']
}
