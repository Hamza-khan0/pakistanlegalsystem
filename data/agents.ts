import type { AgentDefinition, AgentOutput, WorkflowStep, WorkspaceRun } from "@/types";

export const agents: AgentDefinition[] = [
  {
    id: "manager-agent",
    name: "Manager Agent",
    role: "Matter orchestrator",
    description:
      "Breaks user instructions into legal tasks, assigns work to specialist agents, and keeps the matter strategy aligned with deadlines.",
    status: "Ready",
    lastRun: "2026-04-20 14:18",
    specialties: ["Task decomposition", "Matter routing", "Priority control"],
    queueDepth: 3,
    confidence: "92%",
  },
  {
    id: "research-agent",
    name: "Research Agent",
    role: "Authority and issue mining",
    description:
      "Locates Pakistani legal authorities, surfaces maintainability questions, and assembles structured issue notes.",
    status: "Reviewing",
    lastRun: "2026-04-20 13:54",
    specialties: ["Precedent retrieval", "Statutory mapping", "Issue framing"],
    queueDepth: 5,
    confidence: "88%",
  },
  {
    id: "drafting-agent",
    name: "Drafting Agent",
    role: "Pleading and note generation",
    description:
      "Produces petitions, objections, hearing notes, and filing-ready first drafts from structured matter context.",
    status: "Ready",
    lastRun: "2026-04-20 14:06",
    specialties: ["Pleadings", "Interim relief", "Bench notes"],
    queueDepth: 4,
    confidence: "90%",
  },
  {
    id: "critic-agent",
    name: "Critic Agent",
    role: "Adversarial review",
    description:
      "Tests draft positions against maintainability gaps, evidentiary weak points, and likely arguments from the other side.",
    status: "Queued",
    lastRun: "2026-04-20 12:42",
    specialties: ["Risk review", "Counter-arguments", "Draft stress tests"],
    queueDepth: 2,
    confidence: "85%",
  },
  {
    id: "procedural-agent",
    name: "Procedural Agent",
    role: "Court process control",
    description:
      "Tracks filing stage, procedural compliance, hearing preparation, and matter-specific court reminders.",
    status: "Ready",
    lastRun: "2026-04-20 11:58",
    specialties: ["Filing checklists", "Court timelines", "Procedural gaps"],
    queueDepth: 3,
    confidence: "94%",
  },
  {
    id: "memory-agent",
    name: "Memory Agent",
    role: "Matter memory and cross-file recall",
    description:
      "Maintains structured matter memory, reuses prior reasoning, and keeps important factual context persistent across sessions.",
    status: "Ready",
    lastRun: "2026-04-20 11:32",
    specialties: ["Case memory", "Cross-matter recall", "Knowledge grounding"],
    queueDepth: 1,
    confidence: "89%",
  },
];

export const agentOutputs: AgentOutput[] = [
  {
    id: "ao-001",
    caseId: "green-valley-dha",
    agentId: "research-agent",
    title: "Maintainability note on allotment cancellation challenge",
    generatedAt: "2026-04-20 10:46",
    confidence: "High",
    status: "Published",
    summary:
      "Supports injunction strategy by framing cancellation as void action with immediate commercial prejudice.",
    citations: ["2021 CLC 1188", "PLD 2018 Lahore 412"],
    nextAction: "Add one authority on absence of efficacious alternate remedy.",
  },
  {
    id: "ao-002",
    caseId: "green-valley-dha",
    agentId: "critic-agent",
    title: "Gap review before motion hearing",
    generatedAt: "2026-04-20 11:20",
    confidence: "Medium",
    status: "Needs Review",
    summary:
      "Flags missing sanctioned site map and warns against overstating possession unless annexure support is complete.",
    citations: ["Specific Relief Act, 1877"],
    nextAction: "Obtain map or soften factual possession claim.",
  },
  {
    id: "ao-003",
    caseId: "horizon-customs-petition",
    agentId: "drafting-agent",
    title: "Draft petition skeleton with prayer clauses",
    generatedAt: "2026-04-20 13:08",
    confidence: "High",
    status: "Published",
    summary:
      "Delivers filing-ready petition skeleton with maintainability and urgency sections organized for partner markup.",
    citations: ["Constitution of Pakistan, Article 199", "2023 PTD 1442"],
    nextAction: "Verify invoice endorsements before final filing print.",
  },
  {
    id: "ao-004",
    caseId: "mehr-un-nisa-service",
    agentId: "procedural-agent",
    title: "Condonation checklist",
    generatedAt: "2026-04-17 16:42",
    confidence: "Medium",
    status: "Published",
    summary:
      "Checklist sequences representation exhibits, limitation explanation, and service record annexures.",
    citations: ["Punjab Service Tribunals Act, 1974"],
    nextAction: "Cross-check all representation dates against originals.",
  },
];

export const workflowSteps: WorkflowStep[] = [
  {
    id: "wf-001",
    title: "User request",
    detail: "Lawyer issues a chamber instruction against the active matter context.",
  },
  {
    id: "wf-002",
    title: "Manager Agent",
    detail: "Splits the task into research, drafting, and procedural sub-workstreams.",
  },
  {
    id: "wf-003",
    title: "Research Agent",
    detail: "Surfaces statutes, precedents, and maintainability questions from Pakistani legal material.",
  },
  {
    id: "wf-004",
    title: "Drafting Agent",
    detail: "Produces structured first draft or hearing note using matter memory and research outputs.",
  },
  {
    id: "wf-005",
    title: "Critic Agent",
    detail: "Pressure-tests the result for gaps, weak authorities, and likely objections.",
  },
  {
    id: "wf-006",
    title: "Final Output",
    detail: "Lawyer receives a reviewed work product with cited material and next actions.",
  },
];

