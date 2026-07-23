"""Constants used throughout the application.

Defines exemplar text snippets per document category, the classification
category list derived from those exemplars, and the typed extraction fields
expected for each category.
"""

CATEGORY_EXEMPLARS: dict[str, list[str]] = {
    "Contract": [
        "This Agreement is entered into as of [Date] by and between [Party A] and [Party B] (each a 'Party' and collectively the 'Parties').",
        "IN WITNESS WHEREOF, the Parties have executed this Agreement as of the date first written above. This Agreement shall be governed by the laws of the State of [State].",
        "Either party may terminate this Agreement upon thirty (30) days written notice. Upon termination, the parties shall fulfill all outstanding obligations accrued prior to the effective date of termination.",
        "Independent Contractor. It is understood and agreed that Consultant is an independent contractor and not an employee of Company. Consultant shall be solely responsible for all taxes and benefits.",
        "This Agreement constitutes the entire understanding between the parties and supersedes all prior agreements, whether written or oral. No modification shall be effective unless in writing signed by both parties.",
    ],
    "RFP/RFQ": [
        "REQUEST FOR PROPOSAL (RFP) #[Number]. [Issuing Organization] is seeking qualified vendors to submit proposals for [Project Name]. Proposals must be received no later than [Date] at [Time].",
        "Evaluation Criteria. Proposals will be evaluated based on the following criteria: technical approach (30%), past performance (20%), cost (35%), and staffing plan (15%). The Contracting Officer will review all responsive submissions.",
        "Submission Instructions. Vendors shall submit one original and three copies of their proposal. All proposals must be signed by an authorized representative. Late proposals will not be considered.",
        "Scope of Work. The Contractor shall provide all labor, materials, and equipment necessary to perform the services described in Exhibit A. The period of performance shall begin on [Start Date].",
        "This solicitation is issued under [Regulation/Policy]. The issuing organization reserves the right to reject any or all proposals and to waive informalities in proposals received.",
    ],
    "Quote/Proposal": [
        "We are pleased to submit this proposal in response to your Request for Quote #[Number]. Our proposed solution leverages our extensive experience in [Domain] to deliver the outcomes you described.",
        "Pricing Summary. The total fixed price for the described scope of work is $[Amount]. This pricing is valid for [Number] days from the date of this proposal. Payment terms are Net 30 upon invoice.",
        "Thank you for the opportunity to provide this quotation. We are confident that our approach will meet your requirements. Please do not hesitate to contact us with any questions regarding this proposal.",
        "Proposed Approach. Our team will follow a phased methodology: Phase 1 — Discovery and Requirements Gathering; Phase 2 — Design and Prototyping; Phase 3 — Implementation and Testing; Phase 4 — Deployment and Training.",
        "We have reviewed your specifications and attached our detailed cost breakdown. This quote includes all labor, materials, software licenses, and travel expenses. Delivery is scheduled within [Number] weeks of order.",
    ],
    "Invoice": [
        "INVOICE #[Number]. Invoice Date: [Date]. Due Date: [Date]. Please remit payment to [Company Name] at [Address]. Reference your Purchase Order Number [PO Number] when submitting payment.",
        "Description of Services: [Service Description]. Quantity: [Qty]. Unit Price: $[Rate]. Total: $[Amount]. Payment Terms: Net 30. Late payments are subject to a [Percent]% monthly finance charge.",
        "Balance Due. Please pay this amount by the due date shown above. If you have any questions regarding this invoice, contact our Accounts Receivable department at [Phone/Email].",
        "Invoice Summary: Subtotal $[Amount]. Sales Tax $[Amount]. Shipping/Handling $[Amount]. Total Due $[Amount]. Make checks payable to [Company Name]. Thank you for your business.",
        "This is a statement of account for the period ending [Date]. Previous Balance: $[Amount]. Payments Received: $[Amount]. New Charges: $[Amount]. Current Amount Due: $[Amount].",
    ],
    "SLA": [
        "Service Level Agreement. Provider shall maintain Monthly Uptime Percentage of at least 99.9%. 'Monthly Uptime Percentage' is calculated as total minutes in month minus total minutes of Downtime, divided by total minutes in month.",
        "If Provider fails to meet the Service Level commitment, Customer shall be eligible for a Service Credit equal to [Percent]% of the monthly fee for each [Number]% below the committed threshold. Service Credits shall not exceed [Percent]% of the monthly fee.",
        "Response Times. Critical incidents shall receive a response within 1 hour and resolution within 4 hours. High priority incidents: 2 hour response, 8 hour resolution. Medium priority: 4 hour response, 24 hour resolution.",
        "Maintenance Windows. Scheduled maintenance shall be performed during the designated maintenance window ([Time] to [Time] on [Day] weekly). Provider shall provide at least [Number] business days notice of scheduled maintenance.",
        "Performance Metrics. The Provider shall report on the following Key Performance Indicators monthly: system availability, average response time, first-call resolution rate, and customer satisfaction score (target: [Number] out of 5).",
    ],
    "Amendment": [
        "This Amendment ([Number]) is made and entered into as of [Date] by and between the parties to that certain [Original Agreement Name] dated [Date] (the 'Agreement').",
        "Section [Number] of the Agreement is hereby deleted in its entirety and replaced with the following: [New Text]. All other terms and conditions of the Agreement shall remain in full force and effect.",
        "The Parties agree to extend the Term of the Agreement by an additional [Number] months, commencing on [Date]. All pricing, service levels, and other provisions shall remain unchanged during the extended term.",
        "This Amendment modifies the pricing structure set forth in Exhibit B of the Agreement. Effective [Date], the monthly fee shall be adjusted to $[Amount]. This adjustment reflects changes in the scope of services described herein.",
        "Except as expressly modified by this Amendment, the Agreement remains unmodified and in full force and effect. In the event of any conflict between this Amendment and the Agreement, the terms of this Amendment shall control.",
    ],
    "NDA": [
        "This Non-Disclosure Agreement (the 'Agreement') is entered into by and between the parties for the purpose of preventing the unauthorized disclosure of Confidential Information. 'Confidential Information' means any non-public information disclosed by one party to the other.",
        "The Receiving Party agrees to hold the Confidential Information in strict confidence and shall not disclose such information to any third party without the prior written consent of the Disclosing Party, except as required by law.",
        "Confidential Information shall not include information that: (a) is or becomes publicly known without breach of this Agreement; (b) was known to the Receiving Party prior to disclosure; or (c) is independently developed by the Receiving Party without use of the Confidential Information.",
        "This Agreement shall terminate [Number] years from the Effective Date. The obligations of confidentiality and non-use shall survive termination for a period of [Number] years. Upon request, the Receiving Party shall return or destroy all Confidential Information.",
        "The parties acknowledge that a breach of this Agreement may cause irreparable harm for which monetary damages would be inadequate. Accordingly, the Disclosing Party shall be entitled to seek injunctive relief without the necessity of posting bond.",
    ],
    "Purchase Order": [
        "PURCHASE ORDER #[Number]. Order Date: [Date]. Payment Terms: Net 30. FOB: Destination. Requested Delivery Date: [Date]. Please reference this Purchase Order number on all packing slips and invoices.",
        "Ship To: [Company Name], [Address], [City, State ZIP]. Vendor: [Vendor Name], [Vendor Address]. Buyer: [Buyer Name]. Please ship via [Carrier] and include the PO number on all correspondence.",
        "Item [Number]. Description: [Item Description]. Quantity Ordered: [Qty]. Unit of Measure: [UOM]. Unit Price: $[Price]. Total Line Amount: $[Total]. This purchase order is subject to the terms and conditions attached hereto.",
        "Authorized by: [Buyer Name], [Title]. This Purchase Order constitutes the entire agreement between Buyer and Seller for the goods described herein. Any modification must be agreed to in writing and signed by both parties.",
        "Delivery Schedule. Line items are to be delivered no later than [Date]. Partial shipments are acceptable unless otherwise noted. All goods must conform to the specifications in Attachment A. Non-conforming goods will be returned at the seller's expense.",
    ],
    "Other": (
        "A procurement-related document that does not clearly fit into any of the "
        "above categories. May include memos, internal forms, correspondence, "
        "or miscellaneous records."
    ),
}

