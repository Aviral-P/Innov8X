import pandas as pd
import os


# ============================================================
# 1. PATHS
# ============================================================

# Get the directory where this Python script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SOURCE_DIR = os.path.join(BASE_DIR, "source_data")
OUTPUT_DIR = os.path.join(BASE_DIR, "processed_data")

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# 2. LOAD DATASETS
# ============================================================

print("Loading datasets...")

loads = pd.read_csv(
    os.path.join(SOURCE_DIR, "loads.csv")
)

trips = pd.read_csv(
    os.path.join(SOURCE_DIR, "trips.csv")
)

delivery_events = pd.read_csv(
    os.path.join(SOURCE_DIR, "delivery_events.csv")
)

routes = pd.read_csv(
    os.path.join(SOURCE_DIR, "routes.csv")
)


# ============================================================
# 3. CONVERT EVENT DATETIME COLUMNS
# ============================================================

delivery_events["actual_datetime"] = pd.to_datetime(
    delivery_events["actual_datetime"]
)

delivery_events["scheduled_datetime"] = pd.to_datetime(
    delivery_events["scheduled_datetime"]
)


# ============================================================
# 4. EXTRACT PICKUP EVENTS
# ============================================================

pickup_events = delivery_events[
    delivery_events["event_type"].str.lower() == "pickup"
].copy()

pickup_events = pickup_events.sort_values(
    "actual_datetime"
)

# Keep only the first pickup event for each load
pickup_events = pickup_events.drop_duplicates(
    subset="load_id",
    keep="first"
)


pickup_events = pickup_events[
    [
        "load_id",
        "scheduled_datetime",
        "actual_datetime",
        "facility_id",
        "location_city",
        "location_state"
    ]
].rename(
    columns={
        "scheduled_datetime": "scheduled_pickup",
        "actual_datetime": "actual_pickup",
        "facility_id": "pickup_facility_id",
        "location_city": "pickup_city",
        "location_state": "pickup_state"
    }
)


# ============================================================
# 5. EXTRACT DELIVERY EVENTS
# ============================================================

delivery_events_only = delivery_events[
    delivery_events["event_type"].str.lower() == "delivery"
].copy()

delivery_events_only = delivery_events_only.sort_values(
    "actual_datetime"
)

# Keep only the first delivery event for each load
delivery_events_only = delivery_events_only.drop_duplicates(
    subset="load_id",
    keep="first"
)


delivery_events_only = delivery_events_only[
    [
        "load_id",
        "scheduled_datetime",
        "actual_datetime",
        "detention_minutes",
        "facility_id",
        "location_city",
        "location_state"
    ]
].rename(
    columns={
        "scheduled_datetime": "scheduled_delivery",
        "actual_datetime": "actual_delivery",
        "facility_id": "delivery_facility_id",
        "location_city": "delivery_city",
        "location_state": "delivery_state"
    }
)


# ============================================================
# 6. MERGE LOADS + TRIPS
# ============================================================

print("Combining loads and trips...")

shipments = loads.merge(
    trips[
        [
            "trip_id",
            "load_id",
            "driver_id",
            "truck_id",
            "trailer_id",
            "dispatch_date",
            "actual_distance_miles",
            "actual_duration_hours",
            "fuel_gallons_used",
            "average_mpg",
            "idle_time_hours",
            "trip_status"
        ]
    ],
    on="load_id",
    how="left"
)


# ============================================================
# 7. ADD ROUTE INFORMATION
# ============================================================

print("Adding route information...")

shipments = shipments.merge(
    routes,
    on="route_id",
    how="left"
)


# ============================================================
# 8. ADD PICKUP INFORMATION
# ============================================================

print("Adding pickup events...")

shipments = shipments.merge(
    pickup_events,
    on="load_id",
    how="left"
)


# ============================================================
# 9. ADD DELIVERY INFORMATION
# ============================================================

print("Adding delivery events...")

shipments = shipments.merge(
    delivery_events_only,
    on="load_id",
    how="left"
)


# ============================================================
# 10. CREATE OUR OWN SHIPMENT ID
# ============================================================

print("Creating shipment IDs...")

shipments.insert(
    0,
    "shipment_id",
    [
        f"SHP{i:08d}"
        for i in range(1, len(shipments) + 1)
    ]
)


# ============================================================
# 11. SELECT THE FINAL COLUMNS
# ============================================================

final_columns = [
    # -------------------------
    # IDENTIFICATION
    # -------------------------
    "shipment_id",
    "load_id",
    "trip_id",
    "customer_id",
    "route_id",

    # -------------------------
    # LOAD INFORMATION
    # -------------------------
    "load_date",
    "load_type",
    "weight_lbs",
    "pieces",

    # -------------------------
    # ROUTE INFORMATION
    # -------------------------
    "origin_city",
    "origin_state",
    "destination_city",
    "destination_state",

    # -------------------------
    # DISTANCE / RATE
    # -------------------------
    "typical_distance_miles",
    "actual_distance_miles",
    "base_rate_per_mile",
    "fuel_surcharge_rate",

    # -------------------------
    # FINANCIAL INFORMATION
    # -------------------------
    "revenue",
    "fuel_surcharge",
    "accessorial_charges",

    # -------------------------
    # PICKUP
    # -------------------------
    "scheduled_pickup",
    "actual_pickup",

    # -------------------------
    # DELIVERY
    # -------------------------
    "scheduled_delivery",
    "actual_delivery",

    # -------------------------
    # DETENTION
    # -------------------------
    "detention_minutes",

    # -------------------------
    # TRUCK / FUEL
    # -------------------------
    "fuel_gallons_used",
    "actual_duration_hours",
    "average_mpg",
    "idle_time_hours",

    # -------------------------
    # FACILITIES
    # -------------------------
    "pickup_facility_id",
    "delivery_facility_id",

    # -------------------------
    # EVENT LOCATIONS
    # -------------------------
    "pickup_city",
    "pickup_state",
    "delivery_city",
    "delivery_state"
]


# ============================================================
# 12. KEEP ONLY REQUIRED COLUMNS
# ============================================================

shipments = shipments[final_columns]


# ============================================================
# 13. BASIC DATA CLEANING
# ============================================================

print("Cleaning data...")

# Remove duplicate shipment rows
shipments = shipments.drop_duplicates(
    subset="load_id"
)

# Sort by shipment ID
shipments = shipments.sort_values(
    "shipment_id"
)


# ============================================================
# 14. VALIDATION
# ============================================================

print("\nRunning validation...")

print(
    "Number of shipments:",
    len(shipments)
)

print(
    "Number of columns:",
    len(shipments.columns)
)

print(
    "Missing trip IDs:",
    shipments["trip_id"].isna().sum()
)

print(
    "Missing route IDs:",
    shipments["route_id"].isna().sum()
)

print(
    "Missing actual distance:",
    shipments["actual_distance_miles"].isna().sum()
)

print(
    "Missing detention values:",
    shipments["detention_minutes"].isna().sum()
)


# ============================================================
# 15. SAVE SHIPMENT MASTER
# ============================================================

output_path = os.path.join(
    OUTPUT_DIR,
    "shipments.csv"
)

shipments.to_csv(
    output_path,
    index=False
)


# ============================================================
# 16. FINAL OUTPUT
# ============================================================

print("\n======================================")
print("SHIPMENT MASTER CREATED SUCCESSFULLY")
print("======================================")

print(
    f"File: {output_path}"
)

print(
    f"Rows: {len(shipments):,}"
)

print(
    f"Columns: {len(shipments.columns)}"
)

print("\nFirst 5 rows:")

print(
    shipments.head().to_string(index=False)
)