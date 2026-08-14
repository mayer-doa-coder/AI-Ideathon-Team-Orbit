"""Kindwise crop.health API — real disease identification from a leaf/plant
photo, keyed by `CROP_HEALTH_API_KEY`. Uses the official `kindwise-api-client`
SDK (`CropHealthApi.identify`) rather than hand-rolled multipart requests,
per Kindwise's own guidance.

Each call deducts one identification credit from the account (100 on the
free tier) — callers must not retry this in a loop.

Raises `CropHealthAPIError` on any failure (missing key, network error, bad
response) instead of returning `None`, so a failed call can never be
silently mistaken for "no disease found" by `nodes/disease_detection.py`.
"""
import base64

from kindwise import CropHealthApi

from app.core.config import settings

DEFAULT_DETAILS = ["treatment", "description"]


class CropHealthAPIError(Exception):
    """Raised when crop.health can't be reached or returns nothing usable."""


def identify_disease(image_base64: str, details: list[str] | None = None) -> dict:
    """Runs a crop.health identification on a base64-encoded image and
    returns the raw API response as a dict — the exact shape crop.health
    itself returns (`result.disease.suggestions[]`), since `identify(...,
    as_dict=True)` hands back `response.json()` unmodified rather than the
    SDK's dataclass wrapper."""
    if not settings.crop_health_api_key:
        raise CropHealthAPIError("CROP_HEALTH_API_KEY is not configured")

    try:
        image_bytes = base64.b64decode(image_base64)
    except Exception as exc:
        raise CropHealthAPIError(f"invalid base64 image data: {exc}") from exc

    api = CropHealthApi(api_key=settings.crop_health_api_key)

    try:
        return api.identify(image_bytes, details=details or DEFAULT_DETAILS, as_dict=True)
    except Exception as exc:  # noqa: BLE001 — any SDK/HTTP failure is a hard failure here
        raise CropHealthAPIError(str(exc)) from exc


def top_candidates(raw_response: dict, limit: int = 3) -> list[dict]:
    """Extracts the top-N disease suggestions (name, confidence, treatment)
    from a raw crop.health response, ranked as the API already ranks them."""
    suggestions = ((raw_response.get("result") or {}).get("disease") or {}).get("suggestions") or []

    candidates = []
    for s in suggestions[:limit]:
        details = s.get("details") or {}
        treatment = details.get("treatment")
        if isinstance(treatment, dict):
            treatment_text = "; ".join(f"{k}: {', '.join(v)}" for k, v in treatment.items() if v)
        else:
            treatment_text = treatment or ""

        candidates.append(
            {
                "disease_name": s.get("name", "unknown"),
                "confidence": s.get("probability", 0.0),
                "treatment": treatment_text,
            }
        )
    return candidates
