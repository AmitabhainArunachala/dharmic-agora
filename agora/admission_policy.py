"""Named admission policies for SAB's runtime surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class AdmissionDecision:
    status: str
    reason: str
    admitted: bool


@dataclass(frozen=True)
class AdmissionPolicy:
    name: str
    lane: str
    description: str

    def decide(self, gate_result: Dict[str, Any]) -> AdmissionDecision:
        if self.lane == "public_fast_lane":
            if bool(gate_result.get("required_passed", False)):
                return AdmissionDecision(status="spark", reason="required_gates_passed", admitted=True)
            if not bool(gate_result.get("ahimsa_passed", True)):
                return AdmissionDecision(status="compost", reason="ahimsa_gate_failed", admitted=False)
            return AdmissionDecision(status="compost", reason="required_gate_failed", admitted=False)
        if self.lane == "protocol_human_review":
            return AdmissionDecision(status="pending", reason="queued_for_human_review", admitted=False)
        raise ValueError(f"Unknown admission lane: {self.lane}")


FAST_LANE_AUTO = AdmissionPolicy(
    name="FAST_LANE_AUTO",
    lane="public_fast_lane",
    description="Public spark lane: required gate failure is composted immediately.",
)

PROTOCOL_LANE_HUMAN_REVIEW = AdmissionPolicy(
    name="PROTOCOL_LANE_HUMAN_REVIEW",
    lane="protocol_human_review",
    description="Protocol lane: submissions are queued with gate evidence for moderation.",
)
