from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import delete, select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.agent_log import AgentRunLog
from app.models.case import Case
from app.models.case_prediction import CasePrediction
from app.models.chamber_run import ChamberRun
from app.models.chamber_run_step import ChamberRunStep
from app.models.corpus_entry import CorpusEntry
from app.models.crawl_job import CrawlJob
from app.models.crawl_source import CrawlSource
from app.models.crawled_document import CrawledDocument
from app.models.document import Document
from app.models.draft import Draft
from app.models.enums import (
    AgentRunStatus,
    CaseStatus,
    ChamberRunStatus,
    ChamberRunStepStatus,
    ChamberTaskType,
    DocumentStatus,
    DocumentType,
    DraftStatus,
    ExtractionStatus,
    GroundingUsageType,
    IntelligenceArtifactType,
    IntelligenceStatus,
    NoteType,
    OcrStatus,
    ParsingStatus,
    PriorityLevel,
    ResearchStatus,
    TimelineEventType,
)
from app.models.grounding_link import GroundingLink
from app.models.intelligence_artifact import IntelligenceArtifact
from app.models.legal_source import LegalSource
from app.models.legal_source_chunk import LegalSourceChunk
from app.models.ml_dataset import MlDataset
from app.models.ml_model import MlModel
from app.models.note import Note
from app.models.research import ResearchEntry
from app.models.research_run import ResearchRun
from app.models.timeline import TimelineEvent
from app.seed.register_crawl_sources import ensure_demo_assets
from app.services.corpus import build_corpus_entries
from app.services.crawling.registry import register_seed_crawl_sources
from app.services.knowledge.ingestion import ingest_seed_legal_sources


def write_placeholder_file(case_id: str, filename: str, content: str) -> str:
    uploads_dir = Path(settings.uploads_dir) / case_id
    uploads_dir.mkdir(parents=True, exist_ok=True)
    destination = uploads_dir / filename
    destination.write_text(content, encoding="utf-8")
    return str(destination)


def first_chunk_id(db, source_id: str) -> str | None:
    return db.scalar(
        select(LegalSourceChunk.id)
        .where(LegalSourceChunk.source_id == source_id)
        .order_by(LegalSourceChunk.chunk_index)
    )


def reset_database(db) -> None:
    db.execute(delete(CasePrediction))
    db.execute(delete(MlModel))
    db.execute(delete(MlDataset))
    db.execute(delete(CorpusEntry))
    db.execute(delete(CrawledDocument))
    db.execute(delete(CrawlJob))
    db.execute(delete(CrawlSource))
    db.execute(delete(GroundingLink))
    db.execute(delete(ChamberRunStep))
    db.execute(delete(ChamberRun))
    db.execute(delete(IntelligenceArtifact))
    db.execute(delete(AgentRunLog))
    db.execute(delete(Draft))
    db.execute(delete(ResearchRun))
    db.execute(delete(ResearchEntry))
    db.execute(delete(Note))
    db.execute(delete(TimelineEvent))
    db.execute(delete(Document))
    db.execute(delete(Case))
    db.execute(delete(LegalSourceChunk))
    db.execute(delete(LegalSource))
    db.commit()


