import type { CaseMatter } from "@/types";

export const cases: CaseMatter[] = [
  {
    id: "green-valley-dha",
    title: "M/s Green Valley Estate Pvt. Ltd. v. Defence Housing Authority, Lahore",
    caseNumber: "Civil Suit No. 102/2026",
    forum: "Lahore High Court, Lahore",
    matterType: "Property Dispute",
    status: "Hearing Due",
    priority: "Critical",
    stage: "Interim injunction pending before motion bench",
    client: "M/s Green Valley Estate Pvt. Ltd.",
    opposingParty: "Defence Housing Authority, Lahore",
    nextHearingDate: "2026-04-24",
    assignedCounsel: ["Ahsan Qureshi", "Sara Nadeem"],
    teamAgents: ["Manager Agent", "Research Agent", "Drafting Agent"],
    summary:
      "The client challenges unilateral cancellation of a commercial allotment after substantial development payments and partial possession. Immediate focus is on preserving the plot and restraining third-party transfer before the next hearing.",
    issues: [
      "Validity of cancellation without speaking order",
      "Maintainability of civil action despite internal DHA remedies",
      "Threshold for interim protection over allotted commercial property",
    ],
    reliefSought: [
      "Declaration that cancellation letter is void and without lawful authority",
      "Permanent injunction against alienation of the plot",
      "Interim stay restraining coercive dispossession",
    ],
    importantNotes: [
      "Court has asked for clearer chronology on payment defaults versus approvals.",
      "Client expects injunction arguments to foreground irreparable loss and balance of convenience.",
      "Missing sanctioned site map remains a weak documentary gap.",
    ],
    factsBackground: [
      {
        label: "Allotment",
        text: "Commercial plot was allotted in 2021 after premium payment and installment schedule approved by DHA estate branch.",
      },
      {
        label: "Dispute Trigger",
        text: "Cancellation letter was issued after the client sought correction of demarcation and disputed an administrative surcharge not found in the original allotment terms.",
      },
      {
        label: "Urgency",
        text: "The client received informal information that the plot may be offered to another allottee if no restraint order is secured this week.",
      },
    ],
    linkedStatutes: [
      "Specific Relief Act, 1877",
      "Transfer of Property Act, 1882",
      "DHA Estate and Building Regulations (placeholder)",
    ],
    precedents: ["2021 CLC 1188", "PLD 2018 Lahore 412", "2023 CLC Note 67"],
    linkedDocumentIds: ["doc-001", "doc-002", "doc-003"],
    timelineIds: ["tl-001", "tl-002", "tl-003"],
    researchNoteIds: ["rn-001", "rn-002"],
    draftArtifacts: [
      {
        id: "draft-001",
        title: "Interim Injunction Application",
        type: "Application",
        status: "Reviewing",
        updatedAt: "2026-04-19",
        owner: "Drafting Agent",
        summary:
          "Updated to foreground possession risk and attach payment schedule annexures.",
      },
      {
        id: "draft-002",
        title: "Rejoinder to Preliminary Objections",
        type: "Reply",
        status: "Drafting",
        updatedAt: "2026-04-18",
        owner: "Sara Nadeem",
        summary:
          "Targets DHA's maintainability objection and internal remedy argument.",
      },
    ],
    riskFlags: [
      "Sanctioned site map not uploaded",
      "Internal appeal record incomplete",
      "Opposite side likely to press jurisdiction objection",
    ],
    proceduralAlerts: [
      "Prepare short note on urgency before 10:00 AM filing cut-off",
      "Verify vakalatnama on latest authorization letter",
    ],
    tags: ["Injunction", "Commercial Plot", "Maintainability"],
  },
  {
    id: "sanaullah-bail",
    title: "Sanaullah Khan v. The State",
    caseNumber: "Criminal Bail Application No. 54-P/2026",
    forum: "Peshawar High Court",
    matterType: "Bail Matter",
    status: "Active",
    priority: "High",
    stage: "Post-arrest bail arguments partly heard",
    client: "Sanaullah Khan",
    opposingParty: "The State through SHO Police Station City",
    nextHearingDate: "2026-04-27",
    assignedCounsel: ["Maha Siddiqui", "Bilal Afridi"],
    teamAgents: ["Manager Agent", "Critic Agent", "Procedural Agent"],
    summary:
      "Post-arrest bail matter arising from a commercial fraud FIR. Defence position is built around delay in registration, documentary nature of dispute, and parity with co-accused already enlarged on bail.",
    issues: [
      "Whether disputed transaction is predominantly civil in complexion",
      "Effect of delay and improved statements on further inquiry",
      "Parity with co-accused already admitted to bail",
    ],
    reliefSought: [
      "Post-arrest bail pending trial",
      "Direction for expeditious conclusion of challan if bail opposed",
    ],
    importantNotes: [
      "Client must not contradict stance on document execution dates.",
      "Complainant has started relying on WhatsApp transcripts not yet formally exhibited.",
    ],
    factsBackground: [
      {
        label: "FIR Context",
        text: "Complaint arises from advance payment for supply of imported machinery, with delivery delays later recast as dishonest inducement.",
      },
      {
        label: "Defence Position",
        text: "Record suggests prior business dealing and settlement discussions before registration of FIR.",
      },
      {
        label: "Trial Posture",
        text: "Investigation file is incomplete and recovery allegations remain generalized.",
      },
    ],
    linkedStatutes: [
      "Code of Criminal Procedure, 1898",
      "Pakistan Penal Code, 1860",
      "Qanun-e-Shahadat Order, 1984",
    ],
    precedents: ["PLD 1995 SC 34", "2022 SCMR 1028", "2024 YLR 611"],
    linkedDocumentIds: ["doc-004", "doc-005"],
    timelineIds: ["tl-004", "tl-005", "tl-006"],
    researchNoteIds: ["rn-003"],
    draftArtifacts: [
      {
        id: "draft-003",
        title: "Supplementary Bail Synopsis",
        type: "Brief",
        status: "Ready for Filing",
        updatedAt: "2026-04-18",
        owner: "Maha Siddiqui",
        summary:
          "Condenses parity, delay, and civil nature arguments into a two-page bench note.",
      },
    ],
    riskFlags: [
      "Uncertified chat screenshots may create factual noise",
      "Parity case order copy still awaited from trial counsel",
    ],
    proceduralAlerts: [
      "Secure certified copy of co-accused bail order",
      "Update chronology with arrest and remand dates",
    ],
    tags: ["Further Inquiry", "Parity", "Commercial Fraud FIR"],
  },
  {
    id: "horizon-customs-petition",
    title: "M/s Horizon Textiles v. Federation of Pakistan",
    caseNumber: "C.P. No. D-1182/2026",
    forum: "Sindh High Court, Karachi",
    matterType: "Constitutional Petition",
    status: "Drafting",
    priority: "High",
    stage: "Petition and stay application under final partner review",
    client: "M/s Horizon Textiles",
    opposingParty: "Federation of Pakistan through FBR and Collectorate of Customs",
    nextHearingDate: "2026-04-30",
    assignedCounsel: ["Hira Kamal", "Usman Tariq"],
    teamAgents: ["Manager Agent", "Research Agent", "Critic Agent"],
    summary:
      "Petition challenges detention and enhanced valuation of textile inputs despite prior clearance practice. The relief strategy is to frame the matter as jurisdictional overreach coupled with violation of fair hearing.",
    issues: [
      "Jurisdictional limits on provisional enhancement of valuation",
      "Violation of audi alteram partem before adverse assessment",
      "Maintainability of constitutional petition despite alternate remedy",
    ],
    reliefSought: [
      "Declaration that impugned detention and valuation letter are without lawful authority",
      "Release of consignment against secured terms",
      "Restraint against coercive recovery pending decision",
    ],
    importantNotes: [
      "Need cleaner annexure index linking every invoice to the valuation matrix.",
      "Bench usually asks first about alternate remedy under customs law.",
    ],
    factsBackground: [
      {
        label: "Commercial Context",
        text: "The importer operates on tight production cycles and detention of the consignment is already affecting export commitments.",
      },
      {
        label: "Administrative Action",
        text: "Collectorate withheld release and issued a valuation departure note without a hearing opportunity.",
      },
      {
        label: "Strategic Angle",
        text: "The strongest constitutional hook lies in procedural illegality and selective deviation from the prior assessment history.",
      },
    ],
    linkedStatutes: [
      "Constitution of the Islamic Republic of Pakistan, 1973",
      "Customs Act, 1969",
      "Sales Tax Act, 1990",
    ],
    precedents: ["PLD 2020 Sindh 221", "2023 PTD 1442", "2025 PTCL 318"],
    linkedDocumentIds: ["doc-006", "doc-007", "doc-008"],
    timelineIds: ["tl-007", "tl-008", "tl-009"],
    researchNoteIds: ["rn-004", "rn-005"],
    draftArtifacts: [
      {
        id: "draft-004",
        title: "Constitutional Petition",
        type: "Plaint",
        status: "Reviewing",
        updatedAt: "2026-04-20",
        owner: "Drafting Agent",
        summary:
          "Reworked maintainability section to anchor exceptions to alternate remedy.",
      },
      {
        id: "draft-005",
        title: "Stay Application",
        type: "Application",
        status: "Ready for Filing",
        updatedAt: "2026-04-20",
        owner: "Usman Tariq",
        summary:
          "Focused on production disruption and export exposure.",
      },
    ],
    riskFlags: [
      "Two invoices still missing customs endorsement",
      "Alternate remedy objection likely at threshold",
    ],
    proceduralAlerts: [
      "Finalize synopsis and list of dates",
      "Check annexure pagination before filing set is printed",
    ],
    tags: ["Article 199", "Customs", "Urgent Release"],
  },
  {
    id: "mehr-un-nisa-service",
    title: "Mehr-un-Nisa v. Punjab Education Department",
    caseNumber: "Service Appeal No. 18/2026",
    forum: "Punjab Service Tribunal, Lahore",
    matterType: "Service Matter",
    status: "Research",
    priority: "Medium",
    stage: "Condonation and maintainability research underway",
    client: "Mehr-un-Nisa",
    opposingParty: "Punjab Education Department",
    nextHearingDate: "2026-05-05",
    assignedCounsel: ["Faraz Latif"],
    teamAgents: ["Research Agent", "Procedural Agent", "Memory Agent"],
    summary:
      "Appeal challenges non-promotion despite seniority and departmental recommendations. Key question is whether delay can be condoned in light of continuing cause and repeated representations.",
    issues: [
      "Limitation and continuing cause in service appeal",
      "Evidentiary value of departmental recommendations",
      "Scope of relief where promotion slots have since been filled",
    ],
    reliefSought: [
      "Setting aside impugned non-promotion order",
      "Direction for reconsideration with due seniority benefits",
      "Consequential benefits subject to final determination",
    ],
    importantNotes: [
      "Client's service record is clean but record of formal communication is patchy.",
      "Need to reconcile representation dates before pleading continuing cause.",
    ],
    factsBackground: [
      {
        label: "Career Progression",
        text: "The appellant has served in the department for over eighteen years and claims supersession by juniors.",
      },
      {
        label: "Departmental Record",
        text: "Internal noting appears favorable, but the final promotion board minutes are not yet on record.",
      },
      {
        label: "Limitation Sensitivity",
        text: "Delay explanation depends on a series of representations and lack of speaking response.",
      },
    ],
    linkedStatutes: [
      "Punjab Service Tribunals Act, 1974",
      "Punjab Civil Servants Act, 1974",
      "Relevant Service Rules (placeholder)",
    ],
    precedents: ["2019 PLC(CS) 877", "2021 SCMR 455"],
    linkedDocumentIds: ["doc-009", "doc-010"],
    timelineIds: ["tl-010", "tl-011"],
    researchNoteIds: ["rn-006"],
    draftArtifacts: [
      {
        id: "draft-006",
        title: "Condonation Application",
        type: "Application",
        status: "Drafting",
        updatedAt: "2026-04-17",
        owner: "Procedural Agent",
        summary:
          "Organizes delay explanation around repeated departmental representations.",
      },
    ],
    riskFlags: [
      "Final promotion board minutes absent",
      "Representation dates need documentary support",
    ],
    proceduralAlerts: [
      "Obtain departmental forwarding letter",
      "Confirm service book extracts before drafting final appeal memo",
    ],
    tags: ["Promotion", "Limitation", "Continuing Cause"],
  },
  {
    id: "al-habib-revenue",
    title: "Al-Habib Developers v. Board of Revenue, Punjab",
    caseNumber: "Revenue Revision No. 77/2026",
    forum: "Board of Revenue, Punjab",
    matterType: "Revenue Matter",
    status: "Awaiting Filing",
    priority: "Medium",
    stage: "Revision petition and annexure set being finalized",
    client: "Al-Habib Developers",
    opposingParty: "Board of Revenue, Punjab and private respondents",
    nextHearingDate: "2026-05-08",
    assignedCounsel: ["Umair Hafeez", "Rida Ameen"],
    teamAgents: ["Drafting Agent", "Procedural Agent"],
    summary:
      "Revenue revision challenges mutation entries and remand proceedings affecting a peri-urban land parcel earmarked for development. Focus is on defects in locus, notice, and record appreciation.",
    issues: [
      "Legality of mutation sanctioned without complete notice",
      "Scope of revision against concurrent adverse findings",
      "Treatment of private respondents' possession narrative",
    ],
    reliefSought: [
      "Setting aside impugned mutation and appellate orders",
      "Fresh decision after lawful notice and record scrutiny",
    ],
    importantNotes: [
      "Counsel wants revenue record genealogy diagram prepared for the brief.",
      "Patwari extracts are legible but not fully indexed.",
    ],
    factsBackground: [
      {
        label: "Land Record History",
        text: "Dispute concerns correction of revenue entries following competing inheritance and sale claims over contiguous khasra numbers.",
      },
      {
        label: "Procedural Defect",
        text: "Client alleges notice did not effectively reach all interested parties before mutation sanction.",
      },
      {
        label: "Current Posture",
        text: "Revision is the immediate vehicle to prevent further reliance on the disputed entry by local authorities.",
      },
    ],
    linkedStatutes: [
      "Punjab Land Revenue Act, 1967",
      "West Pakistan Land Revenue Rules (placeholder)",
    ],
    precedents: ["2020 PLJ Revenue 55", "2024 CLC 901"],
    linkedDocumentIds: ["doc-011", "doc-012"],
    timelineIds: ["tl-012", "tl-013"],
    researchNoteIds: ["rn-007"],
    draftArtifacts: [
      {
        id: "draft-007",
        title: "Revenue Revision Petition",
        type: "Application",
        status: "Reviewing",
        updatedAt: "2026-04-19",
        owner: "Umair Hafeez",
        summary:
          "Refined notice and locus grounds with clearer revenue record references.",
      },
    ],
    riskFlags: [
      "Genealogy chart not yet attached",
      "Private respondent service addresses require reconfirmation",
    ],
    proceduralAlerts: [
      "Verify certified copies of impugned orders",
      "Prepare annexure index for mutation record bundle",
    ],
    tags: ["Mutation", "Notice", "Revenue Revision"],
  },
  {
    id: "raza-foods-civil",
    title: "M/s Raza Foods (Pvt.) Ltd. v. National Logistics Cell",
    caseNumber: "Civil Suit No. 438/2025",
    forum: "Civil Judge Karachi East",
    matterType: "Civil Suit",
    status: "Active",
    priority: "Low",
    stage: "Written statement on record; issues yet to be framed",
    client: "M/s Raza Foods (Pvt.) Ltd.",
    opposingParty: "National Logistics Cell",
    nextHearingDate: "2026-05-14",
    assignedCounsel: ["Dania Rahim"],
    teamAgents: ["Manager Agent", "Memory Agent"],
    summary:
      "Recovery and damages claim arising from delayed transport of temperature-sensitive food inventory. The matter is less urgent but document-heavy, making it a useful baseline for document indexing and issue tracking.",
    issues: [
      "Contractual limitation of liability",
      "Proof of consequential losses",
      "Admissibility of internal spoilage assessments",
    ],
    reliefSought: [
      "Recovery of principal loss and damages",
      "Markup and litigation costs",
    ],
    importantNotes: [
      "This file is a strong candidate for document automation demos because the record is already organized.",
      "Opposing side likely to rely on exclusion clauses in transport agreement.",
    ],
    factsBackground: [
      {
        label: "Commercial Arrangement",
        text: "NLC was engaged to transport refrigerated stock between Karachi and Lahore warehouses under a recurring service arrangement.",
      },
      {
        label: "Loss Event",
        text: "Client alleges delivery delays and failure to maintain required temperature conditions, resulting in spoilage.",
      },
      {
        label: "Proof Theme",
        text: "Success depends on linking logistics records, warehouse reports, and expert opinion on spoilage.",
      },
    ],
    linkedStatutes: [
      "Contract Act, 1872",
      "Qanun-e-Shahadat Order, 1984",
      "Sale of Goods Act, 1930",
    ],
    precedents: ["2018 CLC 233", "2022 CLD 1044"],
    linkedDocumentIds: ["doc-013", "doc-014"],
    timelineIds: ["tl-014", "tl-015"],
    researchNoteIds: ["rn-008"],
    draftArtifacts: [
      {
        id: "draft-008",
        title: "Issues Proposed by Plaintiff",
        type: "Brief",
        status: "Drafting",
        updatedAt: "2026-04-16",
        owner: "Dania Rahim",
        summary:
          "Issue list structured around breach, causation, damages, and exclusion clauses.",
      },
    ],
    riskFlags: ["Independent expert opinion not yet commissioned"],
    proceduralAlerts: [
      "Prepare proposed issues ahead of framing stage",
      "Review warehouse log admissibility objections",
    ],
    tags: ["Recovery", "Damages", "Evidence"],
  },
];

export function getCaseById(id: string) {
  return cases.find((caseItem) => caseItem.id === id);
}
