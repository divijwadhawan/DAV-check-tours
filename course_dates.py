"""Parse DAV abbreviated dates without inventing attendance schedules."""
import re
from datetime import date

TOKEN = re.compile(r'(?<!\d)(\d{1,2})\.(?:(\d{1,2})\.(?:(\d{4}|\d{2})(?!\d))?)?')


def extract_dates(raw):
    tokens = list(TOKEN.finditer(raw))
    if not tokens:
        return {'start_date': '', 'end_date': '', 'days': '', 'date_note': 'Could not parse dates'}
    year = month = None
    parsed = []
    try:
        for token in reversed(tokens):
            day_s, month_s, year_s = token.groups()
            if year_s:
                year = int(year_s)
                if year < 100:
                    year += 2000
            if month_s:
                new_month = int(month_s)
                if not year_s and month is not None and new_month > month and parsed:
                    year -= 1
                month = new_month
            if month is None or year is None:
                raise ValueError('Missing month or year')
            parsed.append(date(year, month, int(day_s)))
        start, end = min(parsed), max(parsed)
    except (ValueError, TypeError):
        return {'start_date': '', 'end_date': '', 'days': '', 'date_note': 'Could not parse dates'}
    recurring = bool(re.search(r'ausg|ferien|wöch|woech|jeden', raw, re.I))
    return {'start_date': start.isoformat(), 'end_date': end.isoformat(),
            'days': (end - start).days + 1,
            'date_note': 'Calendar span; recurring sessions / exclusions apply' if recurring else 'Inclusive calendar span; see original dates for individual sessions'}


def extract_price(entry):
    # DAV's first price box is the own-section member price.
    node = entry.select_one('.tour-price__box .tour-price__icon')
    raw = node.get_text(' ', strip=True) if node else ''
    match = re.search(r'\d[\d.,\s]*', raw)
    if not match:
        return {'cost_eur': '', 'cost_note': raw or 'Not published'}
    value = match.group().strip().replace(' ', '').replace('\u00a0', '')
    if ',' in value:
        value = value.replace('.', '').replace(',', '.')
    elif re.fullmatch(r'\d{1,3}(\.\d{3})+', value):
        value = value.replace('.', '')
    return {'cost_eur': value, 'cost_note': 'DAV München & Oberland member price as listed; additional costs may apply'}
