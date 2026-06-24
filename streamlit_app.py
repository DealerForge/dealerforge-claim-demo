#!/usr/bin/env python3
# DealerForge CLAIM - Working Demo (single-file Streamlit app).
# Gate A | synthetic data only | advisory only.
import streamlit as st
import pandas as pd

# ===== data =====
REASON_CODES = {
    "T": "Diagnostic Operation Discrepancies",
    "L": "Designated-Management Authorization Missing",
    "E": "Add-On Operations",
    "K": "Required Specs Not Recorded",
    "M": "Tech Notes Do Not Support Repair",
    "C": "Labor Not Supported",
    "B": "Non-Warranty Item",
    "N": "Missing Claims",
}

EVIDENCE_STATES = ["Present", "Missing", "Unclear", "Conflicting", "Not Applicable"]

# Canonical permitted labels (used by the UI for compliant phrasing)
MODULE_A_LABELS = [
    "Likely chargeback risk", "Possible — needs OEM verification", "Documentation gap",
    "Process/pre-auth gap", "Not enough information", "No flags found",
]
MODULE_B_LABELS = [
    "Likely legitimate opportunity — verify in OEM system",
    "Possible related operation — needs OEM verification",
    "Diagnostic time may be supportable — needs documentation",
    "Documentation gap blocking recovery", "Not enough information",
    "Not supported by available facts", "Chargeback risk if claimed without correction",
]

def _ro(**kw):
    kw.setdefault("module_a", []); kw.setdefault("module_b", [])
    kw.setdefault("module_a_note", ""); kw.setdefault("module_b_note", "")
    return kw

