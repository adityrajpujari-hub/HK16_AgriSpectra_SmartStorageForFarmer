"""Rule-based government support eligibility suggestions.

This module provides awareness-oriented scheme suggestions based on
crop profile, location signals, risk level, and farmer category.
It is not an official validation system.
"""

from __future__ import annotations

from typing import Dict, List, Tuple


SCHEMES = {
    "PMFBY": {
        "name": "PMFBY (Pradhan Mantri Fasal Bima Yojana)",
        "purpose": "Crop insurance support for weather and post-harvest related losses.",
        "action": "Check seasonal notification, premium, and enrollment window with your state portal or CSC.",
        "link": "https://pmfby.gov.in/",
        "icon": "fa-shield-halved",
        "type": "insurance",
    },
    "PMKSY_SAMPADA": {
        "name": "PM Kisan SAMPADA Yojana",
        "purpose": "Support for post-harvest management, food processing, and cold-chain infrastructure.",
        "action": "Review eligible components and apply through implementing agencies/official portal.",
        "link": "https://www.mofpi.gov.in/en/Schemes/pradhan-mantri-kisan-sampada-yojana",
        "icon": "fa-snowflake",
        "type": "subsidy",
    },
    "MIDH": {
        "name": "Mission for Integrated Development of Horticulture (MIDH)",
        "purpose": "Support for horticulture crops including post-harvest and storage interventions.",
        "action": "Contact the district horticulture office for component-wise subsidy availability.",
        "link": "https://midh.gov.in/",
        "icon": "fa-seedling",
        "type": "subsidy",
    },
    "AIF": {
        "name": "Agriculture Infrastructure Fund (AIF)",
        "purpose": "Financing support for warehousing, cold storage, and post-harvest infrastructure.",
        "action": "Check beneficiary category and financing terms before registration.",
        "link": "https://agriinfra.dac.gov.in/",
        "icon": "fa-warehouse",
        "type": "storage",
    },
    "STATE_POST_HARVEST": {
        "name": "State-Level Post-Harvest / Storage Schemes",
        "purpose": "State-specific storage, warehouse, cold-chain, and farmer support programs.",
        "action": "Verify active schemes on your state agriculture/horticulture department website.",
        "link": "https://agriwelfare.gov.in/en/StateAgriDepartments",
        "icon": "fa-map-location-dot",
        "type": "storage",
    },
}


PERISHABLE_CROPS = {
    "banana",
    "potato",
    "onion",
    "sugarcane",
    "coffee",
    "black pepper",
}

HIGH_HUMIDITY_REGIONS = {"East", "South"}
HEAT_STRESS_REGIONS = {"West", "South"}
FLOOD_PRONE_STATES = {
    "assam",
    "bihar",
    "odisha",
    "west bengal",
    "jharkhand",
    "chhattisgarh",
}
HEAT_PRONE_STATES = {
    "rajasthan",
    "gujarat",
    "maharashtra",
    "telangana",
    "andhra pradesh",
}


def _normalize_risk_level(level: str) -> str:
    value = (level or "").strip().lower()
    if value in {"critical", "very high"}:
        return "CRITICAL"
    if value in {"high"}:
        return "HIGH"
    if value in {"moderate", "medium"}:
        return "MODERATE"
    if value in {"safe", "low"}:
        return "SAFE"
    return value.upper() or "UNKNOWN"


def _is_small_or_marginal(category: str, land_size: float | None) -> bool:
    cat = (category or "").strip().lower()
    if cat in {"small", "marginal"}:
        return True
    if land_size is not None and land_size <= 2.0:
        return True
    return False


def _safe_float(value) -> float | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return float(value)
    except Exception:
        return None


