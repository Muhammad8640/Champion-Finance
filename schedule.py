"""Generate transaction occurrences. A recurring series tracks payment per due date."""
from datetime import date, timedelta
import calendar

FREQUENCIES = ['One-time', 'Weekly', 'Every 2 weeks', 'Monthly', 'Quarterly', 'Yearly']


def add_months_anchored(anchor: date, months: int) -> date:
    """Keep original day-of-month, clipping only in short months."""
    total = anchor.year * 12 + (anchor.month - 1) + months
    year, month0 = divmod(total, 12)
    month = month0 + 1
    day = min(anchor.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def occurrences(transaction, start: date, end: date):
    """Yield dates of a schedule between start/end inclusive."""
    anchor = date.fromisoformat(transaction['due_date'])
    freq = transaction['frequency']
    if start > end or end < anchor:
        return
    if freq == 'One-time':
        if start <= anchor <= end:
            yield anchor
        return
    if freq in ('Weekly', 'Every 2 weeks'):
        step = 7 if freq == 'Weekly' else 14
        index = max(0, (start - anchor).days // step)
        current = anchor + timedelta(days=index * step)
        while current <= end:
            if current >= start:
                yield current
            current += timedelta(days=step)
        return
    interval = {'Monthly': 1, 'Quarterly': 3, 'Yearly': 12}[freq]
    month_diff = (start.year - anchor.year) * 12 + (start.month - anchor.month)
    index = max(0, month_diff // interval - 1)
    while True:
        current = add_months_anchored(anchor, index * interval)
        if current > end:
            return
        if current >= start:
            yield current
        index += 1


def build_occurrences(transactions, statuses, start, end):
    rows = []
    for tx in transactions:
        for due in occurrences(tx, start, end):
            iso = due.isoformat()
            rows.append({**tx, 'occurrence_date': iso, 'paid': statuses.get((tx['id'], iso), False)})
    return sorted(rows, key=lambda r: (r['occurrence_date'], r['name'].casefold(), r['id']))