CASES = [
    _ro(
        ro_id="DUMMY-RO-3001", scenario="Supported opportunity", tag="supported",
        vehicle={"year": 2023, "make": "RAM", "model": "2500", "vin_token": "VINTOK-3001"},
        concern="Coolant leak; temperature gauge climbing.",
        cause="Water pump weep-hole seepage confirmed; bearing play present.",
        correction="Replaced water pump; pressure-tested cooling system; verified no leak; temp normal on road test.",
        evidence=[
            {"item": "DTC / scan report", "state": "Present"},
            {"item": "measured values (pressure test, temp)", "state": "Present"},
            {"item": "pinpoint diagnostic steps in notes", "state": "Present"},
            {"item": "causal part on claim (water pump)", "state": "Present"},
            {"item": "core return confirmation", "state": "Missing"},
            {"item": "diagnostic time punches", "state": "Unclear"},
        ],
        module_a=[
            {"id": "A1", "code": "K", "label": "Likely chargeback risk",
             "title": "Core required but return not confirmed",
             "evidence": ["core return confirmation"], "role": "Warranty Admin",
             "fix": "Confirm core return / exchange before submission; attach core document.",
             "verify": "Core/exchange status in DealerCONNECT.",
             "source": {"id": "S-PARTS-CORE", "type": "audit-calibrated pattern", "confidence": "Provisional"},
             "exposure_usd": 240},
            {"id": "A2", "code": "M", "label": "Documentation gap",
             "title": "Narrative phrasing flagged as possibly discouraged wording",
             "evidence": ["pinpoint diagnostic steps in notes"], "role": "Advisor / Warranty Admin",
             "fix": "Human review the full note; confirm cause/correction language is acceptable.",
             "verify": "Internal documentation review.",
             "source": {"id": "S-PHRASING", "type": "audit-calibrated pattern", "confidence": "Provisional"},
             "exposure_usd": 0, "borderline": True},
        ],
        module_b=[
            {"id": "B1", "label": "Diagnostic time may be supportable — needs documentation",
             "title": "Diagnostic time performed but punches unclear", "role": "Technician / Warranty Admin",
             "facts_present": "Pinpoint diagnostic steps documented in notes.",
             "facts_missing": "Separate, non-overlapping diagnostic time punch.",
             "document": "Add/clarify the diagnostic time punch tied to the condition.",
             "verify": "Diagnostic LOP and time in DealerCONNECT — no current value asserted.",
             "category": "Diagnostic time support",
             "source": {"id": "S-DIAG-LOP", "type": "candidate to verify", "confidence": "Needs current OEM verification"}},
            {"id": "B2", "label": "Likely legitimate opportunity — verify in OEM system",
             "title": "Core value may be recoverable once core return completed", "role": "Warranty Admin / Claims",
             "facts_present": "Causal part on claim; repair facts support the part.",
             "facts_missing": "Completed core return.",
             "document": "Complete and document the core return.",
             "verify": "Core value in OEM system — candidate to verify, no value asserted, no recovery guaranteed.",
             "category": "Parts / core / exchange",
             "source": {"id": "S-CORE-VALUE", "type": "candidate to verify", "confidence": "Needs current OEM verification"}},
        ],
    ),
    _ro(
        ro_id="DUMMY-RO-3002", scenario="Documentation-blocked", tag="blocked",
        vehicle={"year": 2024, "make": "Jeep", "model": "Wrangler", "vin_token": "VINTOK-3002"},
        concern="Intermittent stall / no-start.",
        cause="Crankshaft position sensor fault (pinpoint test isolated sensor).",
        correction="Replaced crankshaft position sensor; verified start and run; cleared codes.",
        evidence=[
            {"item": "DTC / scan report", "state": "Present"},
            {"item": "pinpoint diagnostic steps in notes", "state": "Present"},
            {"item": "causal part on claim", "state": "Present"},
            {"item": "technician time punches", "state": "Missing"},
            {"item": "claimed labor vs. punch reconciliation", "state": "Conflicting"},
        ],
        module_a=[
            {"id": "A1", "code": "T", "label": "Likely chargeback risk",
             "title": "Technician time punches missing for the diagnostic/repair",
             "evidence": ["technician time punches"], "role": "Technician / Warranty Admin",
             "fix": "Locate or correct the time punch record before submission.",
             "verify": "Time punch / labor in DealerCONNECT.",
             "source": {"id": "S-TIME-PUNCH", "type": "audit-calibrated pattern", "confidence": "Provisional"},
             "exposure_usd": 310},
            {"id": "A2", "code": "C", "label": "Likely chargeback risk",
             "title": "Claimed labor not reconciled to a punch (conflicting)",
             "evidence": ["claimed labor vs. punch reconciliation"], "role": "Warranty Admin",
             "fix": "Reconcile claimed time to the actual punch before submission.",
             "verify": "Labor screen in DealerCONNECT.",
             "source": {"id": "S-LABOR-SUPPORT", "type": "audit-calibrated pattern", "confidence": "Provisional"},
             "exposure_usd": 150},
        ],
        module_b=[
            {"id": "B1", "label": "Documentation gap blocking recovery",
             "title": "Diagnostic time likely performed but blocked by missing punches",
             "role": "Technician / Warranty Admin",
             "facts_present": "Pinpoint diagnostic steps documented.",
             "facts_missing": "Time punches to substantiate the diagnostic time.",
             "document": "Document the diagnostic time punch FIRST — do not claim without it.",
             "verify": "After documentation, verify the diagnostic LOP in DealerCONNECT — candidate to verify.",
             "category": "Documentation gap blocking recovery",
             "source": {"id": "S-DIAG-LOP", "type": "candidate to verify", "confidence": "Needs current OEM verification"}},
        ],
    ),
    _ro(
        ro_id="DUMMY-RO-3003", scenario="Not-supported-by-facts", tag="not_supported",
        vehicle={"year": 2025, "make": "Jeep", "model": "Grand Cherokee", "vin_token": "VINTOK-3003"},
        concern="Customer requested oil change (maintenance).",
        cause="Routine maintenance — no defect diagnosed.",
        correction="Performed oil and filter change.",
        evidence=[
            {"item": "3 C's (concern/cause/correction) detail", "state": "Unclear"},
            {"item": "diagnostic / defect evidence", "state": "Not Applicable"},
            {"item": "causal part", "state": "Not Applicable"},
        ],
        module_a=[
            {"id": "A1", "code": "B", "label": "Likely chargeback risk",
             "title": "Weak 3 C's — narrative does not establish a warrantable defect",
             "evidence": ["3 C's (concern/cause/correction) detail"], "role": "Advisor / Technician",
             "fix": "This is maintenance; do not submit as warranty. Confirm correct pay type (customer-pay).",
             "verify": "Pay type / coverage in DealerCONNECT.",
             "source": {"id": "S-3CS", "type": "audit-calibrated pattern", "confidence": "Provisional"},
             "exposure_usd": 95},
        ],
        module_b=[],
        module_b_note="No recovery opportunity — supporting facts are absent. (Risk and recovery are independent passes. Proves the tool is not a 'bill-more' machine.)",
    ),
    _ro(
        ro_id="DUMMY-RO-3004", scenario="Clean RO", tag="clean",
        vehicle={"year": 2024, "make": "RAM", "model": "1500", "vin_token": "VINTOK-3004"},
        concern="Blower motor inoperative on some speeds.",
        cause="Blower motor resistor failed (measured open circuit).",
        correction="Replaced blower motor resistor; verified all blower speeds; documented measured values.",
        evidence=[
            {"item": "DTC / measured values", "state": "Present"},
            {"item": "3 C's detail (cause names failed part + steps)", "state": "Present"},
            {"item": "causal part on claim", "state": "Present"},
            {"item": "technician time punches", "state": "Present"},
            {"item": "verification after repair", "state": "Present"},
        ],
        module_a=[],
        module_a_note="No flags found. (Not claim approval.)",
        module_b=[],
        module_b_note="No recovery opportunity — well-documented. (Not approval. The tool does not cry wolf.)",
    ),
    _ro(
        ro_id="DUMMY-RO-3005", scenario="In-stock battery pattern", tag="supported",
        vehicle={"year": 2024, "make": "Jeep", "model": "Gladiator", "vin_token": "VINTOK-3005"},
        concern="No-start on dealer-inventory unit; battery suspected.",
        cause="Battery failed test on an in-stock unit; replaced.",
        correction="Tested and replaced battery; verified start.",
        evidence=[
            {"item": "battery test printout (correct tester)", "state": "Present"},
            {"item": "in-stock monthly battery-maintenance records", "state": "Missing"},
            {"item": "designated-management authorization", "state": "Missing"},
            {"item": "causal part on claim", "state": "Present"},
        ],
        module_a=[
            {"id": "A1", "code": "B", "label": "Likely chargeback risk",
             "title": "In-stock battery without monthly maintenance records",
             "evidence": ["in-stock monthly battery-maintenance records"], "role": "Warranty Admin / Parts",
             "fix": "Provide in-stock monthly battery-maintenance records, or route to correct pay type.",
             "verify": "In-stock unit battery policy in DealerCONNECT.",
             "source": {"id": "S-INSTOCK-BATT", "type": "audit-calibrated pattern", "confidence": "Provisional"},
             "exposure_usd": 185},
            {"id": "A2", "code": "L", "label": "Process/pre-auth gap",
             "title": "Designated-management authorization missing (in-stock unit)",
             "evidence": ["designated-management authorization"], "role": "Service Management",
             "fix": "Obtain DMP authorization on the hard copy before submission.",
             "verify": "Authorization on hard copy.",
             "source": {"id": "S-DMP", "type": "audit-calibrated pattern", "confidence": "Provisional"},
             "exposure_usd": 130},
        ],
        module_b=[
            {"id": "B1", "label": "Documentation gap blocking recovery",
             "title": "Battery claim blocked until maintenance records + DMP authorization provided",
             "role": "Warranty Admin / Service Management",
             "facts_present": "Battery test printout from the correct tester.",
             "facts_missing": "Monthly maintenance records; DMP authorization.",
             "document": "Provide the records and authorization FIRST — do not claim without them.",
             "verify": "In-stock battery requirements in DealerCONNECT — candidate to verify.",
             "category": "Documentation gap blocking recovery",
             "source": {"id": "S-INSTOCK-BATT", "type": "candidate to verify", "confidence": "Needs current OEM verification"}},
        ],
    ),
    _ro(
        ro_id="DUMMY-RO-3006", scenario="Add-on operation", tag="supported",
        vehicle={"year": 2023, "make": "Jeep", "model": "Compass", "vin_token": "VINTOK-3006"},
        concern="Check-engine light; customer also approved a noticed belt squeal.",
        cause="Purge valve fault (primary); serpentine belt worn (added).",
        correction="Replaced purge valve; replaced serpentine belt as an added operation.",
        evidence=[
            {"item": "DTC for purge valve", "state": "Present"},
            {"item": "causal part (purge valve)", "state": "Present"},
            {"item": "customer authorization for add-on (belt)", "state": "Unclear"},
            {"item": "service-management authorization for add-on", "state": "Missing"},
        ],
        module_a=[
            {"id": "A1", "code": "E", "label": "Likely chargeback risk",
             "title": "Add-on operation lacks documented SM + customer authorization",
             "evidence": ["service-management authorization for add-on", "customer authorization for add-on (belt)"],
             "role": "Service Management / Advisor",
             "fix": "Document SM + customer authorization next to the added belt operation, with date/initials.",
             "verify": "Authorization on hard copy.",
             "source": {"id": "S-ADDON", "type": "audit-calibrated pattern", "confidence": "Provisional"},
             "exposure_usd": 175},
        ],
        module_b=[
            {"id": "B1", "label": "Possible related operation — needs OEM verification",
             "title": "Primary purge-valve repair appears supported — verify related-operation rules",
             "role": "Warranty Admin",
             "facts_present": "DTC and causal part documented for the primary repair.",
             "facts_missing": "Confirmation the belt is warranty vs. customer-pay.",
             "document": "Confirm pay type for the belt; keep the warranty primary clean.",
             "verify": "Related-operation and pay-type rules in DealerCONNECT — candidate to verify.",
             "category": "Candidate LOP / related operation",
             "source": {"id": "S-RELATED-OP", "type": "candidate to verify", "confidence": "Needs current OEM verification"}},
        ],
    ),
    _ro(
        ro_id="DUMMY-RO-3007", scenario="Missing hard copy", tag="not_supported",
        vehicle={"year": 2022, "make": "RAM", "model": "ProMaster", "vin_token": "VINTOK-3007"},
        concern="Electrical fault repaired; claim under review.",
        cause="Wiring repair completed per tech.",
        correction="Repaired wiring harness connector.",
        evidence=[
            {"item": "original hard copy on file", "state": "Missing"},
            {"item": "claim / labor screen", "state": "Missing"},
            {"item": "tech notes", "state": "Unclear"},
        ],
        module_a=[
            {"id": "A1", "code": "N", "label": "Likely chargeback risk",
             "title": "Original hard copy not on file — repair cannot be substantiated",
             "evidence": ["original hard copy on file"], "role": "Warranty Admin",
             "fix": "Locate the original hard copy / warranty file before any submission.",
             "verify": "File retrieval; claim/labor screen.",
             "source": {"id": "S-MISSING-CLAIM", "type": "audit-calibrated pattern", "confidence": "Provisional"},
             "exposure_usd": 220},
            {"id": "A2", "code": "M", "label": "Documentation gap",
             "title": "Tech notes unclear — do not establish cause/correction",
             "evidence": ["tech notes"], "role": "Technician",
             "fix": "Rebuild cause/correction detail from source evidence (no invention).",
             "verify": "Internal review.",
             "source": {"id": "S-TECHNOTES", "type": "audit-calibrated pattern", "confidence": "Provisional"},
             "exposure_usd": 0},
        ],
        module_b=[],
        module_b_note="No recovery opportunity — facts and hard copy are absent. Locate the file first; do not reconstruct after the fact.",
    ),
    _ro(
        ro_id="DUMMY-RO-3008", scenario="Supported diagnostic + goodwill check", tag="supported",
        vehicle={"year": 2023, "make": "Jeep", "model": "Grand Cherokee L", "vin_token": "VINTOK-3008"},
        concern="HVAC inoperative; out-of-coverage by a small margin.",
        cause="Blend-door actuator failed; confirmed by actuation test.",
        correction="Replaced actuator; verified operation.",
        evidence=[
            {"item": "DTC / actuation test", "state": "Present"},
            {"item": "causal part on claim", "state": "Present"},
            {"item": "diagnostic time punch", "state": "Present"},
            {"item": "goodwill / coverage eligibility", "state": "Unclear"},
        ],
        module_a=[
            {"id": "A1", "code": "T", "label": "Possible — needs OEM verification",
             "title": "Diagnostic time present — confirm SM authorization expectation",
             "evidence": ["diagnostic time punch"], "role": "Warranty Admin",
             "fix": "Confirm whether SM authorization is required for this diagnostic line.",
             "verify": "8541 authorization expectation in WAM/DealerCONNECT.",
             "source": {"id": "S-DIAG-AUTH", "type": "audit-calibrated pattern", "confidence": "Provisional"},
             "exposure_usd": 90},
        ],
        module_b=[
            {"id": "B1", "label": "Possible related operation — needs OEM verification",
             "title": "Goodwill / coverage eligibility may apply — verify the specific program",
             "role": "Warranty Admin / Claims",
             "facts_present": "Repair facts and diagnostic documented; just out of coverage by a small margin.",
             "facts_missing": "Confirmed goodwill program and eligibility.",
             "document": "Confirm the specific goodwill program and eligibility before any request.",
             "verify": "Goodwill/NVP grid eligibility in DealerCONNECT — candidate to verify, no value asserted.",
             "category": "Goodwill / NVP / service-contract",
             "source": {"id": "S-GOODWILL", "type": "candidate to verify", "confidence": "Needs current OEM verification"}},
        ],
    ),
]