def seed() -> None:
    session = SessionLocal()
    now = datetime.now(timezone.utc)

    try:
        reset_database(session)
        ensure_demo_assets()
        register_seed_crawl_sources(session)
        ingest_seed_legal_sources(session, reset_existing=True)
        build_corpus_entries(session, include_seeded=True, include_crawled=False)

        green_valley = Case(
            id="green-valley-dha",
            title="M/s Green Valley Estate Pvt. Ltd. v. Defence Housing Authority, Lahore",
            case_number="Civil Suit No. 102/2026",
            forum="Lahore High Court, Lahore",
            matter_type="Property Dispute",
            status=CaseStatus.HEARING_DUE,
            priority=PriorityLevel.CRITICAL,
            client_name="M/s Green Valley Estate Pvt. Ltd.",
            opposing_party="Defence Housing Authority, Lahore",
            summary="The client challenges unilateral cancellation of a commercial allotment after substantial payments and partial possession. The current focus is preserving the plot through interim injunction before threatened third-party transfer.",
            legal_issues=[
                "Validity of cancellation without speaking order",
                "Maintainability despite internal DHA remedies",
                "Threshold for urgent interim protection",
            ],
            relief_sought=[
                "Declaration that cancellation letter is void",
                "Permanent injunction against alienation",
                "Interim stay against coercive dispossession",
            ],
            next_hearing_date=date(2026, 4, 24),
            assigned_counsel=["Ahsan Qureshi", "Sara Nadeem"],
            filing_stage="Interim injunction pending before motion bench",
            risk_flags=[
                "Sanctioned site map not uploaded",
                "Internal appeal record incomplete",
                "Jurisdiction objection likely",
            ],
            important_notes=[
                "Court wants a tighter chronology on payments and surcharge dispute.",
                "Urgency framing should foreground alienation risk.",
            ],
            facts_background=[
                {
                    "label": "Allotment",
                    "text": "Commercial plot was allotted in 2021 after premium payment and an approved installment schedule.",
                },
                {
                    "label": "Dispute Trigger",
                    "text": "Cancellation followed the client's objection to an administrative surcharge and request for demarcation correction.",
                },
            ],
            linked_statutes=[
                "Specific Relief Act, 1877",
                "Transfer of Property Act, 1882",
            ],
            precedents=["2021 CLC 1188", "PLD 2018 Lahore 412"],
            procedural_alerts=[
                "Prepare urgency note before 10:00 AM filing cut-off",
                "Verify vakalatnama against latest authorization letter",
            ],
            tags=["Injunction", "Commercial Plot", "Maintainability"],
        )

        customs_petition = Case(
            id="horizon-customs-petition",
            title="M/s Horizon Textiles v. Federation of Pakistan",
            case_number="C.P. No. D-1182/2026",
            forum="Sindh High Court, Karachi",
            matter_type="Constitutional Petition",
            status=CaseStatus.DRAFTING,
            priority=PriorityLevel.HIGH,
            client_name="M/s Horizon Textiles",
            opposing_party="Federation of Pakistan through FBR and Collectorate of Customs",
            summary="Petition challenges detention and enhanced valuation of textile inputs despite prior clearance practice. The immediate aim is to secure release and frame the matter as jurisdictional overreach plus denial of hearing.",
            legal_issues=[
                "Jurisdictional limits on provisional valuation enhancement",
                "Violation of audi alteram partem",
                "Maintainability despite alternate remedy",
            ],
            relief_sought=[
                "Declaration against unlawful detention and valuation letter",
                "Release of consignment against secured terms",
                "Restraint against coercive recovery",
            ],
            next_hearing_date=date(2026, 4, 30),
            assigned_counsel=["Hira Kamal", "Usman Tariq"],
            filing_stage="Petition and stay application under final partner review",
            risk_flags=[
                "Two invoices still missing customs endorsement",
                "Alternate remedy objection likely at threshold",
            ],
            important_notes=[
                "Annexure index must align every invoice with the valuation matrix.",
                "Bench is likely to ask about alternate remedy first.",
            ],
            facts_background=[
                {
                    "label": "Commercial Context",
                    "text": "Detained consignment is affecting production commitments and export schedules.",
                },
                {
                    "label": "Administrative Action",
                    "text": "Collectorate withheld release and issued a valuation departure note without hearing.",
                },
            ],
            linked_statutes=[
                "Constitution of the Islamic Republic of Pakistan, 1973",
                "Customs Act, 1969",
            ],
            precedents=["PLD 2020 Sindh 221", "2023 PTD 1442"],
            procedural_alerts=[
                "Finalize synopsis and list of dates",
                "Check annexure pagination before filing set is printed",
            ],
            tags=["Article 199", "Customs", "Urgent Release"],
        )

        service_appeal = Case(
            id="mehr-un-nisa-service",
            title="Mehr-un-Nisa v. Punjab Education Department",
            case_number="Service Appeal No. 18/2026",
            forum="Punjab Service Tribunal, Lahore",
            matter_type="Service Matter",
            status=CaseStatus.RESEARCH,
            priority=PriorityLevel.MEDIUM,
            client_name="Mehr-un-Nisa",
            opposing_party="Punjab Education Department",
            summary="Service appeal challenges non-promotion despite seniority and favorable departmental recommendations. Limitation and continuing cause remain the key research questions.",
            legal_issues=[
                "Limitation and continuing cause in service appeal",
                "Evidentiary value of departmental recommendations",
                "Scope of relief where promotion slots are filled",
            ],
            relief_sought=[
                "Setting aside impugned non-promotion order",
                "Direction for reconsideration with due seniority benefits",
            ],
            next_hearing_date=date(2026, 5, 5),
            assigned_counsel=["Faraz Latif"],
            filing_stage="Condonation and maintainability research underway",
            risk_flags=[
                "Final promotion board minutes absent",
                "Representation dates need documentary support",
            ],
            important_notes=[
                "Service record is favorable but communication record is patchy.",
                "Continuing cause argument depends on representations being documented.",
            ],
            facts_background=[
                {
                    "label": "Career Progression",
                    "text": "Appellant claims supersession by juniors after eighteen years of service.",
                },
                {
                    "label": "Limitation Sensitivity",
                    "text": "Delay explanation depends on repeated representations and absence of speaking response.",
                },
            ],
            linked_statutes=[
                "Punjab Service Tribunals Act, 1974",
                "Punjab Civil Servants Act, 1974",
            ],
            precedents=["2019 PLC(CS) 877", "2021 SCMR 455"],
            procedural_alerts=[
                "Obtain departmental forwarding letter",
                "Confirm service book extracts before final appeal memo",
            ],
            tags=["Promotion", "Limitation", "Continuing Cause"],
        )

        revenue_revision = Case(
            id="al-habib-revenue",
            title="Al-Habib Developers v. Board of Revenue, Punjab",
            case_number="Revenue Revision No. 77/2026",
            forum="Board of Revenue, Punjab",
            matter_type="Revenue Matter",
            status=CaseStatus.AWAITING_FILING,
            priority=PriorityLevel.MEDIUM,
            client_name="Al-Habib Developers",
            opposing_party="Board of Revenue, Punjab and private respondents",
            summary="Revenue revision challenges mutation entries and remand proceedings affecting a peri-urban land parcel earmarked for development. Current work is focused on notice defects and lineage clarity.",
            legal_issues=[
                "Legality of mutation sanctioned without complete notice",
                "Scope of revision against concurrent adverse findings",
                "Treatment of possession narrative in revision",
            ],
            relief_sought=[
                "Setting aside impugned mutation and appellate orders",
                "Fresh decision after lawful notice and record scrutiny",
            ],
            next_hearing_date=date(2026, 5, 8),
            assigned_counsel=["Umair Hafeez", "Rida Ameen"],
            filing_stage="Revision petition and annexure set being finalized",
            risk_flags=[
                "Genealogy chart not yet attached",
                "Service addresses require reconfirmation",
            ],
            important_notes=[
                "Counsel wants a genealogy diagram for the brief.",
            ],
            facts_background=[
                {
                    "label": "Land Record History",
                    "text": "Dispute concerns competing inheritance and sale claims over contiguous khasra numbers.",
                },
                {
                    "label": "Procedural Defect",
                    "text": "Client alleges notice did not effectively reach all interested parties before mutation sanction.",
                },
            ],
            linked_statutes=["Punjab Land Revenue Act, 1967"],
            precedents=["2020 PLJ Revenue 55", "2024 CLC 901"],
            procedural_alerts=[
                "Verify certified copies of impugned orders",
                "Prepare annexure index for mutation record bundle",
            ],
            tags=["Mutation", "Notice", "Revenue Revision"],
        )

        session.add_all([green_valley, customs_petition, service_appeal, revenue_revision])
        session.flush()

        documents = [
            Document(
                id="doc-001",
                case_id=green_valley.id,
                name="Plaint with Interim Injunction Application",
                document_type=DocumentType.PLAINT,
                status=DocumentStatus.UNDER_REVIEW,
                category="Primary Pleadings",
                file_name="plaint-injunction-application.txt",
                file_path=write_placeholder_file(
                    green_valley.id,
                    "plaint-injunction-application.txt",
                    "The plaintiff respectfully submits that the impugned cancellation letter was issued without lawful authority...",
                ),
                mime_type="text/plain",
                tags=["Urgent", "Injunction", "Maintainability"],
                extraction_status=ExtractionStatus.PARSED,
                ocr_status=OcrStatus.COMPLETED,
                parsing_status=ParsingStatus.COMPLETED,
                intelligence_status=IntelligenceStatus.PROCESSED,
                extracted_text_preview="The plaintiff respectfully submits that the impugned cancellation letter was issued without lawful authority...",
                extracted_text="The plaintiff respectfully submits that the impugned cancellation letter was issued without lawful authority and without a speaking order. The plaintiff has already paid substantial consideration and seeks urgent interim protection against dispossession and third-party transfer.",
                extraction_error="",
                processed_at=now,
                summary="Main plaint and interim application challenging the allotment cancellation.",
                filed_by="Sara Nadeem",
                pages=22,
                metadata_json={"pagesDetected": 22, "parser": "phase-2-placeholder"},
            ),
            Document(
                id="doc-002",
                case_id=green_valley.id,
                name="Payment Schedule and Receipts Bundle",
                document_type=DocumentType.ANNEXURE,
                status=DocumentStatus.REFERENCE,
                category="Annexures",
                file_name="payment-receipts-bundle.txt",
                file_path=write_placeholder_file(
                    green_valley.id,
                    "payment-receipts-bundle.txt",
                    "Installment receipts, estate branch endorsements, and remittance record.",
                ),
                mime_type="text/plain",
                tags=["Receipts", "Payments", "Annexure-A"],
                extraction_status=ExtractionStatus.READY_FOR_INDEXING,
                ocr_status=OcrStatus.COMPLETED,
                parsing_status=ParsingStatus.COMPLETED,
                intelligence_status=IntelligenceStatus.NOT_PROCESSED,
                extracted_text_preview="Bundle includes premium payment acknowledgment and installment ledger...",
                extracted_text="",
                extraction_error="",
                processed_at=None,
                summary="Receipts, estate branch endorsements, and bank remittance record.",
                filed_by="Case Team Upload",
                pages=31,
                metadata_json={"pagesDetected": 31},
            ),
            Document(
                id="doc-003",
                case_id=customs_petition.id,
                name="Constitutional Petition Draft",
                document_type=DocumentType.PLAINT,
                status=DocumentStatus.UNDER_REVIEW,
                category="Primary Pleadings",
                file_name="constitutional-petition-draft.txt",
                file_path=write_placeholder_file(
                    customs_petition.id,
                    "constitutional-petition-draft.txt",
                    "The petitioner company seeks constitutional relief against unlawful detention of imported textile inputs...",
                ),
                mime_type="text/plain",
                tags=["Article 199", "Customs", "Urgent"],
                extraction_status=ExtractionStatus.PARSED,
                ocr_status=OcrStatus.COMPLETED,
                parsing_status=ParsingStatus.COMPLETED,
                intelligence_status=IntelligenceStatus.PROCESSED,
                extracted_text_preview="The petitioner company seeks constitutional relief against unlawful detention...",
                extracted_text="The petitioner company seeks constitutional relief against unlawful detention of imported textile inputs and challenges the valuation departure note on grounds of denial of hearing, jurisdictional overreach, and immediate commercial prejudice.",
                extraction_error="",
                processed_at=now,
                summary="Main petition challenging detention and valuation enhancement.",
                filed_by="Drafting Agent",
                pages=28,
                metadata_json={"pagesDetected": 28},
            ),
            Document(
                id="doc-004",
                case_id=customs_petition.id,
                name="Valuation Matrix and Invoice Bundle",
                document_type=DocumentType.ANNEXURE,
                status=DocumentStatus.REFERENCE,
                category="Trade Record",
                file_name="valuation-matrix.txt",
                file_path=write_placeholder_file(
                    customs_petition.id,
                    "valuation-matrix.txt",
                    "Comparative matrix shows variance between prior cleared consignments and the impugned provisional enhancement...",
                ),
                mime_type="text/plain",
                tags=["Invoices", "Valuation", "Annexure-C"],
                extraction_status=ExtractionStatus.OCR_RUNNING,
                ocr_status=OcrStatus.QUEUED,
                parsing_status=ParsingStatus.IN_PROGRESS,
                intelligence_status=IntelligenceStatus.PROCESSING,
                extracted_text_preview="Comparative matrix shows variance between prior cleared consignments...",
                extracted_text="",
                extraction_error="",
                processed_at=None,
                summary="Invoice history, prior assessment record, and valuation comparison sheet.",
                filed_by="Trade Documentation Desk",
                pages=46,
                metadata_json={"pagesDetected": 46},
            ),
            Document(
                id="doc-005",
                case_id=service_appeal.id,
                name="Service Appeal Memo",
                document_type=DocumentType.APPLICATION,
                status=DocumentStatus.DRAFT,
                category="Appeal Papers",
                file_name="service-appeal-memo.txt",
                file_path=write_placeholder_file(
                    service_appeal.id,
                    "service-appeal-memo.txt",
                    "The appellant was repeatedly superseded despite seniority, clean service record, and favorable departmental recommendation...",
                ),
                mime_type="text/plain",
                tags=["Promotion", "Service Appeal"],
                extraction_status=ExtractionStatus.PARSED,
                ocr_status=OcrStatus.COMPLETED,
                parsing_status=ParsingStatus.COMPLETED,
                intelligence_status=IntelligenceStatus.PROCESSED,
                extracted_text_preview="The appellant was repeatedly superseded despite seniority...",
                extracted_text="The appellant was repeatedly superseded despite seniority, a clean service record, and favorable departmental recommendations. The appeal requires careful treatment of limitation and the continuing cause argument.",
                extraction_error="",
                processed_at=now,
                summary="Appeal memo challenging supersession and non-promotion.",
                filed_by="Faraz Latif",
                pages=17,
                metadata_json={"pagesDetected": 17},
            ),
            Document(
                id="doc-006",
                case_id=revenue_revision.id,
                name="Revenue Revision Petition",
                document_type=DocumentType.APPLICATION,
                status=DocumentStatus.UNDER_REVIEW,
                category="Revision Papers",
                file_name="revenue-revision-petition.txt",
                file_path=write_placeholder_file(
                    revenue_revision.id,
                    "revenue-revision-petition.txt",
                    "The impugned mutation proceedings suffer from defective notice and incomplete scrutiny of lineage record...",
                ),
                mime_type="text/plain",
                tags=["Mutation", "Revision", "Notice"],
                extraction_status=ExtractionStatus.PARSED,
                ocr_status=OcrStatus.COMPLETED,
                parsing_status=ParsingStatus.COMPLETED,
                intelligence_status=IntelligenceStatus.PROCESSED,
                extracted_text_preview="The impugned mutation proceedings suffer from defective notice...",
                extracted_text="The impugned mutation proceedings suffer from defective notice and incomplete scrutiny of lineage record. The revision petition seeks fresh determination after lawful notice and fuller revenue record review.",
                extraction_error="",
                processed_at=now,
                summary="Revision petition targeting mutation proceedings and appellate orders.",
                filed_by="Umair Hafeez",
                pages=18,
                metadata_json={"pagesDetected": 18},
            ),
        ]

        session.add_all(documents)

        timeline_events = [
            TimelineEvent(
                id="tl-001",
                case_id=green_valley.id,
                title="Cancellation letter issued",
                event_type=TimelineEventType.ORDER,
                description="DHA estate branch issued the impugned cancellation communication.",
                actor="Opposing Authority",
                event_date=date(2026, 4, 9),
            ),
            TimelineEvent(
                id="tl-002",
                case_id=green_valley.id,
                title="Urgency note requested",
                event_type=TimelineEventType.RESEARCH,
                description="Lead counsel asked for a one-page urgency note ahead of motion hearing.",
                actor="Ahsan Qureshi",
                event_date=date(2026, 4, 19),
            ),
            TimelineEvent(
                id="tl-003",
                case_id=customs_petition.id,
                title="Consignment detained",
                event_type=TimelineEventType.ORDER,
                description="Customs held release pending revised valuation assessment.",
                actor="Collectorate of Customs",
                event_date=date(2026, 4, 11),
            ),
            TimelineEvent(
                id="tl-004",
                case_id=service_appeal.id,
                title="Condonation research updated",
                event_type=TimelineEventType.RESEARCH,
                description="Procedural position refined around repeated representations and continuing cause.",
                actor="Procedural Agent",
                event_date=date(2026, 4, 17),
            ),
            TimelineEvent(
                id="tl-005",
                case_id=revenue_revision.id,
                title="Revision petition revised",
                event_type=TimelineEventType.DRAFT,
                description="Grounds on defective notice and locus sharpened after partner comments.",
                actor="Umair Hafeez",
                event_date=date(2026, 4, 19),
            ),
        ]
        session.add_all(timeline_events)

        notes = [
            Note(
                id="note-001",
                case_id=green_valley.id,
                title="Hearing posture note",
                content="Lead with immediate alienation risk and avoid overstatement on possession until the site map is on file.",
                note_type=NoteType.HEARING,
                author="Sara Nadeem",
            ),
            Note(
                id="note-002",
                case_id=customs_petition.id,
                title="Partner review reminder",
                content="Keep the alternate remedy exception tightly framed around denial of hearing and production impact.",
                note_type=NoteType.STRATEGY,
                author="Hira Kamal",
            ),
            Note(
                id="note-003",
                case_id=service_appeal.id,
                title="Client communication",
                content="Need the client to confirm all representation dates before we lock the condonation plea.",
                note_type=NoteType.CLIENT,
                author="Faraz Latif",
            ),
        ]
        session.add_all(notes)

        research_entries = [
            ResearchEntry(
                id="research-001",
                case_id=green_valley.id,
                title="Maintainability exceptions despite internal remedy",
                query="Maintainability of civil action against allotment cancellation despite internal DHA remedy",
                summary="Authorities support intervention where cancellation is alleged to be void on its face and accompanied by threatened third-party transfer.",
                citations=["PLD 2018 Lahore 412", "2021 CLC 1188"],
                source_type="Pakistani Case Law",
                status=ResearchStatus.VERIFIED,
                author="Research Agent",
                next_question="Need one more authority distinguishing contractual remedy from public law taint in allotment matters.",
            ),
            ResearchEntry(
                id="research-002",
                case_id=customs_petition.id,
                title="Alternate remedy exceptions in customs petition",
                query="Article 199 maintainability in customs valuation detention challenge",
                summary="Constitutional jurisdiction remains arguable where detention is coupled with denial of hearing and immediate commercial injury.",
                citations=["PLD 2020 Sindh 221", "2023 PTD 1442"],
                source_type="Pakistani Case Law",
                status=ResearchStatus.VERIFIED,
                author="Research Agent",
                next_question="Need one supporting authority on release against security in valuation disputes.",
            ),
            ResearchEntry(
                id="research-003",
                case_id=service_appeal.id,
                title="Condonation landscape in service appeal",
                query="Continuing cause and condonation in service appeal",
                summary="Delay can be argued through continuing cause if representation record is specifically pleaded and tied to absence of speaking order.",
                citations=["2019 PLC(CS) 877", "2021 SCMR 455"],
                source_type="Pakistani Case Law",
                status=ResearchStatus.FRESH,
                author="Procedural Agent",
                next_question="Cross-check representation dates against originals before final draft.",
            ),
        ]
        session.add_all(research_entries)

        drafts = [
            Draft(
                id="draft-001",
                case_id=green_valley.id,
                title="Interim Injunction Application",
                draft_type="Application",
                status=DraftStatus.REVIEWING,
                content="Updated application foregrounding possession risk and payment chronology...",
                version=3,
                owner="Drafting Agent",
                summary="Updated to foreground possession risk and attach payment schedule annexures.",
            ),
            Draft(
                id="draft-002",
                case_id=customs_petition.id,
                title="Constitutional Petition",
                draft_type="Petition",
                status=DraftStatus.REVIEWING,
                content="Reworked maintainability section to anchor exceptions to alternate remedy...",
                version=4,
                owner="Drafting Agent",
                summary="Petition draft refined for partner markup and filing preparation.",
            ),
            Draft(
                id="draft-003",
                case_id=service_appeal.id,
                title="Condonation Application",
                draft_type="Application",
                status=DraftStatus.DRAFTING,
                content="Organizes delay explanation around repeated departmental representations...",
                version=2,
                owner="Procedural Agent",
                summary="Delay explanation built around repeated representations and continuing cause.",
            ),
            Draft(
                id="draft-004",
                case_id=revenue_revision.id,
                title="Revenue Revision Petition",
                draft_type="Revision",
                status=DraftStatus.REVIEWING,
                content="Grounds on defective notice and locus sharpened after partner comments...",
                version=2,
                owner="Umair Hafeez",
                summary="Notice and locus grounds refined with clearer revenue record references.",
            ),
        ]
        session.add_all(drafts)

        agent_logs = [
            AgentRunLog(
                id="agent-001",
                case_id=green_valley.id,
                agent_name="Research Agent",
                title="Maintainability note on allotment cancellation challenge",
                task_type="Legal research",
                input_summary="Assess maintainability and injunction framing in allotment cancellation challenge.",
                output_summary="Supports injunction strategy by framing cancellation as void action with immediate commercial prejudice.",
                status=AgentRunStatus.COMPLETED,
                confidence_score=0.91,
                citations=["PLD 2018 Lahore 412", "2021 CLC 1188"],
                next_action="Add one authority on absence of efficacious alternate remedy.",
                started_at=now,
                completed_at=now,
                metadata_json={"lane": "research"},
            ),
            AgentRunLog(
                id="agent-002",
                case_id=green_valley.id,
                agent_name="Critic Agent",
                title="Gap review before motion hearing",
                task_type="Adversarial review",
                input_summary="Pressure-test hearing posture and annexure support.",
                output_summary="Flags missing sanctioned site map and warns against overstating possession unless annexure support is complete.",
                status=AgentRunStatus.NEEDS_REVIEW,
                confidence_score=0.67,
                citations=["Specific Relief Act, 1877"],
                next_action="Obtain site map or soften possession claim.",
                started_at=now,
                completed_at=now,
                metadata_json={"lane": "critique"},
            ),
            AgentRunLog(
                id="agent-003",
                case_id=customs_petition.id,
                agent_name="Drafting Agent",
                title="Draft petition skeleton with prayer clauses",
                task_type="Draft generation",
                input_summary="Prepare petition skeleton and urgency prayer structure.",
                output_summary="Delivered filing-ready petition skeleton with maintainability and urgency sections organized for partner markup.",
                status=AgentRunStatus.COMPLETED,
                confidence_score=0.88,
                citations=["Constitution of Pakistan, Article 199", "2023 PTD 1442"],
                next_action="Verify invoice endorsements before final filing print.",
                started_at=now,
                completed_at=now,
                metadata_json={"lane": "drafting"},
            ),
        ]
        session.add_all(agent_logs)

        intelligence_artifacts = [
            IntelligenceArtifact(
                id="artifact-001",
                case_id=green_valley.id,
                document_id="doc-001",
                artifact_type=IntelligenceArtifactType.FACTUAL_SUMMARY,
                title=f"Factual summary - {green_valley.case_number}",
                content=(
                    "Factual Summary\n"
                    "The client challenges cancellation of a commercial allotment after substantial payment and partial possession. "
                    "The record currently frames the dispute as a void cancellation without speaking order, coupled with immediate alienation risk.\n\n"
                    "Key Parties\n- M/s Green Valley Estate Pvt. Ltd.\n- Defence Housing Authority, Lahore"
                ),
                structured_json={
                    "factualSummary": "Cancellation of the commercial allotment is challenged as void, unsupported by a speaking order, and commercially urgent because third-party transfer is threatened.",
                    "keyParties": [
                        "M/s Green Valley Estate Pvt. Ltd.",
                        "Defence Housing Authority, Lahore",
                    ],
                    "importantDates": ["2026-04-09", "2026-04-24"],
                    "reliefSought": green_valley.relief_sought,
                    "nextSteps": green_valley.procedural_alerts,
                    "citations": green_valley.precedents,
                },
                source="Chamber Local Intelligence",
                status=IntelligenceStatus.GENERATED,
            ),
            IntelligenceArtifact(
                id="artifact-002",
                case_id=green_valley.id,
                artifact_type=IntelligenceArtifactType.ISSUE_SPOTTING,
                title=f"Issue spotting - {green_valley.case_number}",
                content=(
                    "Likely Legal Issues\n"
                    "- Validity of cancellation without speaking order\n"
                    "- Maintainability despite internal DHA remedies\n"
                    "- Threshold for urgent interim protection\n\n"
                    "Maintainability Concerns\n"
                    "- Alternate remedy objection remains likely at threshold.\n"
                    "- Injunction urgency depends on a tighter annexure-backed chronology."
                ),
                structured_json={
                    "legalIssues": green_valley.legal_issues,
                    "maintainabilityConcerns": [
                        "Alternate remedy objection likely at threshold.",
                        "Urgent relief depends on a clean payment and possession chronology.",
                    ],
                    "missingInformation": [
                        "Sanctioned site map is still missing.",
                        "Internal appeal record remains incomplete.",
                    ],
                    "riskFlags": green_valley.risk_flags,
                    "recommendations": [
                        "Obtain the sanctioned site map before overstating possession.",
                        "Tighten the chronology around payments and surcharge dispute.",
                    ],
                    "citations": green_valley.precedents,
                },
                source="Chamber Local Intelligence",
                status=IntelligenceStatus.NEEDS_REVIEW,
            ),
            IntelligenceArtifact(
                id="artifact-003",
                case_id=customs_petition.id,
                document_id="doc-003",
                artifact_type=IntelligenceArtifactType.RESEARCH_NOTE,
                title="Research note - alternate remedy in customs detention challenge",
                content=(
                    "Issue\n"
                    "Alternate remedy exception in urgent customs detention challenge\n\n"
                    "Analysis Direction\n"
                    "- Frame the matter around denial of hearing and immediate commercial prejudice.\n"
                    "- Separate verified invoice history from placeholder authority leads.\n\n"
                    "Potential Authorities\n"
                    "- PLD 2020 Sindh 221\n"
                    "- 2023 PTD 1442"
                ),
                structured_json={
                    "query": research_entries[1].query,
                    "summary": research_entries[1].summary,
                    "analysisDirection": [
                        "Frame the petition around denial of hearing and jurisdictional overreach.",
                        "Verify all invoice endorsements before treating the release prayer as mature.",
                    ],
                    "statutoryHooks": customs_petition.linked_statutes,
                    "factualDependencies": [
                        "Two invoices still missing customs endorsement.",
                        "Need confirmation of prior clearance practice from source record.",
                    ],
                    "nextSteps": customs_petition.procedural_alerts,
                    "citations": research_entries[1].citations,
                },
                source="Chamber Local Intelligence",
                status=IntelligenceStatus.NEEDS_REVIEW,
            ),
            IntelligenceArtifact(
                id="artifact-004",
                case_id=green_valley.id,
                artifact_type=IntelligenceArtifactType.PRELIMINARY_OBJECTIONS,
                title=f"Preliminary objections chamber note - {green_valley.case_number}",
                content=(
                    "Objective\n"
                    "Draft preliminary objections in the Green Valley matter and flag record gaps.\n\n"
                    "Primary Chamber Output\n"
                    "1. Maintainability and forum objection framing\n"
                    "   Chamber note: anticipate the alternate remedy objection but stress that the cancellation is pleaded as void and commercially urgent.\n\n"
                    "Critic Review\n"
                    "Do not overstate possession until the sanctioned site map is on file. Keep the internal appeal record gap visible.\n\n"
                    "Final Reviewed Position\n"
                    "A provisional preliminary objections outline is available, but it should be used with a clear caveat about the missing site map and incomplete internal appeal record."
                ),
                structured_json={
                    "objective": "Draft preliminary objections in the Green Valley matter and flag record gaps.",
                    "workflow": "Workflow B - Maintainability / Objections",
                    "taskType": "preliminary_objections",
                    "citations": ["PLD 2018 Lahore 412", "2021 CLC 1188", "Specific Relief Act, 1877"],
                    "nextAction": "Obtain the sanctioned site map and soften possession framing until annexure support is complete.",
                    "agentSequence": [
                        "Manager Agent",
                        "Memory Agent",
                        "Procedural Agent",
                        "Research Agent",
                        "Drafting Agent",
                        "Critic Agent",
                    ],
                    "criticReview": {
                        "missingFacts": [
                            "Sanctioned site map is still missing.",
                            "Internal appeal record remains incomplete.",
                        ],
                        "unsupportedAssumptions": [
                            "Possession should not be overstated without annexure support.",
                        ],
                        "suggestedImprovements": [
                            "Obtain the sanctioned site map.",
                            "Clarify the internal appeal record before finalizing threshold objections.",
                        ],
                        "revisedOutputSummary": "A provisional preliminary objections outline is available, but it should be used with a clear caveat about the missing site map and incomplete internal appeal record.",
                    },
                },
                source="Chamber Orchestrator",
                status=IntelligenceStatus.NEEDS_REVIEW,
            ),
        ]
        session.add_all(intelligence_artifacts)

        chamber_run = ChamberRun(
            id="run-001",
            case_id=green_valley.id,
            task_type=ChamberTaskType.PRELIMINARY_OBJECTIONS,
            user_instruction="Draft preliminary objections in this matter and flag record gaps.",
            selected_workflow="Workflow B - Maintainability / Objections",
            status=ChamberRunStatus.COMPLETED,
            final_output=intelligence_artifacts[-1].content,
            final_summary="A provisional preliminary objections outline is available, but it should be used with a clear caveat about the missing site map and incomplete internal appeal record.",
            confidence_score=0.79,
            metadata_json={
                "memorySummary": "Case memory assembled from 2 intelligence artifact, 1 research entry, 1 draft, 1 note, 1 document.",
                "memorySources": [
                    {
                        "sourceId": "artifact-001",
                        "sourceType": "Intelligence Artifact",
                        "title": f"Factual summary - {green_valley.case_number}",
                        "detail": "Factual Summary",
                        "excerpt": "Cancellation of the commercial allotment is challenged as void and commercially urgent.",
                    },
                    {
                        "sourceId": "research-001",
                        "sourceType": "Research Entry",
                        "title": research_entries[0].title,
                        "detail": research_entries[0].source_type,
                        "excerpt": research_entries[0].summary,
                    },
                    {
                        "sourceId": "draft-001",
                        "sourceType": "Draft",
                        "title": drafts[0].title,
                        "detail": "Application / v3",
                        "excerpt": drafts[0].summary,
                    },
                    {
                        "sourceId": "doc-001",
                        "sourceType": "Document",
                        "title": documents[0].name,
                        "detail": documents[0].document_type.value,
                        "excerpt": documents[0].extracted_text_preview,
                    },
                ],
                "agentSequence": [
                    "Manager Agent",
                    "Memory Agent",
                    "Procedural Agent",
                    "Research Agent",
                    "Drafting Agent",
                    "Critic Agent",
                ],
                "routingNotes": "Maintainability / objections workflow was selected because the instruction signals threshold objections or jurisdiction concerns.",
                "legalGroundingStatus": "Grounded",
                "legalRetrievalQuery": "preliminary objections maintainability jurisdiction injunction order vii rule 11 order xxxix rule 1 specific relief act",
                "legalSources": [
                    {
                        "sourceId": "cpc-order-7-rule-11",
                        "title": "Code of Civil Procedure - Order VII Rule 11",
                        "citationLabel": "CPC Order VII Rule 11",
                        "excerpt": "Order VII Rule 11 addresses rejection of plaint where the plaint does not disclose a cause of action or is barred by law on the face of the plaint.",
                        "relevanceScore": 6.7,
                    },
                    {
                        "sourceId": "cpc-order-39-rule-1",
                        "title": "Code of Civil Procedure - Order XXXIX Rule 1",
                        "citationLabel": "CPC Order XXXIX Rule 1",
                        "excerpt": "Order XXXIX Rule 1 deals with temporary injunctions where property is threatened with alienation or dispossession.",
                        "relevanceScore": 6.1,
                    },
                    {
                        "sourceId": "specific-relief-section-54",
                        "title": "Specific Relief Act - Section 54",
                        "citationLabel": "Specific Relief Act Section 54",
                        "excerpt": "Section 54 concerns perpetual injunctions where a defendant threatens to invade the plaintiff's rights.",
                        "relevanceScore": 5.6,
                    },
                ],
                "finalArtifactId": "artifact-004",
                "linkedDraftId": "draft-001",
                "criticSummary": "A provisional preliminary objections outline is available, but it should be used with a clear caveat about the missing site map and incomplete internal appeal record.",
                "nextAction": "Obtain the sanctioned site map and soften possession framing until annexure support is complete.",
            },
            started_at=now,
            completed_at=now,
        )
        session.add(chamber_run)

        chamber_run_steps = [
            ChamberRunStep(
                id="run-step-001",
                run_id=chamber_run.id,
                step_order=1,
                agent_name="Manager Agent",
                task_label="Task routing and chamber plan",
                input_summary="Open the Green Valley matter and determine the right workflow for threshold objections.",
                output_summary="Selected the Workflow B - Maintainability / Objections workflow for preliminary_objections on Civil Suit No. 102/2026.",
                full_output="Objective\nDraft preliminary objections in this matter and flag record gaps.\n\nSelected Workflow\nWorkflow B - Maintainability / Objections",
                structured_json={
                    "objective": "Draft preliminary objections in this matter and flag record gaps.",
                    "selectedWorkflow": "Workflow B - Maintainability / Objections",
                },
                status=ChamberRunStepStatus.COMPLETED,
                confidence_score=0.86,
                source_artifact_ids=["artifact-001", "artifact-002"],
                metadata_json={"workflow": "Workflow B - Maintainability / Objections"},
                created_at=now,
                completed_at=now,
            ),
            ChamberRunStep(
                id="run-step-002",
                run_id=chamber_run.id,
                step_order=2,
                agent_name="Memory Agent",
                task_label="Matter continuity retrieval",
                input_summary="Retrieve prior summaries, research, drafts, and document context for the Green Valley matter.",
                output_summary="Retrieved 4 matter memory sources for the run.",
                full_output="Memory Summary\nUsed prior summary artifact, one research entry, one draft, and one processed pleading excerpt.",
                structured_json={
                    "summary": "Used prior summary artifact, one research entry, one draft, and one processed pleading excerpt.",
                    "sources": chamber_run.metadata_json["memorySources"],
                },
                status=ChamberRunStepStatus.COMPLETED,
                confidence_score=0.82,
                source_artifact_ids=["artifact-001", "artifact-002"],
                metadata_json={"sourceDocumentIds": ["doc-001"]},
                created_at=now,
                completed_at=now,
            ),
            ChamberRunStep(
                id="run-step-003",
                run_id=chamber_run.id,
                step_order=3,
                agent_name="Procedural Agent",
                task_label="Procedural posture and risk check",
                input_summary="Review filing stage and hearing posture for threshold objections.",
                output_summary="The matter is currently at: Interim injunction pending before motion bench.",
                full_output="Procedural Posture\nThe matter is presently at Interim injunction pending before motion bench before Lahore High Court, Lahore.",
                structured_json={
                    "proceduralPosture": green_valley.filing_stage,
                    "checkpoints": green_valley.procedural_alerts,
                    "cautionFlags": green_valley.risk_flags,
                    "nextActions": [
                        "Confirm every annexure before relying on the possession narrative.",
                    ],
                },
                status=ChamberRunStepStatus.COMPLETED,
                confidence_score=0.79,
                source_artifact_ids=["artifact-001"],
                metadata_json={},
                created_at=now,
                completed_at=now,
            ),
            ChamberRunStep(
                id="run-step-004",
                run_id=chamber_run.id,
                step_order=4,
                agent_name="Research Agent",
                task_label="Issue analysis and authority direction",
                input_summary="Surface likely maintainability objections and supporting authority leads.",
                output_summary="Validity of cancellation without speaking order; Maintainability despite internal DHA remedies; Threshold for urgent interim protection",
                full_output="Likely Legal Issues\n- Validity of cancellation without speaking order\n- Maintainability despite internal DHA remedies\n- Threshold for urgent interim protection",
                structured_json={
                    "legalIssues": green_valley.legal_issues,
                    "maintainabilityConcerns": [
                        "Alternate remedy objection likely at threshold.",
                        "Urgent relief depends on a clean payment and possession chronology.",
                    ],
                    "missingInformation": [
                        "Sanctioned site map is still missing.",
                        "Internal appeal record remains incomplete.",
                    ],
                    "citations": ["PLD 2018 Lahore 412", "2021 CLC 1188"],
                    "recommendations": [
                        "Tighten the chronology around payments and surcharge dispute.",
                        "Frame the objection as provisional until the record gap is cured.",
                    ],
                },
                status=ChamberRunStepStatus.COMPLETED,
                confidence_score=0.74,
                source_artifact_ids=["artifact-002"],
                metadata_json={},
                created_at=now,
                completed_at=now,
            ),
            ChamberRunStep(
                id="run-step-005",
                run_id=chamber_run.id,
                step_order=5,
                agent_name="Drafting Agent",
                task_label="Preliminary objections outline drafting pass",
                input_summary="Convert the issue and procedure review into a first-pass objections outline.",
                output_summary="AI-assisted first-pass preliminary objections outline for M/s Green Valley Estate Pvt. Ltd. v. Defence Housing Authority, Lahore.",
                full_output="1. Maintainability and jurisdiction objections\n2. Record gaps and evidentiary reservations\n3. Prayer and without-prejudice reservations",
                structured_json={
                    "title": f"Preliminary objections outline - {green_valley.case_number}",
                    "draftType": "Preliminary objections outline",
                    "artifactType": "Preliminary Objections",
                    "citations": ["PLD 2018 Lahore 412", "2021 CLC 1188"],
                    "nextAction": "Pressure-test the draft against the live annexure set.",
                },
                status=ChamberRunStepStatus.COMPLETED,
                confidence_score=0.71,
                source_artifact_ids=["artifact-001", "artifact-002"],
                metadata_json={"nextAction": "Pressure-test the draft against the live annexure set."},
                created_at=now,
                completed_at=now,
            ),
            ChamberRunStep(
                id="run-step-006",
                run_id=chamber_run.id,
                step_order=6,
                agent_name="Critic Agent",
                task_label="Critic and reliability review",
                input_summary="Review the draft support for missing facts, unsupported assumptions, and procedural dependencies.",
                output_summary="A provisional preliminary objections outline is available, but it should be used with a clear caveat about the missing site map and incomplete internal appeal record.",
                full_output="Missing Facts or Record Gaps\n- Sanctioned site map is still missing.\n- Internal appeal record remains incomplete.\n\nSuggested Improvements\n- Obtain the sanctioned site map.\n- Clarify the internal appeal record before finalizing threshold objections.",
                structured_json={
                    "missingFacts": [
                        "Sanctioned site map is still missing.",
                        "Internal appeal record remains incomplete.",
                    ],
                    "unsupportedAssumptions": [
                        "Possession should not be overstated without annexure support.",
                    ],
                    "structuralWeaknesses": [
                        "Threshold objections should remain provisional until the annexure bundle is complete.",
                    ],
                    "proceduralDependencies": green_valley.procedural_alerts,
                    "suggestedImprovements": [
                        "Obtain the sanctioned site map.",
                        "Clarify the internal appeal record before finalizing threshold objections.",
                    ],
                    "revisedOutputSummary": "A provisional preliminary objections outline is available, but it should be used with a clear caveat about the missing site map and incomplete internal appeal record.",
                },
                status=ChamberRunStepStatus.COMPLETED,
                confidence_score=0.79,
                source_artifact_ids=["artifact-001", "artifact-002"],
                metadata_json={"reviewedAgents": ["Manager Agent", "Memory Agent", "Procedural Agent", "Research Agent", "Drafting Agent"]},
                created_at=now,
                completed_at=now,
            ),
        ]
        session.add_all(chamber_run_steps)

        session.add(
            AgentRunLog(
                id="agent-004",
                case_id=green_valley.id,
                agent_name="Manager Agent",
                title="Chamber workflow completed for preliminary objections",
                task_type="preliminary_objections",
                input_summary="Draft preliminary objections in this matter and flag record gaps.",
                output_summary="A provisional preliminary objections outline is available, but it should be used with a clear caveat about the missing site map and incomplete internal appeal record.",
                status=AgentRunStatus.COMPLETED,
                confidence_score=0.79,
                citations=["PLD 2018 Lahore 412", "2021 CLC 1188", "Specific Relief Act, 1877"],
                next_action="Obtain the sanctioned site map and soften possession framing until annexure support is complete.",
                started_at=now,
                completed_at=now,
                metadata_json={
                    "runId": "run-001",
                    "workflow": "Workflow B - Maintainability / Objections",
                    "artifactId": "artifact-004",
                    "criticSummary": "A provisional preliminary objections outline is available, but it should be used with a clear caveat about the missing site map and incomplete internal appeal record.",
                },
            )
        )

        seeded_grounding = [
            GroundingLink(
                id="grounding-001",
                run_id="run-001",
                source_id="cpc-order-7-rule-11",
                chunk_id=first_chunk_id(session, "cpc-order-7-rule-11"),
                relevance_score=6.7,
                usage_type=GroundingUsageType.RETRIEVED,
                excerpt="Order VII Rule 11 addresses rejection of plaint where the plaint does not disclose a cause of action or is barred by law on the face of the plaint.",
            ),
            GroundingLink(
                id="grounding-002",
                run_id="run-001",
                source_id="cpc-order-39-rule-1",
                chunk_id=first_chunk_id(session, "cpc-order-39-rule-1"),
                relevance_score=6.1,
                usage_type=GroundingUsageType.RETRIEVED,
                excerpt="Order XXXIX Rule 1 deals with temporary injunctions where property is threatened with alienation or dispossession.",
            ),
            GroundingLink(
                id="grounding-003",
                run_id="run-001",
                source_id="specific-relief-section-54",
                chunk_id=first_chunk_id(session, "specific-relief-section-54"),
                relevance_score=5.6,
                usage_type=GroundingUsageType.RETRIEVED,
                excerpt="Section 54 concerns perpetual injunctions where a defendant threatens to invade the plaintiff's rights.",
            ),
            GroundingLink(
                id="grounding-004",
                artifact_id="artifact-004",
                source_id="cpc-order-7-rule-11",
                chunk_id=first_chunk_id(session, "cpc-order-7-rule-11"),
                relevance_score=6.7,
                usage_type=GroundingUsageType.RELIED_ON,
                excerpt="Order VII Rule 11 addresses rejection of plaint where the plaint does not disclose a cause of action or is barred by law on the face of the plaint.",
            ),
            GroundingLink(
                id="grounding-005",
                artifact_id="artifact-004",
                source_id="cpc-order-39-rule-1",
                chunk_id=first_chunk_id(session, "cpc-order-39-rule-1"),
                relevance_score=6.1,
                usage_type=GroundingUsageType.RELIED_ON,
                excerpt="Order XXXIX Rule 1 deals with temporary injunctions where property is threatened with alienation or dispossession.",
            ),
            GroundingLink(
                id="grounding-006",
                artifact_id="artifact-003",
                source_id="constitution-article-199",
                chunk_id=first_chunk_id(session, "constitution-article-199"),
                relevance_score=6.4,
                usage_type=GroundingUsageType.RELIED_ON,
                excerpt="Article 199 empowers a High Court to issue constitutional directions where unlawful exercise of power or lack of lawful authority is shown.",
            ),
            GroundingLink(
                id="grounding-007",
                artifact_id="artifact-003",
                source_id="constitution-article-10a",
                chunk_id=first_chunk_id(session, "constitution-article-10a"),
                relevance_score=5.9,
                usage_type=GroundingUsageType.RELIED_ON,
                excerpt="Article 10A supports arguments around denial of hearing and due process.",
            ),
            GroundingLink(
                id="grounding-008",
                artifact_id="artifact-001",
                source_id="cpc-order-39-rule-1",
                chunk_id=first_chunk_id(session, "cpc-order-39-rule-1"),
                relevance_score=5.1,
                usage_type=GroundingUsageType.SUGGESTED,
                excerpt="Order XXXIX Rule 1 is a core procedural hook for urgent preservation relief in property disputes.",
            ),
        ]
        session.add_all(seeded_grounding)
        session.commit()

        print("Seed completed successfully.")
    finally:
        session.close()


if __name__ == "__main__":
    seed()
