"""Seeded supplier catalog search + ranking — the Tier 2 marketplace
capability. Queries the `suppliers`/`supplier_products` Postgres tables
directly (see `db/models.py`); this data is never chunked/embedded, so it
stays entirely outside the RAG path in `rag/qa.py` and `tools/rag.py`.

Ranking is a transparent weighted sum over normalized signals, not an
optimizer — deliberately simple so it's easy to retune (`RANK_WEIGHTS`) or
swap a signal for a smarter one later (e.g. real drive-time instead of
haversine distance) without touching the node that calls this module.

When no supplier lists the product in the farmer's requested district, we
switch ranking modes rather than silently blending price/rating in as a
substitute for locality: `rank_by_distance` picks the genuinely nearest
match by haversine distance from a reference point (the farm's own
coordinates, or the requested district's, geocoded by the caller — this
module does no HTTP itself, same separation as `tools/weather.py` vs
`tools/financials.py`). If no reference point is available either, we say
so explicitly instead of presenting a price-ranked list as if it were
proximity-ranked.
"""
import math
from dataclasses import dataclass, field

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models import Supplier, SupplierProduct

# Weights must sum to 1.0. distance/stock only contribute when the farmer
# gave a location / quantity to compare against — see _normalize below.
RANK_WEIGHTS = {
    "price": 0.35,
    "distance": 0.25,
    "rating": 0.20,
    "delivery": 0.10,
    "stock": 0.10,
}

EARTH_RADIUS_KM = 6371.0


@dataclass
class SupplierOffer:
    supplier_id: int
    business_name: str
    district: str
    address: str | None
    phone: str | None
    product_name: str
    unit: str
    price_bdt_per_unit: float
    stock_available: float
    delivery_days: int
    rating: float
    last_updated: str
    distance_km: float | None
    score: float = 0.0
    reasons: list[str] = field(default_factory=list)


@dataclass
class MarketplaceSearchResult:
    offers: list[SupplierOffer]
    # False whenever `offers` came from outside the requested district
    # (either ranked by real distance, or — if no reference point was
    # available — by price/rating with that caveat surfaced to the caller).
    matched_district: bool
    # True only when the fallback offers are genuinely ranked nearest-first.
    ranked_by_distance: bool


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _normalize(values: list[float], higher_is_better: bool) -> list[float]:
    """Min-max normalize to [0, 1]. All-equal inputs score 1.0 for everyone
    (no signal to differentiate on, so it shouldn't penalize anyone)."""
    lo, hi = min(values), max(values)
    if hi == lo:
        return [1.0] * len(values)
    return [
        (v - lo) / (hi - lo) if higher_is_better else (hi - v) / (hi - lo)
        for v in values
    ]


def find_supplier_offers(
    db: Session,
    product: str,
    district: str | None = None,
    limit: int = 25,
) -> tuple[list[SupplierProduct], bool]:
    """Fuzzy match on product name OR category, joined with the supplier
    row. Matching category too means a generic term like "fertilizer" or
    "pesticide" finds everything in that category even when individual
    listings use a specific formulation name (e.g. "Cypermethrin 10EC")
    that doesn't literally contain the word "pesticide".

    Returns `(offers, matched_district)`. `matched_district` is True when
    either the returned rows are actually in the requested district, or no
    district was requested at all (nothing to fail to match, so it's not a
    fallback). It's only False when the farmer asked for a district and
    none of the matching rows are in it — the caller then ranks that
    fallback set honestly (see `rank_by_distance`) instead of presenting it
    as if it were local.
    """
    term = f"%{product}%"
    q = (
        db.query(SupplierProduct)
        .join(Supplier, SupplierProduct.supplier_id == Supplier.id)
        .filter(or_(SupplierProduct.product_name.ilike(term), SupplierProduct.category.ilike(term)))
    )

    if not district:
        return q.limit(limit).all(), True

    in_district = q.filter(Supplier.district.ilike(f"%{district}%")).limit(limit).all()
    if in_district:
        return in_district, True

    return q.limit(limit).all(), False


