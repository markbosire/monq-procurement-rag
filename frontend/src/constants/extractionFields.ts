/**
 * Field label and section-group definitions for document extraction display.
 *
 * Maps backend field keys to human-readable labels and organises them
 * into themed groups for the metadata panel.
 *
 * @packageDocumentation
 * @since 1.0.0
 */

/** A named group of extraction field keys displayed together. */
export interface SectionGroup {
  /** Section heading label. */
  label: string
  /** Field keys that belong to this section. */
  keys: string[]
}

// ── Labels ─────────────────────────────────────────────────────────

/** Maps backend extraction field keys to human-readable display labels. */
export const fieldLabels: Record<string, string> = {
  parties: 'Parties',
  effective_date: 'Effective Date',
  expiration_date: 'Expiration Date',
  governing_law: 'Governing Law',
  contract_value: 'Contract Value',
  signatories: 'Signatories',
  submission_deadline: 'Submission Deadline',
  issuing_organization: 'Issuing Organization',
  project_title: 'Project Title',
  budget_range: 'Budget Range',
  evaluation_criteria: 'Evaluation Criteria',
  contact_officer: 'Contact Officer',
  total_price: 'Total Price',
  valid_until: 'Valid Until',
  payment_terms: 'Payment Terms',
  vendor_name: 'Vendor Name',
  scope_summary: 'Scope Summary',
  authorized_representative: 'Authorized Representative',
  invoice_number: 'Invoice Number',
  invoice_date: 'Invoice Date',
  due_date: 'Due Date',
  total_amount: 'Total Amount',
  purchase_order_reference: 'PO Reference',
  service_provider: 'Service Provider',
  customer: 'Customer',
  uptime_guarantee: 'Uptime Guarantee',
  response_time: 'Response Time',
  resolution_time: 'Resolution Time',
  service_credits: 'Service Credits',
  amendment_number: 'Amendment Number',
  original_agreement_date: 'Original Agreement Date',
  changed_terms_summary: 'Changed Terms',
  extended_term: 'Extended Term',
  authorized_signatories: 'Authorized Signatories',
  confidentiality_period: 'Confidentiality Period',
  mutual_or_one_way: 'Mutual or One-Way',
  po_number: 'PO Number',
  order_date: 'Order Date',
  delivery_date: 'Delivery Date',
  authorized_by: 'Authorized By',
}

// ── Groups ─────────────────────────────────────────────────────────

/** Themed groups for organising extracted fields in the metadata panel. */
export const sectionGroups: SectionGroup[] = [
  { label: 'Agreement', keys: ['parties', 'effective_date', 'expiration_date', 'governing_law', 'contract_value', 'signatories'] },
  { label: 'Submission', keys: ['submission_deadline', 'issuing_organization', 'project_title', 'budget_range', 'evaluation_criteria', 'contact_officer'] },
  { label: 'Financial', keys: ['total_price', 'valid_until', 'payment_terms', 'vendor_name', 'scope_summary', 'authorized_representative'] },
  { label: 'Invoice', keys: ['invoice_number', 'invoice_date', 'due_date', 'total_amount', 'purchase_order_reference'] },
  { label: 'Service', keys: ['service_provider', 'customer', 'uptime_guarantee', 'response_time', 'resolution_time', 'service_credits'] },
  { label: 'Amendment', keys: ['amendment_number', 'original_agreement_date', 'changed_terms_summary', 'extended_term', 'authorized_signatories'] },
  { label: 'Confidentiality', keys: ['confidentiality_period', 'mutual_or_one_way'] },
  { label: 'Purchase Order', keys: ['po_number', 'order_date', 'delivery_date', 'authorized_by'] },
]
