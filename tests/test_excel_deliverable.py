"""
Tests for Excel Command Center deliverable structure and formulas.
"""
from pathlib import Path
import openpyxl
import pytest

ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = ROOT / "excel" / "Olist_Ops_Command_Center.xlsx"


def test_excel_file_exists():
    """Verify Excel workbook exists and has non-trivial size."""
    assert EXCEL_PATH.exists(), f"Excel deliverable not found at {EXCEL_PATH}"
    assert EXCEL_PATH.stat().st_size > 50000, "Excel file is unexpectedly small"


def test_excel_sheet_structure():
    """Verify all 8 expected sheets are present."""
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=False, read_only=False)
    expected_sheets = [
        "Cover",
        "Dashboard",
        "Monthly_KPIs",
        "Recon_Checks",
        "Backlog_Worklist",
        "Capacity_Model",
        "Seller_Risk",
        "WhatIf_Handoff",
    ]
    for sheet_name in expected_sheets:
        assert sheet_name in wb.sheetnames, f"Missing sheet: {sheet_name}"
    wb.close()


def test_excel_dynamic_formulas():
    """Verify that calculations use live Excel formulas rather than static values."""
    wb = openpyxl.load_workbook(EXCEL_PATH, data_only=False)
    
    # Check Capacity_Model has formulas
    ws_cap = wb["Capacity_Model"]
    found_formula = False
    for row in ws_cap.iter_rows(values_only=True):
        for cell in row:
            if isinstance(cell, str) and cell.startswith("="):
                found_formula = True
                break
        if found_formula:
            break
    assert found_formula, "Capacity_Model must contain live formulas"

    # Check Dashboard has formulas
    ws_dash = wb["Dashboard"]
    found_dash_formula = False
    for row in ws_dash.iter_rows(values_only=True):
        for cell in row:
            if isinstance(cell, str) and cell.startswith("="):
                found_dash_formula = True
                break
        if found_dash_formula:
            break
    assert found_dash_formula, "Dashboard must contain dynamic formulas"

    wb.close()

