# `invoices_with_errors.csv`

## Overview

`invoices_with_errors.csv` is the **synthetic test dataset** created for the AI Freight Invoice Auditor.

It is generated from the clean `invoices.csv` dataset by injecting controlled, realistic billing errors into a subset of freight invoices.

The purpose of this dataset is to provide invoices that the future **Audit Engine** can analyze and compare against contractual and shipment-level evidence.

---

## Dataset Statistics

| Metric                                   |         Value |
| ---------------------------------------- | ------------: |
| Total invoices                           |        85,410 |
| Invoices with injected errors            |        12,811 |
| Clean invoices                           |        72,599 |
| Error rate                               |          ~15% |
| Total injected overcharge                | $2,859,118.79 |
| Average overcharge per erroneous invoice |         ~$223 |

The dataset was generated using a fixed random seed (`42`) so that the same error distribution can be reproduced.

---

## Error Types

Five types of billing errors are currently injected.

### 1. Rate Error

The billed base freight charge is increased by **10%** above the original calculated base charge.

Example:

```text
Correct base charge:  $2,000
Billed base charge:   $2,200
Overcharge:             $200
```

---

### 2. Fuel Surcharge Error

The calculated fuel surcharge is increased by **20%**.

Example:

```text
Correct fuel surcharge:  $500
Billed surcharge:        $600
Overcharge:              $100
```

---

### 3. Detention Error

An additional **$100 detention charge** is injected.

The purpose is to simulate a detention charge that is not supported by the contractual calculation.

---

### 4. Accessorial Error

An existing accessorial charge is duplicated.

For example:

```text
Original accessorial:  $150
Billed accessorial:    $300
Overcharge:            $150
```

If an invoice has no existing accessorial charge, a synthetic `$75` charge is introduced.

---

### 5. Distance Error

The billed distance is increased by **15%**.

This represents a carrier billing more mileage than the shipment's recorded distance.

> **Important:** In the current version of the generator, `actual_distance_miles` is modified when this error is injected. This should be corrected in a later version by separating `actual_distance_miles` from `billed_distance_miles`.

---

## Error Distribution

The current generated dataset contains approximately:

| Error Type           |   Invoices |
| -------------------- | ---------: |
| Distance error       |      2,597 |
| Rate error           |      2,596 |
| Detention error      |      2,577 |
| Fuel surcharge error |      2,540 |
| Accessorial error    |      2,501 |
| **Total**            | **12,811** |

The distribution is approximately balanced because the error type is randomly selected from the five available error categories.

---

## Important Columns

### Identification

| Column        | Description                                |
| ------------- | ------------------------------------------ |
| `invoice_id`  | Unique invoice identifier                  |
| `shipment_id` | Shipment associated with the invoice       |
| `load_id`     | Original load identifier                   |
| `customer_id` | Customer associated with the shipment      |
| `route_id`    | Route associated with the shipment         |
| `contract_id` | Contract rule used for calculating charges |

### Shipment / Billing Information

| Column                           | Description                                         |
| -------------------------------- | --------------------------------------------------- |
| `actual_distance_miles`          | Shipment distance used by the current invoice model |
| `base_rate_per_mile`             | Contractual rate per mile                           |
| `calculated_base_charge`         | Base freight charge                                 |
| `fuel_surcharge_rate`            | Contractual fuel surcharge rate                     |
| `calculated_fuel_surcharge`      | Fuel surcharge                                      |
| `detention_minutes`              | Recorded detention time                             |
| `detention_free_minutes`         | Contractual free detention period                   |
| `detention_rate_per_hour`        | Detention charge rate                               |
| `calculated_detention_charge`    | Detention charge                                    |
| `calculated_accessorial_charges` | Accessorial charges                                 |
| `calculated_subtotal`            | Sum of calculated charges                           |
| `minimum_charge`                 | Contractual minimum charge                          |
| `expected_total`                 | Total invoice amount after injected modifications   |
| `billed_amount`                  | Amount presented as billed                          |

### Error Ground-Truth Metadata

| Column                  | Description                                      |
| ----------------------- | ------------------------------------------------ |
| `has_injected_error`    | Whether an artificial billing error was injected |
| `injected_error_type`   | Type of injected billing error                   |
| `injected_error_amount` | Amount of overcharge introduced by the generator |

---

## Data Generation Pipeline

This dataset is part of the following pipeline:

```text
Original Operational Data
        ↓
Shipment Master
        ↓
Contract / Rate Rules
        ↓
Clean Freight Invoices
        ↓
Inject Billing Errors
        ↓
invoices_with_errors.csv
        ↓
Ground Truth
        ↓
Audit Engine
```

---

## Source Datasets

The clean invoice dataset was generated from:

```text
data/processed_data/shipments.csv
data/processed_data/contract_rules.csv
```

The shipment master itself was created from the original operational datasets, including:

```text
loads.csv
trips.csv
routes.csv
delivery_events.csv
```

---

## Purpose in the AI Freight Invoice Auditor

This dataset acts as the **controlled testing environment** for the audit system.

The future audit engine will attempt to identify discrepancies without directly relying on:

```text
has_injected_error
injected_error_type
injected_error_amount
```

Those columns are **ground-truth labels** and should only be used for evaluating the auditor's performance.

The intended architecture is:

```text
Invoice
   +
Contract Rules
   +
Shipment Evidence
   +
Delivery Evidence
   ↓
Audit Engine
   ↓
Detected Discrepancy
   ↓
Evidence
   ↓
Explanation
   ↓
Confidence Score
```

---

## Reproducibility

The error injection script uses:

```python
np.random.seed(42)
```

Therefore, the same source invoice dataset and generation code should produce the same error selection and distribution.

---

## Important Limitation

This is a **synthetic error-injection dataset**, not a collection of real fraudulent invoices.

The injected errors are designed to represent realistic freight billing discrepancies for:

* model development
* rule-engine testing
* anomaly detection
* evaluation
* hackathon demonstration

The synthetic contract parameters should therefore be clearly distinguished from values directly obtained from the original operational datasets.

---

## Next Step

The next stage is **Step 5 — Ground Truth Creation**.

Ground truth will establish, for every invoice:

```text
Correct contractual amount
        ↓
Actual billed amount
        ↓
Difference
        ↓
Error category
        ↓
Overcharge amount
        ↓
Audit label
```

This ground-truth dataset will then be used to evaluate the **AI Freight Invoice Audit Engine**.