CASE_BY_ID = {c["ro_id"]: c for c in CASES}

# ----- Executive framing constants (from the DealerForge investor briefing) -----
MARKET = {
    "service_parts_pool": "$164B+",
    "service_parts_pool_note": "annual U.S. franchised service & parts sales",
    "ros_per_year": "276M+",
    "ros_per_year_note": "repair orders written across U.S. dealerships each year",
    "source": "NADA Data, U.S. franchised new-car dealerships (2025).",
}

CLAIM_LOOP = [
    ("Review before submission", "Examines repair orders before they are submitted."),
    ("Flag exposure", "Surfaces missing authorizations, documentation gaps, and chargeback risk."),
    ("Identify supported recovery", "Finds legitimate recovery grounded in actual repair facts — candidate to verify."),
    ("Coach for next time", "Guides advisors and technicians to prevent the same failure again."),
]

STRICT_RULES = ["No inflation.", "No invented facts.", "Evidence-based recovery only."]

PLATFORM_VISION = [
    ("Warranty Audit Protection & Supported Recovery", "The entry wedge — sharp, measurable, defensible."),
    ("Fixed Ops Revenue Integrity", "Documentation, process, and accountability across the service drive."),
    ("DealerForge Operating Intelligence", "A full dealership intelligence platform spanning service, sales, and trust."),
]

GO_TO_MARKET = ["Pilot", "Prove", "Expand", "Scale"]

# Provisional validation targets (non-guaranteed; calibrate with IT + reviewer)
VALIDATION_TARGETS = [
    ("Material-defect recall", "Share of human-verified material defects the tool also flagged", "calibrate"),
    ("Clean-case recognition", "Share of clean ROs correctly left clean", "calibrate"),
    ("False findings per RO", "Reviewer-judged unfounded flags per RO", "trend down"),
    ("Invented / incorrect facts", "Asserted facts not actually present", "0 (hard)"),
    ("Over-claim leakage", "'use this LOP' / asserted dollar value", "0 (hard)"),
    ("Reviewer willingness to continue", "The most honest single signal", "yes"),
    ("Security incidents / unauthorized external actions", "Any submit/write/email/financial action", "0 (hard)"),
]

# ===== engine =====
import datetime
from collections import Counter, defaultdict

OEM_ADAPTER = "no current value — verify in DealerCONNECT/OEM"

