"""Brief schemas (PRD F-006, System Design §3).

`ModelBrief` is the only shape Gemini may return. It deliberately has no numeric, score, or flag
fields: amounts, counts, windows, and rule matches come from graph tool output (BR-003).
`Brief` adds server-set metadata; the model never sets `model`, `run_at`, or `cached`.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class Statement(BaseModel):
    text: str = Field(description="One factual sentence grounded in the cited evidence.")
    evidence_ids: list[str] = Field(
        description="IDs from the evidence bundle that support this sentence. Copy them exactly."
    )


class ModelBrief(BaseModel):
    observations: list[Statement] = Field(
        description="What the evidence shows. Every observation cites at least one evidence ID."
    )
    counterevidence: list[Statement] = Field(
        description="Evidence that weakens or contradicts a suspicious reading, e.g. no rapid forwarding."
    )
    unknowns: list[str] = Field(
        description="Questions the data cannot answer, e.g. where funds went past the data boundary."
    )
    suggested_checks: list[str] = Field(
        description="Manual checks an analyst could do next. No accusations, no conclusions of guilt."
    )


class Brief(ModelBrief):
    case_id: str
    model: str
    run_at: datetime
    cached: bool = False