export const workspaceRuns: WorkspaceRun[] = [
  {
    id: "wr-001",
    prompt: "Draft preliminary objections in this matter",
    createdAt: "2026-04-20 14:10",
    decomposition: [
      "Identify threshold objections from forum, limitation, and maintainability record.",
      "Review pleadings for documentary gaps and alternate remedy hooks.",
      "Prepare objection headings and concise supporting grounds.",
    ],
    citedMaterials: [
      "PLD 2018 Lahore 412",
      "Specific Relief Act, 1877",
      "Internal allotment cancellation chronology",
    ],
    flaggedIssues: [
      "Missing sanctioned site map weakens a possession-heavy objection.",
      "Jurisdiction objection should not contradict the alternate remedy stance.",
    ],
    outputs: [
      {
        agent: "Manager Agent",
        role: "Orchestration",
        tone: "analysis",
        title: "Task split completed",
        summary:
          "The request was routed as a threshold-objection workflow with research, draft, and adversarial review lanes.",
        bullets: [
          "Maintains consistency between maintainability and jurisdiction objections.",
          "Marked annexure deficiencies for the critic pass.",
        ],
        citations: ["Matter chronology", "Current pleadings set"],
      },
      {
        agent: "Research Agent",
        role: "Authority scan",
        tone: "analysis",
        title: "Objection themes surfaced",
        summary:
          "Most viable objections are maintainability, efficacious alternate remedy, and absence of complete documentary basis for urgent civil intervention.",
        bullets: [
          "Frame alternate remedy as presently available and unexhausted.",
          "Use possession ambiguity only as a supporting inconsistency, not the lead objection.",
        ],
        citations: ["PLD 2018 Lahore 412", "2021 CLC 1188"],
      },
      {
        agent: "Drafting Agent",
        role: "Draft generation",
        tone: "draft",
        title: "Preliminary objections drafted",
        summary:
          "Prepared four objection headings with short legal grounds and documentary references aligned to the file.",
        bullets: [
          "Objection on maintainability and internal remedy.",
          "Objection on suppression of complete payment and site documentation.",
          "Objection on failure to establish prima facie irreparable loss.",
        ],
        citations: ["Specific Relief Act, 1877"],
      },
      {
        agent: "Critic Agent",
        role: "Stress test",
        tone: "critical",
        title: "Draft tempered for credibility",
        summary:
          "Recommended softening the objection on possession and strengthening the alternate-remedy narrative to avoid overreach.",
        bullets: [
          "Do not assert facts not squarely supported by annexures.",
          "Keep tone formal and threshold-focused rather than argumentative on merits.",
        ],
        citations: ["Internal annexure audit"],
      },
    ],
    finalSummary:
      "A filing-style set of preliminary objections is ready for lawyer review, with the strongest weight on maintainability and alternate remedy.",
  },
  {
    id: "wr-002",
    prompt: "Summarize the factual controversy",
    createdAt: "2026-04-20 13:36",
    decomposition: [
      "Extract the factual chronology from pleadings and key annexures.",
      "Separate admitted background from disputed allegations.",
      "Produce a neutral controversy note for counsel prep.",
    ],
    citedMaterials: [
      "Cancellation letter dated 09.04.2026",
      "Payment schedule and receipts bundle",
      "Urgency instruction note",
    ],
    flaggedIssues: [
      "Possession position remains partly inferential.",
      "Administrative surcharge dispute should be explained in plain language.",
    ],
    outputs: [
      {
        agent: "Manager Agent",
        role: "Matter framing",
        tone: "analysis",
        title: "Controversy framing",
        summary:
          "The matter was framed as a dispute over allotment cancellation after substantial compliance and contested surcharge demands.",
        bullets: [
          "Separated contractual/payment background from urgent injunctive posture.",
          "Marked what is admitted versus what remains contested.",
        ],
        citations: ["Matter summary"],
      },
      {
        agent: "Memory Agent",
        role: "Matter memory",
        tone: "analysis",
        title: "Chronology recalled",
        summary:
          "Compiled the payment, surcharge objection, and cancellation sequence into a concise working narrative for future prompts.",
        bullets: [
          "Captures the client's investment and development expectations.",
          "Keeps the threatened third-party transfer as the key urgency trigger.",
        ],
        citations: ["Payment receipts", "Cancellation letter"],
      },
      {
        agent: "Drafting Agent",
        role: "Structured output",
        tone: "draft",
        title: "Factual controversy note",
        summary:
          "Prepared a neutral note describing the allotment, disputed surcharge, unilateral cancellation, and threatened alienation risk.",
        bullets: [
          "Useful for hearing prep, client updates, and petition summary sections.",
          "Keeps argumentative language out of the fact statement.",
        ],
        citations: ["Pleadings draft"],
      },
    ],
    finalSummary:
      "The factual controversy is now reduced to a neutral chronology that can feed petitions, hearings, and research tasks.",
  },
];