# Decision vocabulary -> (human-readable, lifecycle state, gate)
DECISIONS = {
    "CONFIRM_RISK":          ("Confirmed — will correct before submission", "confirmed_exposure", "human-confirmed"),
    "DISMISS_FALSE_POSITIVE":("Dismissed — false positive (overrules system)", "false_positive", "G3"),
    "REQUEST_DOCUMENTATION": ("Document first — recovery blocked until documented", "blocked_documentation", "G2 blocked"),
    "APPROVE_CANDIDATE":     ("Approved as candidate — remains candidate until OEM-verified", "approved_candidate", "G2"),
    "REJECT":                ("Rejected", "rejected", "G3"),
    "PENDING":               ("Pending human review", "under_review", ""),
}

# Sensible default disposition per finding (the "pre-approved" replay; user can change live)
def default_decision(kind, finding):
    if kind == "A":
        return "DISMISS_FALSE_POSITIVE" if finding.get("borderline") else "CONFIRM_RISK"
    lab = finding.get("label", "")
    if "Documentation gap blocking recovery" in lab:
        return "REQUEST_DOCUMENTATION"
    if "Diagnostic time may be supportable" in lab:
        return "REQUEST_DOCUMENTATION"
    return "APPROVE_CANDIDATE"


def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def process_review(case, decisions=None, reviewer=None):
    """decisions: {finding_id: decision_key}. reviewer: {name, role}."""
    decisions = decisions or {}
    reviewer = reviewer or {"name": "Warranty Admin", "role": "Warranty Administrator (DEMO)"}
    audit = []
    def log(actor, action, target, before=None, after=None):
        audit.append({"event_id": "EV%03d" % (len(audit) + 1), "actor": actor, "action": action,
                      "target": target, "before": before, "after": after, "ts": now_iso()})

    log("system", "G1_intake_accepted", case["ro_id"], after="admitted (sanitization attested)")
    rows_a, rows_b, external = [], [], []

    def handle(findings, kind):
        out = []
        for f in findings:
            fid = f["id"]
            log("system", "finding_created", fid, after="candidate")
            dec = decisions.get(fid) or default_decision(kind, f)
            human, state, gate = DECISIONS.get(dec, DECISIONS["PENDING"])
            if dec != "PENDING":
                log("%s / %s" % (reviewer["name"], reviewer["role"]), "ReviewDecision", fid,
                    before="candidate", after=state)
            if dec == "CONFIRM_RISK":
                external.append({"finding": fid, "human_action": f.get("fix", ""), "by_system": False})
            if dec == "REQUEST_DOCUMENTATION":
                external.append({"finding": fid, "human_action": "Document first: " + f.get("document", f.get("fix", "")), "by_system": False})
            out.append({"finding": f, "kind": kind, "decision": dec, "human": human,
                        "state": state, "gate": gate, "overrides": dec == "DISMISS_FALSE_POSITIVE"})
        return out

    rows_a = handle(case.get("module_a", []), "A")
    rows_b = handle(case.get("module_b", []), "B")
    log("%s / %s" % (reviewer["name"], reviewer["role"]), "G4_signoff", case["ro_id"], after="review closed (advisory)")

    # exposure identified = sum of synthetic exposure on CONFIRMED Module A risks
    exposure_identified = sum(r["finding"].get("exposure_usd", 0) for r in rows_a if r["decision"] == "CONFIRM_RISK")
    exposure_total = sum(r["finding"].get("exposure_usd", 0) for r in rows_a)
    return {
        "case": case, "reviewer": reviewer, "module_a": rows_a, "module_b": rows_b,
        "external_actions": external, "audit": audit, "oem_adapter": OEM_ADAPTER,
        "exposure_identified": exposure_identified, "exposure_total": exposure_total,
        "module_a_note": case.get("module_a_note", ""), "module_b_note": case.get("module_b_note", ""),
        "generated": now_iso(),
    }


def portfolio_summary(cases=None):
    cases = cases or CASES
    reason_counts = Counter()
    recovery_categories = Counter()
    scenario_counts = Counter()
    exposure_by_code = defaultdict(int)
    total_exposure = 0
    total_recovery_candidates = 0
    per_ro = []
    for c in cases:
        scenario_counts[c["tag"]] += 1
        ro_exposure = 0
        for f in c.get("module_a", []):
            reason_counts[f["code"]] += 1
            exposure_by_code[f["code"]] += f.get("exposure_usd", 0)
            ro_exposure += f.get("exposure_usd", 0)
        for f in c.get("module_b", []):
            recovery_categories[f.get("category", "Other")] += 1
            total_recovery_candidates += 1
        total_exposure += ro_exposure
        per_ro.append({"ro_id": c["ro_id"], "scenario": c["scenario"], "tag": c["tag"],
                       "risk_findings": len(c.get("module_a", [])),
                       "recovery_candidates": len(c.get("module_b", [])),
                       "exposure_usd": ro_exposure})
    return {
        "n_ros": len(cases),
        "reason_counts": dict(reason_counts),
        "recovery_categories": dict(recovery_categories),
        "scenario_counts": dict(scenario_counts),
        "exposure_by_code": dict(exposure_by_code),
        "total_exposure": total_exposure,
        "total_recovery_candidates": total_recovery_candidates,
        "per_ro": per_ro,
    }

# ===== branding =====
import streamlit as st

NAVY = "#1d2226"; INK = "#20262b"; STEEL = "#6b7480"; LINE = "#e2e0da"
ACCENT = "#3e6d8e"; ACCENT_DEEP = "#2f5571"; ACCENT_TINT = "#eef3f7"
GOOD = "#3f6f57"; WARN = "#8a6d3b"; BAD = "#9a3b3b"; WARM = "#f7f5f1"

STATE_COLORS = {"Present": GOOD, "Missing": BAD, "Unclear": WARN,
                "Conflicting": "#7a4d8a", "Not Applicable": STEEL}

SHIELD_SVG = """
<svg width="40" height="44" viewBox="0 0 44 48" xmlns="http://www.w3.org/2000/svg">
  <path d="M22 1 L42 8 V25 C42 37 33 45 22 47 C11 45 2 37 2 25 V8 Z" fill="#262d33" stroke="#6b7480" stroke-width="1.4"/>
  <path d="M10 18 L18 21 L22 19 L26 21 L34 18 L26 24 L22 22 L18 24 Z" fill="#9aa3ad"/>
  <rect x="20.6" y="17" width="2.8" height="19" rx="1" fill="#9aa3ad"/>
  <circle cx="22" cy="29" r="3" fill="#3e6d8e"/>
</svg>"""

def page_config(title):
    st.set_page_config(page_title="DealerForge CLAIM — " + title, page_icon="🛡️",
                       layout="wide", initial_sidebar_state="expanded")

