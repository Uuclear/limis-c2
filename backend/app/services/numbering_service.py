from datetime import date

from sqlalchemy.orm import Session

from app.models.numbering import NumberingRule


def _needs_reset(rule: NumberingRule) -> bool:
    today = date.today()
    if rule.sequence_reset == "yearly":
        return rule.last_reset_date.year < today.year
    elif rule.sequence_reset == "monthly":
        return (rule.last_reset_date.year < today.year
                or rule.last_reset_date.month < today.month)
    return False


def _format_date_part(date_format: str) -> str:
    today = date.today()
    if date_format == "YYYY":
        return str(today.year)
    elif date_format == "YYYYMM":
        return today.strftime("%Y%m")
    return ""


def generate_number(db: Session, entity_type: str) -> str:
    rule = (
        db.query(NumberingRule)
        .filter(NumberingRule.entity_type == entity_type, NumberingRule.is_active.is_(True))
        .with_for_update()
        .first()
    )
    if not rule:
        raise ValueError(f"编号规则不存在或未启用: {entity_type}")

    if _needs_reset(rule):
        rule.current_sequence = 0
        rule.last_reset_date = date.today()

    rule.current_sequence += 1
    seq = str(rule.current_sequence).zfill(rule.sequence_digits)

    parts = [rule.prefix]
    date_part = _format_date_part(rule.date_format)
    if date_part:
        parts.append(date_part)
    parts.append(seq)

    db.flush()
    return rule.separator.join(parts)