def rank_offers(
    offers: list[SupplierProduct],
    quantity: float | None = None,
    ref_lat: float | None = None,
    ref_lon: float | None = None,
) -> list[SupplierOffer]:
    """Score + explain each raw catalog row by a weighted blend of price,
    rating, delivery, stock, and distance-if-known. Returns best-first."""
    if not offers:
        return []

    have_ref = ref_lat is not None and ref_lon is not None
    distances = (
        [_haversine_km(ref_lat, ref_lon, o.supplier.lat, o.supplier.lon) for o in offers]
        if have_ref and all(o.supplier.lat is not None for o in offers)
        else None
    )

    prices = [o.price_bdt_per_unit for o in offers]
    ratings = [o.supplier.rating for o in offers]
    deliveries = [o.delivery_days for o in offers]
    avg_price = sum(prices) / len(prices)

    price_scores = _normalize(prices, higher_is_better=False)
    rating_scores = _normalize(ratings, higher_is_better=True)
    delivery_scores = _normalize(deliveries, higher_is_better=False)
    distance_scores = _normalize(distances, higher_is_better=False) if distances else [1.0] * len(offers)

    # With no reference point to compare against, distance can't score
    # anything — redistribute its weight to price+rating so scores still
    # sum to 1.0 instead of silently underweighting every offer.
    weights = dict(RANK_WEIGHTS)
    if distances is None:
        redistributed = weights.pop("distance")
        weights["price"] += redistributed / 2
        weights["rating"] += redistributed / 2

    ranked: list[SupplierOffer] = []
    for i, o in enumerate(offers):
        stock_ok = quantity is None or o.stock_available >= quantity
        stock_score = 1.0 if stock_ok else max(0.2, o.stock_available / quantity) if quantity else 1.0

        score = (
            price_scores[i] * weights["price"]
            + rating_scores[i] * weights["rating"]
            + delivery_scores[i] * weights["delivery"]
            + stock_score * weights["stock"]
            + (distance_scores[i] * weights["distance"] if distances else 0)
        )

        reasons = []
        if price_scores[i] >= 0.99:
            reasons.append(f"lowest price found (৳{o.price_bdt_per_unit:.0f}/{o.unit} vs avg ৳{avg_price:.0f})")
        if distances and distances[i] == min(distances):
            # Use the same rounding as the displayed distance_km (below) so
            # the reason text and the offer line never disagree by 1 km.
            reasons.append(f"closest option ({round(distances[i], 1):.0f} km away)")
        if rating_scores[i] >= 0.99 and len(set(ratings)) > 1:
            reasons.append(f"highest-rated supplier ({o.supplier.rating:.1f}/5)")
        if delivery_scores[i] >= 0.99 and len(set(deliveries)) > 1:
            reasons.append(f"fastest delivery ({o.delivery_days}d)")
        if quantity and not stock_ok:
            reasons.append(f"only {o.stock_available:.0f}{o.unit} in stock — short of the {quantity:.0f}{o.unit} needed")
        elif quantity:
            reasons.append(f"stock covers your {quantity:.0f}{o.unit} request")
        if not reasons:
            reasons.append(f"rated {o.supplier.rating:.1f}/5, delivers in {o.delivery_days}d")

        ranked.append(
            SupplierOffer(
                supplier_id=o.supplier.id,
                business_name=o.supplier.business_name,
                district=o.supplier.district,
                address=o.supplier.address,
                phone=o.supplier.phone,
                product_name=o.product_name,
                unit=o.unit,
                price_bdt_per_unit=o.price_bdt_per_unit,
                stock_available=o.stock_available,
                delivery_days=o.delivery_days,
                rating=o.supplier.rating,
                last_updated=o.last_updated.isoformat() if o.last_updated else "",
                distance_km=round(distances[i], 1) if distances else None,
                score=round(score, 4),
                reasons=reasons,
            )
        )

    ranked.sort(key=lambda offer: offer.score, reverse=True)
    return ranked


