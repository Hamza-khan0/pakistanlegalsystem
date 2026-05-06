import type { ResearchNote } from "@/types";

export const researchNotes: ResearchNote[] = [
  {
    id: "rn-001",
    caseId: "green-valley-dha",
    title: "Maintainability exceptions despite internal remedy",
    status: "Verified",
    author: "Research Agent",
    updatedAt: "2026-04-19",
    authorities: ["PLD 2018 Lahore 412", "2021 CLC 1188"],
    summary:
      "Authorities support court intervention where cancellation is alleged to be void on its face, commercially prejudicial, and accompanied by threatened third-party transfer.",
    nextQuestion:
      "Need one more authority distinguishing contractual remedy from public law taint in allotment matters.",
  },
  {
    id: "rn-002",
    caseId: "green-valley-dha",
    title: "Interim injunction framing note",
    status: "Fresh",
    author: "Critic Agent",
    updatedAt: "2026-04-20",
    authorities: ["Specific Relief Act, 1877", "2023 CLC Note 67"],
    summary:
      "Bench-facing note recommends leading with irreparable prejudice and possession risk rather than detailed merits at the ad interim stage.",
    nextQuestion:
      "Confirm whether partial possession evidence can be shown without inviting factual controversy.",
  },
  {
    id: "rn-003",
    caseId: "sanaullah-bail",
    title: "Further inquiry and parity digest",
    status: "Verified",
    author: "Research Agent",
    updatedAt: "2026-04-18",
    authorities: ["2022 SCMR 1028", "PLD 1995 SC 34"],
    summary:
      "Digest frames the matter as one of further inquiry due to documentary dispute, delayed FIR, and parity with similarly placed co-accused.",
    nextQuestion:
      "Upload the certified parity order to strengthen the bench brief.",
  },
  {
    id: "rn-004",
    caseId: "horizon-customs-petition",
    title: "Alternate remedy exceptions in customs petition",
    status: "Verified",
    author: "Research Agent",
    updatedAt: "2026-04-20",
    authorities: ["PLD 2020 Sindh 221", "2023 PTD 1442"],
    summary:
      "Constitutional jurisdiction remains arguable where detention is coupled with denial of hearing and immediate commercial injury that statutory remedy cannot promptly cure.",
    nextQuestion:
      "Need one supporting authority on release against security in valuation disputes.",
  },
  {
    id: "rn-005",
    caseId: "horizon-customs-petition",
    title: "Valuation deviation checklist",
    status: "Needs Review",
    author: "Memory Agent",
    updatedAt: "2026-04-19",
    authorities: ["Customs Act, 1969"],
    summary:
      "Checklist tracks the documentary ingredients required to show selective valuation departure from prior consignments.",
    nextQuestion:
      "Verify invoice endorsements before relying on the comparison table in oral submissions.",
  },
  {
    id: "rn-006",
    caseId: "mehr-un-nisa-service",
    title: "Condonation landscape in service appeal",
    status: "Fresh",
    author: "Procedural Agent",
    updatedAt: "2026-04-17",
    authorities: ["2019 PLC(CS) 877", "2021 SCMR 455"],
    summary:
      "Research suggests delay can be argued through continuing cause only if representation record is specifically pleaded and tied to absence of speaking order.",
    nextQuestion:
      "Need documentary cross-check of all representation dates before the condonation application is finalized.",
  },
  {
    id: "rn-007",
    caseId: "al-habib-revenue",
    title: "Revenue revision grounds note",
    status: "Verified",
    author: "Research Agent",
    updatedAt: "2026-04-18",
    authorities: ["2020 PLJ Revenue 55", "2024 CLC 901"],
    summary:
      "Revision grounds are strongest where mutation notice defects and incomplete appreciation of lineage record appear from the record itself.",
    nextQuestion:
      "Attach genealogy chart to make the locus challenge visually clear.",
  },
  {
    id: "rn-008",
    caseId: "raza-foods-civil",
    title: "Damages proof roadmap",
    status: "Fresh",
    author: "Memory Agent",
    updatedAt: "2026-04-16",
    authorities: ["2018 CLC 233", "2022 CLD 1044"],
    summary:
      "Recommends bundling transport logs, warehouse records, and expert opinion to survive exclusion-clause and remoteness objections.",
    nextQuestion:
      "Decide whether independent expert can be retained before issues are framed.",
  },
];

export function getResearchByCase(caseId: string) {
  return researchNotes.filter((note) => note.caseId === caseId);
}