def inject_css():
    st.markdown(f"""<style>
    .block-container {{padding-top: 2.2rem; max-width: 1180px;}}
    h1,h2,h3,h4 {{color:{NAVY}; letter-spacing:-.01em;}}
    .df-hero {{background:linear-gradient(165deg,{NAVY},#262d33); color:#fff; border-radius:14px;
        padding:26px 30px; margin-bottom:8px;}}
    .df-hero .name {{font-size:24px; font-weight:800;}}
    .df-hero .sub {{font-size:12px; letter-spacing:.16em; text-transform:uppercase; color:#9aa3ad; margin-top:2px;}}
    .df-hero .lead {{font-size:18px; border-left:3px solid {ACCENT}; padding-left:15px; margin-top:16px;}}
    .df-hero .motto {{margin-top:11px; font-weight:600; color:#dfe6ea;}}
    .df-chip {{display:inline-block; background:{ACCENT_TINT}; border:1px solid {LINE}; color:{ACCENT_DEEP};
        border-radius:14px; padding:2px 11px; font-size:12px; font-weight:600; margin:2px 4px 2px 0;}}
    .df-safety {{background:#fff; border:1px solid {LINE}; border-left:4px solid {ACCENT};
        border-radius:10px; padding:11px 15px; font-size:13px; color:{INK};}}
    .df-card {{background:#fff; border:1px solid {LINE}; border-radius:10px; padding:15px 17px; margin-bottom:10px;}}
    .df-card.a {{border-left:4px solid {ACCENT};}} .df-card.b {{border-left:4px solid {GOOD};}}
    .df-card.over {{border-left:4px solid {BAD};}}
    .df-lbl {{font-weight:700; color:{NAVY};}} .df-muted {{color:{STEEL}; font-size:12.5px;}}
    .df-pill {{display:inline-block; color:#fff; border-radius:11px; padding:1px 9px; font-size:11px; font-weight:700;}}
    .df-state {{display:inline-block; border-radius:11px; padding:1px 9px; font-size:11px; font-weight:600; color:#fff;}}
    .df-foot {{color:{STEEL}; font-size:12px; border-top:1px solid {LINE}; margin-top:26px; padding-top:12px;}}
    div[data-testid="stMetricValue"] {{font-size:26px;}}
    </style>""", unsafe_allow_html=True)

def hero(lead, motto="Protect what you earned. Capture what you’re legitimately owed."):
    st.markdown(f"""<div class="df-hero">
      <div style="display:flex;align-items:center;gap:14px;">{SHIELD_SVG}
        <div><div class="name">DealerForge &middot; CLAIM</div>
        <div class="sub">Warranty Audit Protection &amp; Supported Recovery</div></div></div>
      <div class="lead">{lead}</div>
      <div class="motto">{motto}</div>
    </div>""", unsafe_allow_html=True)

def safety_banner():
    st.markdown("""<div class="df-safety"><b>GATE A · SYNTHETIC DATA ONLY · ADVISORY ONLY.</b>
    No real customers, vehicles, or claims. The system <b>recommends</b>; a human <b>decides</b> and
    <b>acts</b>; the OEM <b>determines</b>. It never approves, submits, determines claimability, asserts
    a dollar value, or takes any external action. Module B is always &ldquo;candidate to verify.&rdquo;</div>""",
    unsafe_allow_html=True)

def state_badge(state):
    return f'<span class="df-state" style="background:{STATE_COLORS.get(state, STEEL)}">{state}</span>'

def footer():
    st.markdown("""<div class="df-foot">DealerForge Technologies &middot; Gate A synthetic demonstration &middot;
    advisory only &middot; no real data &middot; no external action. &nbsp;&ldquo;Forged for excellence.&rdquo;<br>
    DealerForge &amp; its calibration are DealerForge IP; a pilot evaluates the tool and transfers no ownership.</div>""",
    unsafe_allow_html=True)

def sidebar_brand():
    with st.sidebar:
        st.markdown(f'<div style="display:flex;align-items:center;gap:10px;">{SHIELD_SVG}'
                    f'<b style="font-size:15px;color:{NAVY}">DealerForge</b></div>', unsafe_allow_html=True)
        st.caption("CLAIM — Warranty Audit Protection & Supported Recovery")
        st.caption("Gate A · synthetic · advisory only")


# ============================ UI (single-file multipage) ============================
A_OPTIONS = ["CONFIRM_RISK", "DISMISS_FALSE_POSITIVE", "PENDING"]
B_OPTIONS = ["APPROVE_CANDIDATE", "REQUEST_DOCUMENTATION", "REJECT", "PENDING"]


def page_overview():
    hero("An advisory tool that reads a warranty repair order <b>before submission</b> — flagging the "
         "documentation gaps that cause chargebacks, and surfacing legitimate recovery the facts support — "
         "while authorized humans keep every decision.")
    safety_banner()
    st.write("")
    c1, c2, c3 = st.columns([1.1, 1.1, 1])
    c1.metric(MARKET["service_parts_pool"], MARKET["service_parts_pool_note"])
    c2.metric(MARKET["ros_per_year"], MARKET["ros_per_year_note"])
    c3.metric("8 synthetic ROs", "supported · blocked · not-supported · clean")
    st.caption("Market context — " + MARKET["source"] +
               "  Warranty chargebacks, undocumented labor, and missed supported recovery erode gross claim by claim.")
    st.divider()
    st.subheader("The wedge: Warranty Audit Protection & Supported Recovery")
    st.write("CLAIM reviews repair orders **before submission** and closes the loop:")
    for col, (title, desc) in zip(st.columns(4), CLAIM_LOOP):
        col.markdown(f'<div class="df-card a"><div class="df-lbl">{title}</div>'
                     f'<div class="df-muted" style="margin-top:6px">{desc}</div></div>', unsafe_allow_html=True)
    st.markdown("**Strict rules:** " + "  ".join(f'<span class="df-chip">{r}</span>' for r in STRICT_RULES),
                unsafe_allow_html=True)
    st.divider()
    left, right = st.columns(2)
    with left:
        st.subheader("What it is")
        st.markdown("""
- A second set of eyes **before submission** — risk first, recovery second.
- Calibrated against a **real Stellantis/FCA warranty audit** (audit-calibrated patterns, not universal policy).
- **Human-in-the-loop:** it recommends; an authorized reviewer decides and acts; the OEM determines.
- An accountable record: who decided what, why, and when — append-only audit trail.
- **Dual mandate:** *Protect what you earned. Capture what you’re legitimately owed.*
""")
    with right:
        st.subheader("What it is **not**")
        st.markdown("""
- Not autonomous — never adjudicates, submits, or appeals a claim.
- Not integrated with CDK/DMS — no write access, no email, no money movement.
- Never says **“use this LOP,”** never asserts a dollar recovery value.
- Not a **“bill-more”** machine — “no facts, no opportunity” is a first-class outcome.
- Not proven accuracy/ROI, no OEM approval, no completed security review, not production-ready.
""")
    st.divider()
    st.subheader("A governed, multi-agent architecture")
    arch = [("Ronald", "Executive intelligence & coordination across the operation."),
            ("CLAIM", "Warranty evidence, audit protection, and supported recovery. *(this demo)*"),
            ("FORGE", "Fixed-ops process, coaching, and accountability.")]
    for col, (n, d) in zip(st.columns(3), arch):
        col.markdown(f'<div class="df-card"><div class="df-lbl">{n}</div>'
                     f'<div class="df-muted" style="margin-top:6px">{d}</div></div>', unsafe_allow_html=True)
    st.markdown('<span class="df-chip">Strict authority boundaries</span>'
                '<span class="df-chip">Full audit trails</span>'
                '<span class="df-chip">Human approval gates (G1–G5)</span>'
                '<span class="df-chip">PCS — Pilot Control System</span>', unsafe_allow_html=True)
    st.info("**Start the demo:** choose **🔎 Live Review** in the left sidebar to watch one repair order "
            "go through the dual-pass review and the human decisions.", icon="👉")