def rank_by_distance(
    offers: list[SupplierProduct],
    ref_lat: float,
    ref_lon: float,
    quantity: float | None = None,
) -> list[SupplierOffer]:
    """Nearest-first ranking, used specifically when no supplier lists the
    product in the farmer's requested district. Distance is the sort key —
    not one signal blended among several — so "nearest supplier" actually
    means nearest, not a generalized best-deal pick that happens to be far
    away. Offers whose supplier has no coordinates are excluded (there's no
    honest distance to report for them)."""
    with_coords = [o for o in offers if o.supplier.lat is not None and o.supplier.lon is not None]
    if not with_coords:
        return []

    distances = [_haversine_km(ref_lat, ref_lon, o.supplier.lat, o.supplier.lon) for o in with_coords]
    order = sorted(range(len(with_coords)), key=lambda i: distances[i])
    distance_scores = _normalize(distances, higher_is_better=False)

    ranked: list[SupplierOffer] = []
    for rank, i in enumerate(order):
        o = with_coords[i]
        stock_ok = quantity is None or o.stock_available >= quantity

        # Same rounding as the displayed distance_km (below), so the reason
        # text and the offer line never disagree by 1 km.
        d_display = round(distances[i], 1)
        reasons = [
            f"nearest available supplier ({d_display:.0f} km away)"
            if rank == 0
            else f"next-nearest option ({d_display:.0f} km away)"
        ]
        if quantity and not stock_ok:
            reasons.append(f"only {o.stock_available:.0f}{o.unit} in stock — short of the {quantity:.0f}{o.unit} needed")
        elif quantity:
            reasons.append(f"stock covers your {quantity:.0f}{o.unit} request")

        ranked.append(
            SupplierOffer(
                supplier_id=o.supplier.id,
                business_name=o.supplier.business_name,
                district=o.supplier.district,
                address=o.supplier.address,
                phone=o.supplier.phone,
                product_name=o.product_name,
                unit=o.unit,
                price_bdt_per_unit=o.price_bdt_per_unit,
                stock_available=o.stock_available,
                delivery_days=o.delivery_days,
                rating=o.supplier.rating,
                last_updated=o.last_updated.isoformat() if o.last_updated else "",
                distance_km=round(distances[i], 1),
                score=round(distance_scores[i], 4),
                reasons=reasons,
            )
        )

    return ranked


def search_and_rank_suppliers(
    db: Session,
    product: str,
    district: str | None = None,
    quantity: float | None = None,
    ref_lat: float | None = None,
    ref_lon: float | None = None,
) -> MarketplaceSearchResult:
    """`ref_lat`/`ref_lon` is whatever point distance should be measured
    from — the farmer's own farm coordinates if known, or the requested
    district's geocoded coordinates otherwise (the caller resolves this;
    see `agents/nodes/marketplace_lookup.py`, which reuses the same
    `tools/weather.geocode_location` the weather node already calls)."""
    offers, matched_district = find_supplier_offers(db, product=product, district=district)
    if not offers:
        return MarketplaceSearchResult(offers=[], matched_district=False, ranked_by_distance=False)

    if district and not matched_district:
        have_ref = ref_lat is not None and ref_lon is not None
        if have_ref:
            nearest = rank_by_distance(offers, ref_lat, ref_lon, quantity=quantity)
            if nearest:
                return MarketplaceSearchResult(offers=nearest, matched_district=False, ranked_by_distance=True)
        # No usable reference point (or no supplier had coordinates) — be
        # honest that this is a price/rating fallback, not a proximity one.
        return MarketplaceSearchResult(
            offers=rank_offers(offers, quantity=quantity, ref_lat=ref_lat, ref_lon=ref_lon),
            matched_district=False,
            ranked_by_distance=False,
        )

    return MarketplaceSearchResult(
        offers=rank_offers(offers, quantity=quantity, ref_lat=ref_lat, ref_lon=ref_lon),
        matched_district=matched_district,
        ranked_by_distance=False,
    )
