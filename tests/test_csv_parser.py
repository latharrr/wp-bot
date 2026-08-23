from datetime import date

import pytest

from app.services.csv_parser import parse_poll_csv, parse_poll_date


def test_parse_poll_csv_normalizes_columns_and_types():
    raw = (
        b"Mobile,Product_Name,Poll_Date,Vote\n"
        b"9198765,Widget, 2026-08-01 ,YES\n"
        b" 9198766 ,Gadget,2026-08-02,No\n"
    )
    df = parse_poll_csv(raw)
    assert list(df.columns) == ["mobile", "product_name", "poll_date", "vote"]
    assert df["mobile"].tolist() == ["9198765", "9198766"]
    assert df["vote"].tolist() == ["yes", "no"]
    assert df["poll_date"].tolist() == [date(2026, 8, 1), date(2026, 8, 2)]


def test_parse_poll_csv_raises_on_missing_columns():
    raw = b"mobile,vote\n123,yes\n"
    with pytest.raises(ValueError, match="missing required columns"):
        parse_poll_csv(raw)


def test_parse_poll_date_accepts_date_and_string():
    assert parse_poll_date(date(2026, 1, 5)) == date(2026, 1, 5)
    assert parse_poll_date("2026-01-05") == date(2026, 1, 5)