def page_live_review():
    st.markdown("## 🔎 Live Review — dual-pass, human-in-the-loop")
    safety_banner()
    labels = {c["ro_id"]: f'{c["ro_id"]}  ·  {c["scenario"]}' for c in CASES}
    ro_id = st.selectbox("Select a synthetic repair order", list(labels), format_func=lambda x: labels[x])
    case = CASE_BY_ID[ro_id]
    st.session_state.setdefault("decisions", {})
    st.session_state["decisions"].setdefault(ro_id, {})
    dec_store = st.session_state["decisions"][ro_id]
    for f in case.get("module_a", []):
        dec_store.setdefault(f["id"], default_decision("A", f))
    for f in case.get("module_b", []):
        dec_store.setdefault(f["id"], default_decision("B", f))
    _, ctb = st.columns([4, 1])
    with ctb:
        if st.button("↺ Reset to recommended", use_container_width=True):
            for f in case.get("module_a", []) + case.get("module_b", []):
                k = "A" if f in case.get("module_a", []) else "B"
                dec_store[f["id"]] = default_decision(k, f)
            st.rerun()
    v = case["vehicle"]
    st.markdown(f'<div class="df-card"><span class="df-lbl">{case["ro_id"]}</span> '
                f'&middot; <b>{v["year"]} {v["make"]} {v["model"]}</b> '
                f'&middot; VIN <code>{v["vin_token"]}</code> &middot; <span class="df-muted">{case["scenario"]}</span><br>'
                f'<b>Concern:</b> {case["concern"]}<br><b>Cause:</b> {case["cause"]}<br>'
                f'<b>Correction:</b> {case["correction"]}<br>'
                f'<span class="df-muted">Intake: manual structured input of a sanitized synthetic RO (Gate A).</span></div>',
                unsafe_allow_html=True)
    st.markdown("**Evidence** &nbsp;<span class='df-muted'>(Present · Missing · Unclear · Conflicting · Not Applicable)</span>",
                unsafe_allow_html=True)
    st.markdown(" &nbsp; ".join(f'{state_badge(e["state"])} {e["item"]}' for e in case["evidence"]),
                unsafe_allow_html=True)
    st.divider()
    rep = process_review(case, dec_store)
    st.markdown("### 🟦 Module A — Audit-Risk / Chargeback Protection  ·  *risk first*")
    if not case.get("module_a"):
        st.success(rep["module_a_note"] or "No flags found. (Not claim approval.)")
    for r in rep["module_a"]:
        f = r["finding"]; over = r["decision"] == "DISMISS_FALSE_POSITIVE"
        cls = "df-card over" if over else "df-card a"
        cc1, cc2 = st.columns([3, 1.3])
        with cc1:
            st.markdown(
                f'<div class="{cls}"><span class="df-pill" style="background:{ACCENT}">{f["code"]} · {f["label"]}</span> '
                f'<b>{f["title"]}</b><br>'
                f'<span class="df-muted">role: {f["role"]} &middot; source: {f["source"]["id"]} '
                f'({f["source"]["type"]}, {f["source"]["confidence"]})</span><br>'
                f'<b>Fix:</b> {f.get("fix","")}<br><b>Verify:</b> {f.get("verify","")}'
                + (f'<br><span class="df-muted">synthetic exposure on RO: ${f["exposure_usd"]} '
                   f'(amount at chargeback risk — not recoverable dollars)</span>' if f.get("exposure_usd") else "")
                + '</div>', unsafe_allow_html=True)
        with cc2:
            cur = dec_store[f["id"]]
            dec_store[f["id"]] = st.selectbox("Reviewer decision", A_OPTIONS, index=A_OPTIONS.index(cur),
                                              key=f"a_{ro_id}_{f['id']}", format_func=lambda d: DECISIONS[d][0])
            if dec_store[f["id"]] == "DISMISS_FALSE_POSITIVE":
                st.markdown('<span class="df-muted">⤷ human overrules the system (G3)</span>', unsafe_allow_html=True)
    st.markdown("### 🟩 Module B — Recovery Opportunity  ·  *candidate to verify*")
    if not case.get("module_b"):
        st.info(rep["module_b_note"] or "No recovery opportunity. (Not approval.)")
    for r in rep["module_b"]:
        f = r["finding"]
        cc1, cc2 = st.columns([3, 1.3])
        with cc1:
            st.markdown(
                f'<div class="df-card b"><span class="df-pill" style="background:{GOOD}">{f["label"]}</span> '
                f'<b>{f["title"]}</b><br>'
                f'<span class="df-muted">role: {f["role"]} &middot; category: {f.get("category","")} &middot; '
                f'source: {f["source"]["id"]} ({f["source"]["confidence"]})</span><br>'
                f'<b>Facts present:</b> {f.get("facts_present","")}<br>'
                f'<b>Facts missing:</b> {f.get("facts_missing","")}<br>'
                f'<b>Document:</b> {f.get("document","")}<br><b>Verify:</b> {f.get("verify","")}</div>',
                unsafe_allow_html=True)
        with cc2:
            cur = dec_store[f["id"]]
            dec_store[f["id"]] = st.selectbox("Reviewer decision", B_OPTIONS, index=B_OPTIONS.index(cur),
                                              key=f"b_{ro_id}_{f['id']}", format_func=lambda d: DECISIONS[d][0])
    rep = process_review(case, dec_store)
    st.divider()
    st.markdown("### 🧭 Human authority & audit trail")
    m1, m2, m3 = st.columns(3)
    m1.metric("Synthetic exposure identified", f"${rep['exposure_identified']}",
              help="Sum of confirmed Module-A risks. Amount already on the RO at chargeback risk — NOT recoverable dollars.")
    m2.metric("Risk findings", len(rep["module_a"]))
    m3.metric("Recovery candidates", len(rep["module_b"]))
    st.markdown(f'<div class="df-card"><b>Reviewer:</b> {rep["reviewer"]["name"]} — {rep["reviewer"]["role"]} '
                f'&nbsp; <span class="df-muted">(final authority: P. Bowers, Service Director — DEMO)</span><br>'
                f'The system <b>recommends</b>; a human <b>decides</b>; a human <b>acts</b>; the OEM '
                f'<b>determines</b>. This demo performs <b>no</b> external action.<br>'
                f'<span class="df-muted">OEM verification adapter (read-only): {rep["oem_adapter"]}</span></div>',
                unsafe_allow_html=True)
    colx, coly = st.columns(2)
    with colx:
        st.markdown("**External-action register** (human-performed, *not* by the system)")
        if rep["external_actions"]:
            for e in rep["external_actions"]:
                st.markdown(f"- `{e['finding']}` — {e['human_action']}")
        else:
            st.caption("No external actions queued.")
    with coly:
        st.markdown("**Append-only audit log** (non-sensitive labels/IDs only)")
        st.dataframe([{"event": ev["event_id"], "actor": ev["actor"], "action": ev["action"], "target": ev["target"]}
                      for ev in rep["audit"]], use_container_width=True, hide_index=True, height=240)
    md = [f"# CLAIM review — {case['ro_id']} ({case['scenario']}) [SYNTHETIC / Gate A / ADVISORY]", ""]
    for r in rep["module_a"]:
        f = r["finding"]; md.append(f"- A [{f['code']} · {f['label']}] {f['title']} — {DECISIONS[r['decision']][0]}")
    for r in rep["module_b"]:
        f = r["finding"]; md.append(f"- B [{f['label']}] {f['title']} — {DECISIONS[r['decision']][0]}")
    md.append(f"\nSynthetic exposure identified: ${rep['exposure_identified']} (not recoverable dollars).")
    st.download_button("⬇️ Export this review (Markdown)", "\n".join(md),
                       file_name=f"CLAIM_review_{ro_id}.md", mime="text/markdown")


