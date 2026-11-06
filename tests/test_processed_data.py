"""
Tests for processed analytical datasets and business assertions.
"""
from pathlib import Path
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"


def test_recon_summary_assertions():
    """Verify Problem 1: Reconciliation check summary structure and values."""
    path = PROCESSED_DIR / "recon_summary.csv"
    assert path.exists(), "recon_summary.csv not found"

    df = pd.read_csv(path)
    expected_checks = [
        "C1_order_without_items",
        "C2_order_without_payment",
        "C3_overpaid_vs_basket",
        "C4_underpaid_vs_basket",
        "C5_delivered_without_delivery_date",
        "C6_delivered_without_approval",
        "C7_carrier_before_purchase",
        "C8_customer_before_carrier",
        "C9_canceled_but_delivered",
    ]
    assert set(expected_checks).issubset(set(df["check_id"]))
    assert len(df) == 9

    # C1 (payment without items) should be the largest financial leakage
    c1 = df[df["check_id"] == "C1_order_without_items"].iloc[0]
    assert c1["orders_failing"] == 775
    assert c1["amount_at_stake_brl"] > 160000


def test_stuck_orders_backlog():
    """Verify Problem 2: Stuck orders backlog count and triage priority."""
    path = PROCESSED_DIR / "stuck_orders_prioritized.csv"
    assert path.exists(), "stuck_orders_prioritized.csv not found"

    df = pd.read_csv(path)
    # Total stuck backlog count
    assert len(df) == 1729
    # Triage buckets must be strictly P1, P2, P3
    assert set(df["priority"].unique()) == {"P1", "P2", "P3"}
    # P1 orders are high-value (> 200 BRL)
    assert (df[df["priority"] == "P1"]["order_value"] >= 200.0).all()
    # P3 orders are auto-resolvable
    assert (df[df["priority"] == "P3"]["auto_resolvable"] == 1).all()


def test_monthly_kpis_integrity():
    """Verify Problem 3: Monthly KPI series bounds and completeness."""
    path = PROCESSED_DIR / "monthly_kpis.csv"
    assert path.exists(), "monthly_kpis.csv not found"

    df = pd.read_csv(path)
    assert len(df) == 20  # Jan 2017 to Aug 2018 = 20 months
    assert df["purchase_month"].min() == "2017-01"
    assert df["purchase_month"].max() == "2018-08"

    # Delivery & late rates should be reasonable percentages
    assert (df["late_pct"] >= 0).all() and (df["late_pct"] <= 50).all()
    assert (df["gmv_brl"] > 0).all()
    assert (df["orders_placed"] > 0).all()


def test_seller_risk_tiers():
    """Verify Problem 4: Seller risk score bounds and quadrant distribution."""
    path = PROCESSED_DIR / "seller_risk_tiers.csv"
    assert path.exists(), "seller_risk_tiers.csv not found"

    df = pd.read_csv(path)
    assert len(df) >= 700  # Scored qualified sellers

    # Risk scores must be 0-100 bounded
    assert (df["risk_score"] >= 0).all() and (df["risk_score"] <= 100).all()

    # Priority quadrants must exist
    expected_quadrants = {
        "Q1 Fix now (AM-owned)",
        "Q2 Protect (keep happy)",
        "Q3 Automate nudges / restrict",
        "Q4 Self-serve",
    }
    assert expected_quadrants.issubset(set(df["quadrant"].unique()))

    # Q1 (Fix now) should be a focused high-GMV high-risk cohort (~32 sellers)
    q1_count = (df["quadrant"] == "Q1 Fix now (AM-owned)").sum()
    assert 20 <= q1_count <= 50


def test_whatif_scenario_monotonicity():
    """Verify Problem 3 what-if: late rate drops as seller handoff improves."""
    path = PROCESSED_DIR / "whatif_handoff.csv"
    assert path.exists(), "whatif_handoff.csv not found"

    df = pd.read_csv(path)
    # As handoff reduction increases, late_rate_new_pct should decrease monotonically
    assert df["late_rate_new_pct"].is_monotonic_decreasing