def evaluate_eligibility(payload: Dict) -> Dict:
    crop = (payload.get("crop_type") or "").strip().lower()
    region = (payload.get("region") or "").strip().title() or "North"
    state = (payload.get("state") or "").strip().lower()
    risk_level = _normalize_risk_level(payload.get("risk_level") or "")
    storage_days = int(payload.get("storage_days") or 0)
    farmer_category = (payload.get("farmer_category") or "").strip()
    land_size = _safe_float(payload.get("landholding_size"))

    schemes: Dict[str, List[str]] = {}
    checks: List[Dict] = []

    def add_scheme(code: str, reason: str):
        schemes.setdefault(code, []).append(reason)

    perishable = crop in PERISHABLE_CROPS
    high_risk = risk_level in {"HIGH", "CRITICAL"}
    humidity_or_flood = region in HIGH_HUMIDITY_REGIONS or state in FLOOD_PRONE_STATES
    heat_prone = region in HEAT_STRESS_REGIONS or state in HEAT_PRONE_STATES
    small_or_marginal = _is_small_or_marginal(farmer_category, land_size)

    checks.append({"label": "High or critical storage risk", "met": high_risk})
    checks.append({"label": "Perishable / short shelf-life crop profile", "met": perishable})
    checks.append({"label": "Humidity/flood-related regional stress", "met": humidity_or_flood})
    checks.append({"label": "Heat stress regional condition", "met": heat_prone})
    checks.append({"label": "Small & marginal farmer priority", "met": small_or_marginal})

    if high_risk:
        add_scheme("AIF", "Your storage risk is high/critical, so infrastructure support may be relevant.")
        add_scheme("PMKSY_SAMPADA", "High post-harvest risk can align with cold-chain and post-harvest support.")
        add_scheme("STATE_POST_HARVEST", "State programs often prioritize high post-harvest risk conditions.")

    if perishable:
        add_scheme("PMKSY_SAMPADA", "Perishable crops may benefit from cold-chain/post-harvest interventions.")
        add_scheme("MIDH", "Horticulture and perishable crop support may apply for storage and handling.")
        add_scheme("AIF", "Cold-storage/warehouse financing may be relevant for perishables.")

    if humidity_or_flood:
        add_scheme("PMFBY", "Flood/humidity-prone conditions increase loss risk and insurance relevance.")
        add_scheme("AIF", "Improved storage infrastructure can reduce moisture-related damage.")
        add_scheme("STATE_POST_HARVEST", "State schemes may provide local resilience support.")

    if heat_prone:
        add_scheme("PMFBY", "Heat stress can raise crop and storage loss exposure.")
        add_scheme("STATE_POST_HARVEST", "State-level support may exist for heat-stress mitigation and storage.")

    if storage_days > 90:
        add_scheme("AIF", "Long storage duration may require better storage infrastructure.")
        add_scheme("PMKSY_SAMPADA", "Longer storage windows can benefit from post-harvest management support.")

    if small_or_marginal:
        add_scheme("PMFBY", "Small/marginal farmers are often a priority in support outreach.")
        add_scheme("MIDH", "Farmer category may align with subsidy-oriented horticulture support.")
        add_scheme("AIF", "Farmer collectives and eligible categories can access infrastructure support pathways.")

    if not schemes:
        add_scheme("STATE_POST_HARVEST", "Use state agriculture portals to identify active local support programs.")
        add_scheme("PMFBY", "Insurance verification is recommended for seasonal risk management.")

    scheme_items: List[Dict] = []
    for code, reasons in schemes.items():
        base = SCHEMES[code]
        scheme_items.append(
            {
                "code": code,
                "name": base["name"],
                "purpose": base["purpose"],
                "why_eligible": " ".join(reasons),
                "recommended_next_action": base["action"],
                "official_link": base["link"],
                "icon": base["icon"],
                "type": base["type"],
            }
        )

    recommended_actions = [
        "Review the official eligibility criteria for each suggested scheme.",
        "Keep crop, land, and identity documents ready before applying.",
        "Contact your district agriculture/horticulture office or FPO for local guidance.",
    ]

    return {
        "input_summary": {
            "crop_type": payload.get("crop_type"),
            "region": region,
            "state": payload.get("state") or "Not provided",
            "risk_level": risk_level,
            "storage_days": storage_days,
            "farmer_category": farmer_category,
            "landholding_size": payload.get("landholding_size") or "Not provided",
        },
        "checks": checks,
        "possible_schemes": scheme_items,
        "recommended_actions": recommended_actions,
        "disclaimer": (
            "This eligibility check is for awareness only and does not guarantee approval. "
            "Farmers must verify details on official government portals."
        ),
    }

