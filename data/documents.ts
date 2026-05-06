import type { CaseDocument } from "@/types";

type SeedDocument = Omit<
  CaseDocument,
  "intelligenceStatus" | "extractedText" | "extractionError" | "processedAt"
> &
  Partial<
    Pick<
      CaseDocument,
      "intelligenceStatus" | "extractedText" | "extractionError" | "processedAt"
    >
  >;

function seedDocument(document: SeedDocument): CaseDocument {
  return {
    intelligenceStatus:
      document.intelligenceStatus ??
      (document.extractionStatus === "Parsed"
        ? "Processed"
        : document.extractionStatus === "Manual Review"
          ? "Failed"
          : "Not Processed"),
    extractedText: document.extractedText ?? document.previewText,
    extractionError:
      document.extractionError ??
      (document.extractionStatus === "Manual Review"
        ? "Manual extraction review required in the seeded dataset."
        : ""),
    processedAt: document.processedAt ?? null,
    ...document,
  };
}

const seededDocuments: SeedDocument[] = [
  {
    id: "doc-001",
    caseId: "green-valley-dha",
    name: "Plaint with Interim Injunction Application",
    type: "Plaint",
    category: "Primary Pleadings",
    uploadDate: "2026-04-18",
    status: "Under Review",
    extractionStatus: "Parsed",
    tags: ["Urgent", "Injunction", "Maintainability"],
    pages: 22,
    filedBy: "Sara Nadeem",
    summary:
      "Combined plaint and interim relief papers challenging allotment cancellation and seeking restraint.",
    previewText:
      "The plaintiff respectfully submits that the impugned cancellation letter was issued without lawful authority, without affording fair hearing, and in breach of the settled allotment framework...",
  },
  {
    id: "doc-002",
    caseId: "green-valley-dha",
    name: "Payment Schedule and Receipts Bundle",
    type: "Annexure",
    category: "Annexures",
    uploadDate: "2026-04-17",
    status: "Reference",
    extractionStatus: "Ready for Indexing",
    tags: ["Receipts", "Payments", "Annexure-A"],
    pages: 31,
    filedBy: "Case Team Upload",
    summary:
      "Installment receipts, estate branch endorsements, and bank remittance record.",
    previewText:
      "Bundle includes premium payment acknowledgment, installment ledger, and correspondence regarding surcharge objections...",
  },
  {
    id: "doc-003",
    caseId: "green-valley-dha",
    name: "Cancellation Letter dated 09.04.2026",
    type: "Order Sheet",
    category: "Impugned Orders",
    uploadDate: "2026-04-16",
    status: "Reference",
    extractionStatus: "Manual Review",
    tags: ["Impugned Order", "Cancellation"],
    pages: 4,
    filedBy: "Ahsan Qureshi",
    summary:
      "Primary cancellation communication relied upon in the plaint.",
    previewText:
      "The competent authority has been pleased to cancel the allotment for non-compliance with payment obligations and allied terms...",
  },
  {
    id: "doc-004",
    caseId: "sanaullah-bail",
    name: "Bail Petition and Grounds",
    type: "Application",
    category: "Bail Papers",
    uploadDate: "2026-04-14",
    status: "Filed",
    extractionStatus: "Parsed",
    tags: ["Further Inquiry", "Parity"],
    pages: 13,
    filedBy: "Bilal Afridi",
    summary:
      "Filed post-arrest bail petition highlighting civil complexion of dispute.",
    previewText:
      "The petitioner seeks concession of bail on the grounds that the matter is documentary, recovery has no meaningful nexus with custody, and co-accused has already secured relief...",
  },
  {
    id: "doc-005",
    caseId: "sanaullah-bail",
    name: "FIR, Remand, and Challan Extracts",
    type: "Annexure",
    category: "Criminal Record",
    uploadDate: "2026-04-13",
    status: "Reference",
    extractionStatus: "Parsed",
    tags: ["FIR", "Remand", "Challan"],
    pages: 27,
    filedBy: "Support Desk",
    summary:
      "Core criminal process documents assembled for hearing prep.",
    previewText:
      "The FIR narrates alleged inducement in connection with machinery supply, followed by arrest memo, remand orders, and incomplete challan materials...",
  },
  {
    id: "doc-006",
    caseId: "horizon-customs-petition",
    name: "Constitutional Petition Draft",
    type: "Plaint",
    category: "Primary Pleadings",
    uploadDate: "2026-04-20",
    status: "Under Review",
    extractionStatus: "Parsed",
    tags: ["Article 199", "Customs", "Urgent"],
    pages: 28,
    filedBy: "Drafting Agent",
    summary:
      "Main petition challenging detention and valuation enhancement.",
    previewText:
      "The petitioner company seeks constitutional relief against unlawful detention of imported textile inputs and arbitrary deviation from established valuation practice...",
  },
  {
    id: "doc-007",
    caseId: "horizon-customs-petition",
    name: "Stay Application for Release of Consignment",
    type: "Application",
    category: "Interim Relief",
    uploadDate: "2026-04-20",
    status: "Pending Signature",
    extractionStatus: "Ready for Indexing",
    tags: ["Stay", "Release", "Production Risk"],
    pages: 9,
    filedBy: "Usman Tariq",
    summary:
      "Interim application for release of detained consignment on secured terms.",
    previewText:
      "Unless interim protection is granted, the petitioner faces production disruption, export delay exposure, and avoidable financial prejudice...",
  },
  {
    id: "doc-008",
    caseId: "horizon-customs-petition",
    name: "Valuation Matrix and Invoice Bundle",
    type: "Annexure",
    category: "Trade Record",
    uploadDate: "2026-04-19",
    status: "Reference",
    extractionStatus: "OCR Running",
    tags: ["Invoices", "Valuation", "Annexure-C"],
    pages: 46,
    filedBy: "Trade Documentation Desk",
    summary:
      "Invoice history, prior assessment record, and internal valuation comparison sheet.",
    previewText:
      "Comparative matrix shows variance between prior cleared consignments and the impugned provisional enhancement...",
  },
  {
    id: "doc-009",
    caseId: "mehr-un-nisa-service",
    name: "Service Appeal Memo",
    type: "Application",
    category: "Appeal Papers",
    uploadDate: "2026-04-15",
    status: "Draft",
    extractionStatus: "Parsed",
    tags: ["Promotion", "Service Appeal"],
    pages: 17,
    filedBy: "Faraz Latif",
    summary:
      "Appeal memo challenging supersession and non-promotion.",
    previewText:
      "The appellant was repeatedly superseded despite seniority, clean service record, and favorable departmental recommendation...",
  },
  {
    id: "doc-010",
    caseId: "mehr-un-nisa-service",
    name: "Departmental Recommendation Letters",
    type: "Annexure",
    category: "Departmental Record",
    uploadDate: "2026-04-14",
    status: "Reference",
    extractionStatus: "Manual Review",
    tags: ["Recommendations", "Seniority"],
    pages: 12,
    filedBy: "Client Intake",
    summary:
      "Letters and notings showing internal recommendation for promotion.",
    previewText:
      "Internal office notes recommend promotion on merit and seniority grounds, though the final decision is not communicated by speaking order...",
  },
  {
    id: "doc-011",
    caseId: "al-habib-revenue",
    name: "Revenue Revision Petition",
    type: "Application",
    category: "Revision Papers",
    uploadDate: "2026-04-19",
    status: "Under Review",
    extractionStatus: "Parsed",
    tags: ["Mutation", "Revision", "Notice"],
    pages: 18,
    filedBy: "Umair Hafeez",
    summary:
      "Revision petition targeting mutation proceedings and appellate orders.",
    previewText:
      "The impugned mutation proceedings suffer from defective notice, incomplete scrutiny of lineage record, and misreading of possession claims...",
  },
  {
    id: "doc-012",
    caseId: "al-habib-revenue",
    name: "Certified Mutation Record",
    type: "Annexure",
    category: "Revenue Record",
    uploadDate: "2026-04-18",
    status: "Reference",
    extractionStatus: "Ready for Indexing",
    tags: ["Mutation", "Revenue Record"],
    pages: 34,
    filedBy: "Court Runner",
    summary:
      "Certified copies of disputed mutation, appellate order, and jamabandi extracts.",
    previewText:
      "Record bundle contains mutation entries, endorsement sheets, and appellate observations relevant to notice and locus challenges...",
  },
  {
    id: "doc-013",
    caseId: "raza-foods-civil",
    name: "Written Statement of Defendant",
    type: "Written Statement",
    category: "Pleadings",
    uploadDate: "2026-04-10",
    status: "Filed",
    extractionStatus: "Parsed",
    tags: ["Exclusion Clause", "Damages"],
    pages: 19,
    filedBy: "Litigation Support",
    summary:
      "Defendant's written statement relying on contractual exclusions and causation objections.",
    previewText:
      "The defendant denies negligence and pleads contractual limitation of liability, disputed temperature data, and failure of proof on special damages...",
  },
  {
    id: "doc-014",
    caseId: "raza-foods-civil",
    name: "Warehouse Loss Assessment",
    type: "Affidavit",
    category: "Evidence",
    uploadDate: "2026-04-09",
    status: "Reference",
    extractionStatus: "Ready for Indexing",
    tags: ["Affidavit", "Spoilage", "Damages"],
    pages: 8,
    filedBy: "Client Finance Team",
    summary:
      "Affidavit and internal damage assessment used to quantify spoilage losses.",
    previewText:
      "Assessment records stock spoilage, batch disposal decisions, and estimated financial exposure arising from delayed refrigerated transport...",
  },
];

export const documents: CaseDocument[] = seededDocuments.map(seedDocument);

export function getDocumentsByCase(caseId: string) {
  return documents.filter((document) => document.caseId === caseId);
}