def page_dashboard():
    st.markdown("## 📊 Executive Dashboard")
    safety_banner()
    ps = portfolio_summary()
    clean = ps["scenario_counts"].get("clean", 0)
    m = st.columns(4)
    m[0].metric("Repair orders reviewed", ps["n_ros"])
    m[1].metric("Synthetic exposure identified", f"${ps['total_exposure']:,}",
                help="Amounts already on the ROs at chargeback risk (illustrative). NOT recoverable dollars.")
    m[2].metric("Supported-recovery candidates", ps["total_recovery_candidates"],
                help="Candidates to verify — no dollar value asserted.")
    m[3].metric("Clean ROs recognized", clean)
    st.caption("Market context — " + MARKET["service_parts_pool"] + " " + MARKET["service_parts_pool_note"]
               + " · " + MARKET["ros_per_year"] + " " + MARKET["ros_per_year_note"] + ". " + MARKET["source"])
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Audit reason-code patterns flagged")
        rc = pd.DataFrame([{"code": f"{k} · {REASON_CODES[k]}", "findings": v}
                           for k, v in sorted(ps["reason_counts"].items(), key=lambda x: -x[1])]).set_index("code")
        st.bar_chart(rc, horizontal=True, color=ACCENT)
        st.caption("Audit-calibrated risk patterns (T/L/E/K/M/C/B/N) — not asserted as universal OEM policy.")
    with c2:
        st.markdown("#### Synthetic exposure by reason code")
        ex = pd.DataFrame([{"code": k, "exposure $": v} for k, v in
                           sorted(ps["exposure_by_code"].items(), key=lambda x: -x[1]) if v > 0]).set_index("code")
        st.bar_chart(ex, color=WARN)
        st.caption("Amounts already on the RO at chargeback risk (illustrative) — never recoverable dollars.")
    c3, c4 = st.columns([1.2, 1])
    with c3:
        st.markdown("#### Supported-recovery candidates by category")
        rcat = pd.DataFrame([{"category": k, "candidates": v} for k, v in
                             sorted(ps["recovery_categories"].items(), key=lambda x: -x[1])]).set_index("category")
        st.bar_chart(rcat, horizontal=True, color=GOOD)
        st.caption("Each is a 'candidate to verify' — no value asserted, no recovery guaranteed.")
    with c4:
        st.markdown("#### Outcome mix")
        sc = {"supported": "Supported", "blocked": "Documentation-blocked",
              "not_supported": "Not-supported", "clean": "Clean"}
        mix = pd.DataFrame([{"outcome": sc.get(k, k), "ROs": v} for k, v in ps["scenario_counts"].items()]).set_index("outcome")
        st.bar_chart(mix, color=ACCENT_DEEP)
    st.divider()
    st.markdown("#### Per-RO summary")
    df = pd.DataFrame(ps["per_ro"]).rename(columns={
        "ro_id": "RO", "scenario": "Scenario", "risk_findings": "Risk findings",
        "recovery_candidates": "Recovery candidates", "exposure_usd": "Synthetic exposure $"})
    st.dataframe(df[["RO", "Scenario", "Risk findings", "Recovery candidates", "Synthetic exposure $"]],
                 use_container_width=True, hide_index=True)
    st.divider()
    left, right = st.columns(2)
    with left:
        st.subheader("Why it works — proof, not assertion")
        st.markdown("""
1. **Calibrated on real audits.** Built against real completed Stellantis dealership audits — encoding actual OEM reason-code logic.
2. **Validated on unseen cases.** Tested against expert auditor findings on cases it was never trained on. Accuracy is **measured, not claimed**.
3. **Proven before rollout.** Value is established through a controlled single-store pilot before any group rollout.
""")
        st.markdown("**Strict rules:** " + "  ".join(f'<span class="df-chip">{r}</span>' for r in STRICT_RULES),
                    unsafe_allow_html=True)
    with right:
        st.subheader("Validation targets (non-guaranteed)")
        st.dataframe(pd.DataFrame([{"Measure": n, "Definition": d, "Target": t} for n, d, t in VALIDATION_TARGETS]),
                     use_container_width=True, hide_index=True, height=300)
    st.divider()
    st.subheader("The platform vision — warranty is the entry point, not the ceiling")
    for col, (i, (title, desc)) in zip(st.columns(3), enumerate(PLATFORM_VISION, 1)):
        col.markdown(f'<div class="df-card a"><div class="df-muted">0{i}</div>'
                     f'<div class="df-lbl">{title}</div>'
                     f'<div class="df-muted" style="margin-top:6px">{desc}</div></div>', unsafe_allow_html=True)
    st.markdown("**Go-to-market:** " + "  →  ".join(f'<span class="df-chip">{g}</span>' for g in GO_TO_MARKET),
                unsafe_allow_html=True)


