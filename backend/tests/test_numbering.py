from datetime import date

from app.models.numbering import NumberingRule
from app.services.numbering_service import generate_number


def _create_rule(db, entity_type="commission", prefix="WT", sequence_reset="yearly"):
    rule = NumberingRule(
        entity_type=entity_type,
        name=f"{entity_type}编号规则",
        prefix=prefix,
        date_format="YYYY",
        separator="-",
        sequence_digits=4,
        sequence_reset=sequence_reset,
        current_sequence=0,
        last_reset_date=date.today(),
        is_active=True,
    )
    db.add(rule)
    db.commit()
    return rule


def test_generate_number_basic(db):
    _create_rule(db, "commission", "WT")
    number = generate_number(db, "commission")
    year = date.today().year
    assert number == f"WT-{year}-0001"


def test_generate_number_increments(db):
    _create_rule(db, "commission", "WT")
    n1 = generate_number(db, "commission")
    n2 = generate_number(db, "commission")
    year = date.today().year
    assert n1 == f"WT-{year}-0001"
    assert n2 == f"WT-{year}-0002"


def test_generate_number_no_rule_raises(db):
    import pytest
    with pytest.raises(ValueError, match="编号规则不存在"):
        generate_number(db, "nonexistent")


def test_generate_number_yearly_reset(db):
    from datetime import date as d
    rule = _create_rule(db, "commission", "WT", "yearly")
    rule.current_sequence = 99
    rule.last_reset_date = d(2025, 6, 15)  # last year
    db.commit()
    number = generate_number(db, "commission")
    year = d.today().year
    assert number == f"WT-{year}-0001"


def test_generate_number_different_entity_types(db):
    _create_rule(db, "commission", "WT")
    _create_rule(db, "sample", "YP")
    wt = generate_number(db, "commission")
    yp = generate_number(db, "sample")
    year = date.today().year
    assert wt == f"WT-{year}-0001"
    assert yp == f"YP-{year}-0001"
