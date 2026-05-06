LEGAL_CHAMBER_BRIEF = """
You are assisting a Pakistani legal chamber. Produce structured internal work product,
not final legal advice. Distinguish between facts grounded in supplied material and
inferences that still need review. When authority support is uncertain, label it as a
placeholder or research lead instead of presenting it as a verified citation.
""".strip()

SUMMARY_SECTIONS = [
    "Factual Summary",
    "Procedural Summary",
    "Key Parties",
    "Important Dates",
    "Relief Sought",
    "Next-Step Recommendations",
]

ISSUE_SECTIONS = [
    "Likely Legal Issues",
    "Maintainability Concerns",
    "Missing Information or Missing Documents",
    "Risk Flags",
    "Next-Step Recommendations",
]

RESEARCH_SECTIONS = [
    "Issue",
    "Analysis Direction",
    "Potential Authorities",
    "Statutory Hooks",
    "Factual Dependencies",
    "Next Research Steps",
]


def placeholder_authority(label: str) -> str:
    return f"Placeholder research lead - {label}"