def page_governance():
    st.markdown("## 🛡️ Governance & Safety")
    safety_banner()
    st.subheader("Authority chain (enforced, not just policy)")
    st.markdown('<span class="df-chip">System RECOMMENDS</span> → '
                '<span class="df-chip">Human DECIDES</span> → '
                '<span class="df-chip">Human ACTS</span> → '
                '<span class="df-chip">OEM DETERMINES</span>', unsafe_allow_html=True)
    st.caption("The system never decides, acts externally, or adjudicates. ReviewDecision and ExternalAction "
               "are separate records; the append-only audit log stores only non-sensitive labels/IDs.")
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Two authorization gates")
        st.markdown("""
**Gate A — Prototype build (met).** Synthetic-data-only. This demo. Authorizes no real data, live store, or external model.

**Gate B — Live pilot (not started).** Real (pseudonymized, minimum-necessary) data. A separate human
authorization requiring store approval · named humans · approved model terms · a secure external store ·
a retention rule · a named incident-response owner · an executed store-specific pilot charter.
""")
    with c2:
        st.subheader("Two data zones")
        st.markdown("""
**Restricted raw-intake zone** — sanitized source documents only, under access control, encryption,
retention/deletion, approved storage, dealer data rights, audit trail, incident response. **Outside Git.**

**Derived-analysis zone** — RO tokens, VIN last-8 or hashed, finding IDs, rule IDs, evidence states,
reviewer decisions, outcomes. No raw customer/dealer data in Git.
""")
    st.divider()
    st.subheader("Finding lifecycle & human gates (PCS)")
    st.code("intake → candidate → under_review → (supported | rejected | false_positive) → final", language="text")
    st.dataframe(pd.DataFrame([
        {"Gate": "G1", "Control": "Intake acceptance — RO admitted only after sanitization/validation."},
        {"Gate": "G2", "Control": "Candidate → human-approved opportunity — recorded approve + checklist."},
        {"Gate": "G3", "Control": "False-positive confirmation — recorded human decision."},
        {"Gate": "G4", "Control": "Final outcome / report sign-off — recorded human approval."},
        {"Gate": "G5", "Control": "Export — any output leaving the system is gated and logged; no auto-distribution."},
    ]), use_container_width=True, hide_index=True)
    st.divider()
    g1, g2 = st.columns(2)
    with g1:
        st.subheader("What it does NOT do")
        st.markdown("""
- No autonomous decisions, claim submission, appeal, or concession.
- No DMS/CDK write · no email · no money movement.
- No **“use this LOP”** · no asserted dollar recovery value.
- No “approved / claimable / submit-as-is” outside a negative disclaimer.
- No real customer data in the demo · no PII to memory.
""")
    with g2:
        st.subheader("Stop conditions (hard)")
        st.markdown("""
Halt immediately on: any PII detected · any unauthorized external action · any output reading as a
claimability decision · any **over-claim leak** (“use this LOP” / “claim more” / asserted value) ·
any auto-submit attempt · credential exposure · data outside approved scope · loss of the shutdown.
""")
    st.success("Anti-over-claim by design: **“Not supported by available facts”** and **“Documentation gap "
               "blocking recovery”** are first-class outcomes. A legitimacy filter, not a billing amplifier.")


def page_ask():
    st.markdown("## 🤝 The Ask — a controlled validation path")
    safety_banner()
    st.subheader("Phased so a clean negative result is a valid, valuable outcome")
    phases = [
        ("Phase 1 — Executive & workflow alignment",
         "Agree outcomes, stakeholders, one limited use case, the **data & security boundaries**, and the success measures. (This conversation.)"),
        ("Phase 2 — Sanitized historical validation",
         "Sanitized/synthetic ROs only; compare findings to qualified human reviewers; measure false positives/negatives, evidence completeness, usefulness. No live data."),
        ("Phase 3 — Authorized controlled pilot",
         "Only on separate written authorization, under a store-specific charter, approved data handling, named reviewers, **no autonomous claim submission**, documented exit criteria. (Behind Gate B.)"),
    ]
    for col, (t, d) in zip(st.columns(3), phases):
        col.markdown(f'<div class="df-card a"><div class="df-lbl">{t}</div>'
                     f'<div class="df-muted" style="margin-top:6px">{d}</div></div>', unsafe_allow_html=True)
    st.divider()
    st.subheader("The specific request")
    st.markdown("""
> Help define **Phase 1** — the data and security boundaries — and authorize **sanitized/synthetic
> validation** under Corporate IT's rules, with **no autonomous action, no live data until Gate B**,
> and an **immediate shutdown switch Corporate IT controls.**
""")
    st.markdown("""
**What we ask Corporate IT to provide:** an IT/Security point of contact · the approved data scope ·
(for Gate B) the model provider & terms · storage/retention/logging expectations · the reviewer access
list · the stop conditions and shutdown mechanism.

**What we are *not* asking for:** production deployment · DMS/CDK integration · authority to submit
claims or act autonomously · approval of accuracy or ROI · OEM/regulatory sign-off · live customer data.
""")
    st.divider()
    o1, o2 = st.columns(2)
    with o1:
        st.subheader("Go-to-market")
        st.markdown("  →  ".join(f'**{g}**' for g in GO_TO_MARKET))
    with o2:
        st.subheader("Ownership")
        st.markdown("""
DealerForge and its audit-calibration logic are **DealerForge IP** (Philip Bowers). A pilot lets Mac
Haik **evaluate** the tool under Corporate IT's rules and **transfers no ownership**. Any arrangement to
employ Philip to build it out, license it, or acquire it is a **separate business discussion**.
""")
    st.info("Built by a 15-year fixed-ops operator, from inside the service drive — governed multi-agent "
            "architecture, audit trails, and explicit human authority at every step.", icon="🔧")


PAGES = {
    "🏠 Overview": page_overview,
    "🔎 Live Review": page_live_review,
    "📊 Executive Dashboard": page_dashboard,
    "🛡️ Governance & Safety": page_governance,
    "🤝 The Ask": page_ask,
}


def main():
    st.set_page_config(page_title="DealerForge CLAIM — Working Demo", page_icon="🛡️",
                       layout="wide", initial_sidebar_state="expanded")
    inject_css()
    sidebar_brand()
    with st.sidebar:
        st.divider()
        choice = st.radio("Demo navigation", list(PAGES), label_visibility="collapsed")
        st.caption("Gate A · synthetic · advisory only")
    PAGES[choice]()
    footer()


if __name__ == "__main__":
    main()
