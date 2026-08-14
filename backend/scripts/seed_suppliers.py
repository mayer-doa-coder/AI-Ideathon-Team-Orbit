"""CLI: seed the mock supplier catalog for the Tier 2 marketplace feature.

Clears and re-inserts every run, so the catalog can be freely edited here
and reseeded during development/demo without worrying about duplicates.
This is the hackathon's allowed seeded/mock catalog, not a live feed —
swap the query layer in `app/tools/marketplace.py` for a real supplier API
later without touching the agent node that calls it.

Data-design notes (from a realism audit — see conversation history):
- Prices are anchored close to `tools/financials.py`'s reference fertilizer
  prices (Urea 27, TSP 34, MoP 27, DAP 30, Gypsum 14, Zinc Sulphate 220,
  Boric Acid 240 BDT/kg), with natural ±5-20% spread across districts —
  real retail fertilizer prices vary this much on transport/dealer margin.
- Every district has at least 2 suppliers where the catalog needs to
  demonstrate real ranking/comparison; single-supplier districts are ones
  where that's realistic too (e.g. a specialist nursery town).
- Covers all 8 divisions of Bangladesh, not just the northern rice belt.
- Ratings, stock, delivery time, and `last_updated` are deliberately
  uneven — including one genuinely out-of-stock listing and one stale
  (rarely-updated) shop — rather than uniformly "good" placeholder values.
- Pesticide/fungicide names use real BD agrochemical formulation codes
  (e.g. "Cypermethrin 10EC", "Mancozeb 80WP") instead of ad hoc "Pesticide -
  X" prefixes — both more authentic and consistently matchable via the
  product/category search in `tools/marketplace.py`.

Usage (from the backend/ venv):
    python -m scripts.seed_suppliers
"""
from datetime import datetime, timedelta, timezone

from app.db.models import Supplier, SupplierProduct
from app.db.session import SessionLocal

NOW = datetime.now(timezone.utc)


def _days_ago(n: int) -> datetime:
    return NOW - timedelta(days=n)