CLASSIFICATION_CATEGORIES = list(CATEGORY_EXEMPLARS.keys())

TYPE_FIELDS: dict[str, dict[str, str]] = {
    "Contract": {
        "parties": "string",
        "effective_date": "string",
        "expiration_date": "string",
        "governing_law": "string",
        "contract_value": "string",
        "signatories": "string",
    },
    "RFP/RFQ": {
        "submission_deadline": "string",
        "issuing_organization": "string",
        "project_title": "string",
        "budget_range": "string",
        "evaluation_criteria": "string",
        "contact_officer": "string",
    },
    "Quote/Proposal": {
        "total_price": "string",
        "valid_until": "string",
        "payment_terms": "string",
        "vendor_name": "string",
        "scope_summary": "string",
        "authorized_representative": "string",
    },
    "Invoice": {
        "invoice_number": "string",
        "invoice_date": "string",
        "due_date": "string",
        "vendor_name": "string",
        "total_amount": "string",
        "purchase_order_reference": "string",
    },
    "SLA": {
        "service_provider": "string",
        "customer": "string",
        "uptime_guarantee": "string",
        "response_time": "string",
        "resolution_time": "string",
        "service_credits": "string",
    },
    "Amendment": {
        "amendment_number": "string",
        "original_agreement_date": "string",
        "effective_date": "string",
        "changed_terms_summary": "string",
        "extended_term": "string",
        "authorized_signatories": "string",
    },
    "NDA": {
        "parties": "string",
        "effective_date": "string",
        "confidentiality_period": "string",
        "governing_law": "string",
        "mutual_or_one_way": "string",
        "signatories": "string",
    },
    "Purchase Order": {
        "po_number": "string",
        "vendor_name": "string",
        "order_date": "string",
        "total_amount": "string",
        "delivery_date": "string",
        "authorized_by": "string",
    },
    "Other": {},
}