SUPPLIERS = [
    # --- Rajshahi (2 suppliers: strong central-bazar dealer + smaller shop) ---
    {
        "business_name": "Shaheb Bazar Krishi Bhandar",
        "district": "Rajshahi",
        "address": "Shaheb Bazar, Rajshahi",
        "lat": 24.3729,
        "lon": 88.6041,
        "phone": "01712-847215",
        "rating": 4.5,
        "products": [
            {"product_name": "Urea", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 27, "stock_available": 4800, "delivery_days": 0, "days_ago": 1},
            {"product_name": "TSP", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 35, "stock_available": 2600, "delivery_days": 1, "days_ago": 2},
            {"product_name": "MoP", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 28, "stock_available": 1900, "delivery_days": 1, "days_ago": 4},
            {"product_name": "BRRI Dhan28 Rice Seed", "category": "seed", "unit": "kg", "price_bdt_per_unit": 58, "stock_available": 700, "delivery_days": 1, "days_ago": 6},
        ],
    },
    {
        "business_name": "Al-Amin Agro House",
        "district": "Rajshahi",
        "address": "Rajshahi College Road, Rajshahi",
        "lat": 24.3653,
        "lon": 88.6238,
        "phone": "01812-556930",
        "rating": 3.8,
        "products": [
            {"product_name": "Urea", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 29, "stock_available": 950, "delivery_days": 2, "days_ago": 9},
            {"product_name": "Cypermethrin 10EC", "category": "pesticide", "unit": "litre", "price_bdt_per_unit": 385, "stock_available": 45, "delivery_days": 2, "days_ago": 9},
            {"product_name": "Cabbage Seed (BARI Cabbage-1)", "category": "seed", "unit": "kg", "price_bdt_per_unit": 3800, "stock_available": 8, "delivery_days": 3, "days_ago": 12},
        ],
    },
    # --- Bogura (2 suppliers: major potato/rice hub, worth real competition) ---
    {
        "business_name": "Bogura Bus Stand Agro Bhandar",
        "district": "Bogura",
        "address": "Bus Stand Bazar, Bogura",
        "lat": 24.8465,
        "lon": 89.3773,
        "phone": "01911-402278",
        "rating": 4.7,
        "products": [
            {"product_name": "Urea", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 25, "stock_available": 4200, "delivery_days": 0, "days_ago": 1},
            {"product_name": "DAP", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 31, "stock_available": 2400, "delivery_days": 0, "days_ago": 1},
            {"product_name": "MoP", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 27, "stock_available": 1750, "delivery_days": 1, "days_ago": 3},
            {"product_name": "Cypermethrin 10EC", "category": "pesticide", "unit": "litre", "price_bdt_per_unit": 350, "stock_available": 85, "delivery_days": 1, "days_ago": 2},
            {"product_name": "Boric Acid", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 230, "stock_available": 95, "delivery_days": 3, "days_ago": 10},
            # Genuinely out of stock — realistic during peak potato-planting season (Nov-Dec),
            # and demonstrates the ranking logic's honest stock-shortfall handling.
            {"product_name": "Potato Seed (BARI/Diamant)", "category": "seed", "unit": "kg", "price_bdt_per_unit": 45, "stock_available": 0, "delivery_days": 5, "days_ago": 1},
        ],
    },
    {
        "business_name": "Sherpur Road Krishi Ghar",
        "district": "Bogura",
        "address": "Sherpur Road, Bogura",
        "lat": 24.8520,
        "lon": 89.3650,
        "phone": "01715-903364",
        "rating": 4.0,
        "products": [
            {"product_name": "Urea", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 26, "stock_available": 3100, "delivery_days": 1, "days_ago": 3},
            {"product_name": "TSP", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 34, "stock_available": 1400, "delivery_days": 2, "days_ago": 5},
            {"product_name": "Potato Seed (BARI/Diamant)", "category": "seed", "unit": "kg", "price_bdt_per_unit": 48, "stock_available": 1200, "delivery_days": 1, "days_ago": 2},
        ],
    },
    # --- Rangpur (2 suppliers) ---
    {
        "business_name": "Rangpur Station Road Krishi Bhandar",
        "district": "Rangpur",
        "address": "Station Road, Rangpur",
        "lat": 25.7439,
        "lon": 89.2752,
        "phone": "01614-772091",
        "rating": 4.4,
        "products": [
            {"product_name": "Urea", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 28, "stock_available": 2600, "delivery_days": 1, "days_ago": 2},
            {"product_name": "TSP", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 33, "stock_available": 1700, "delivery_days": 2, "days_ago": 4},
            {"product_name": "Zinc Sulphate", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 215, "stock_available": 280, "delivery_days": 3, "days_ago": 8},
            {"product_name": "BRRI Dhan29 Rice Seed", "category": "seed", "unit": "kg", "price_bdt_per_unit": 60, "stock_available": 900, "delivery_days": 1, "days_ago": 3},
        ],
    },
    {
        "business_name": "Dhap Bazar Agro Center",
        "district": "Rangpur",
        "address": "Dhap, Rangpur",
        "lat": 25.7580,
        "lon": 89.2445,
        "phone": "01518-337750",
        "rating": 3.5,
        "products": [
            {"product_name": "Urea", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 30, "stock_available": 600, "delivery_days": 2, "days_ago": 11},
            {"product_name": "Potato Seed (BARI/Diamant)", "category": "seed", "unit": "kg", "price_bdt_per_unit": 41, "stock_available": 500, "delivery_days": 2, "days_ago": 6},
        ],
    },
    # --- Dhaka (2 suppliers — placed in the district's actual farming
    # upazilas, Savar and Dhamrai, not deep urban Dhaka) ---
    {
        "business_name": "Savar Krishi Upokoron Bhandar",
        "district": "Dhaka",
        "address": "Bazar Road, Savar, Dhaka",
        "lat": 23.8583,
        "lon": 90.2667,
        "phone": "01722-119483",
        "rating": 4.3,
        "products": [
            {"product_name": "DAP", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 32, "stock_available": 3600, "delivery_days": 1, "days_ago": 2},
            {"product_name": "Urea", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 30, "stock_available": 5200, "delivery_days": 0, "days_ago": 1},
            {"product_name": "Mancozeb 80WP", "category": "pesticide", "unit": "kg", "price_bdt_per_unit": 420, "stock_available": 130, "delivery_days": 2, "days_ago": 5},
            {"product_name": "Hybrid Maize Seed", "category": "seed", "unit": "kg", "price_bdt_per_unit": 245, "stock_available": 420, "delivery_days": 2, "days_ago": 7},
        ],
    },
    {
        "business_name": "Dhamrai Agro Traders",
        "district": "Dhaka",
        "address": "Dhamrai Bazar, Dhaka",
        "lat": 23.9088,
        "lon": 90.2273,
        "phone": "01823-660512",
        "rating": 4.1,
        "products": [
            {"product_name": "Urea", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 31, "stock_available": 1800, "delivery_days": 1, "days_ago": 4},
            {"product_name": "Imidacloprid 20SL", "category": "pesticide", "unit": "litre", "price_bdt_per_unit": 405, "stock_available": 55, "delivery_days": 2, "days_ago": 6},
        ],
    },
    # --- Khulna (1 supplier — coastal district, cooperative-store naming
    # is a common real pattern here) ---
    {
        "business_name": "Khulna Sadar Krishi Samabay Bhandar",
        "district": "Khulna",
        "address": "Khulna Sadar",
        "lat": 22.8456,
        "lon": 89.5403,
        "phone": "01916-284057",
        "rating": 3.9,
        "products": [
            {"product_name": "Urea", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 26, "stock_available": 3300, "delivery_days": 2, "days_ago": 5},
            {"product_name": "Gypsum", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 15, "stock_available": 2100, "delivery_days": 2, "days_ago": 9},
            {"product_name": "Imidacloprid 20SL", "category": "pesticide", "unit": "litre", "price_bdt_per_unit": 410, "stock_available": 38, "delivery_days": 3, "days_ago": 7},
        ],
    },
    # --- Cumilla (1 supplier — real major potato/vegetable district;
    # fungicide paired with potato seed reflects the real late-blight risk) ---
    {
        "business_name": "Kandirpar Krishi Bhandar",
        "district": "Cumilla",
        "address": "Kandirpar, Cumilla",
        "lat": 23.4633,
        "lon": 91.1800,
        "phone": "01717-528890",
        "rating": 4.2,
        "products": [
            {"product_name": "Potato Seed (BARI/Diamant)", "category": "seed", "unit": "kg", "price_bdt_per_unit": 44, "stock_available": 1600, "delivery_days": 1, "days_ago": 2},
            {"product_name": "Mancozeb 80WP", "category": "pesticide", "unit": "kg", "price_bdt_per_unit": 415, "stock_available": 110, "delivery_days": 1, "days_ago": 3},
            {"product_name": "TSP", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 36, "stock_available": 1500, "delivery_days": 1, "days_ago": 4},
            {"product_name": "Urea", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 29, "stock_available": 2200, "delivery_days": 1, "days_ago": 3},
        ],
    },
    # --- Mymensingh (1 supplier — general rice/jute belt dealer) ---
    {
        "business_name": "Mymensingh Notun Bazar Krishi Ghar",
        "district": "Mymensingh",
        "address": "Notun Bazar, Mymensingh",
        "lat": 24.7471,
        "lon": 90.4203,
        "phone": "01611-773402",
        "rating": 4.0,
        "products": [
            {"product_name": "Urea", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 27, "stock_available": 2900, "delivery_days": 1, "days_ago": 3},
            {"product_name": "DAP", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 31, "stock_available": 1600, "delivery_days": 2, "days_ago": 6},
            {"product_name": "BRRI Dhan49 Rice Seed", "category": "seed", "unit": "kg", "price_bdt_per_unit": 55, "stock_available": 750, "delivery_days": 1, "days_ago": 4},
        ],
    },
    # --- Sylhet (1 supplier, deliberately smaller catalog — haor/tea
    # region is less fertilizer-intensive than the northern rice belt, and
    # remoter river/hill logistics from Dhaka wholesale push prices up a
    # little and delivery out a little, same pattern as Barisal below) ---
    {
        "business_name": "Sylhet Ambarkhana Krishi Bhandar",
        "district": "Sylhet",
        "address": "Ambarkhana, Sylhet",
        "lat": 24.8998,
        "lon": 91.8687,
        "phone": "01319-664821",
        "rating": 3.6,
        "products": [
            {"product_name": "Urea", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 30, "stock_available": 900, "delivery_days": 3, "days_ago": 10},
            {"product_name": "MoP", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 29, "stock_available": 400, "delivery_days": 3, "days_ago": 12},
        ],
    },
    # --- Jashore (1 supplier — Jhikargacha upazila is Bangladesh's real
    # nursery/vegetable-seed hub; a pure seed specialist with no
    # fertilizer/pesticide at all is the realistic shape for this town.
    # Hybrid vegetable seed genuinely prices in the thousands-to-tens-of-
    # thousands BDT/kg range since seed is sold by the gram, not the kg. ) ---
    {
        "business_name": "Jhikargacha Nursery & Seed House",
        "district": "Jashore",
        "address": "Jhikargacha, Jashore",
        "lat": 23.0965,
        "lon": 89.1439,
        "phone": "01914-408215",
        "rating": 4.6,
        "products": [
            {"product_name": "Hybrid Tomato Seed (BARI Tomato-14)", "category": "seed", "unit": "kg", "price_bdt_per_unit": 18500, "stock_available": 3, "delivery_days": 2, "days_ago": 2},
            {"product_name": "Hybrid Chili Seed", "category": "seed", "unit": "kg", "price_bdt_per_unit": 42000, "stock_available": 1, "delivery_days": 3, "days_ago": 5},
            {"product_name": "Cabbage Seed (BARI Cabbage-1)", "category": "seed", "unit": "kg", "price_bdt_per_unit": 3600, "stock_available": 6, "delivery_days": 1, "days_ago": 1},
            {"product_name": "Hybrid Cucumber Seed", "category": "seed", "unit": "kg", "price_bdt_per_unit": 9500, "stock_available": 4, "delivery_days": 2, "days_ago": 4},
        ],
    },
    # --- Barisal (1 supplier — southern rice belt; river-transport
    # logistics from Dhaka wholesale realistically push prices up a bit
    # and delivery out a bit, same reasoning as Sylhet above) ---
    {
        "business_name": "Barisal Band Road Krishi Bhandar",
        "district": "Barisal",
        "address": "Band Road, Barisal",
        "lat": 22.7010,
        "lon": 90.3535,
        "phone": "01777-215690",
        "rating": 3.7,
        "products": [
            {"product_name": "Urea", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 30, "stock_available": 1500, "delivery_days": 3, "days_ago": 8},
            {"product_name": "MoP", "category": "fertilizer", "unit": "kg", "price_bdt_per_unit": 29, "stock_available": 700, "delivery_days": 3, "days_ago": 9},
        ],
    },
]


def main() -> None:
    db = SessionLocal()
    try:
        db.query(SupplierProduct).delete()
        db.query(Supplier).delete()
        db.commit()

        for entry in SUPPLIERS:
            supplier = Supplier(
                business_name=entry["business_name"],
                district=entry["district"],
                address=entry["address"],
                lat=entry["lat"],
                lon=entry["lon"],
                phone=entry["phone"],
                rating=entry["rating"],
            )
            db.add(supplier)
            db.flush()

            for product in entry["products"]:
                days_ago = product.pop("days_ago")
                db.add(SupplierProduct(supplier_id=supplier.id, last_updated=_days_ago(days_ago), **product))

        db.commit()

        supplier_count = len(SUPPLIERS)
        product_count = sum(len(s["products"]) for s in SUPPLIERS)
        district_count = len({s["district"] for s in SUPPLIERS})
        print(f"Seeded {supplier_count} suppliers ({district_count} districts) with {product_count} product listings.")
        print("Try it: ask the chat agent \"where can I buy urea near Rajshahi?\"")
    finally:
        db.close()


if __name__ == "__main__":
    main()
