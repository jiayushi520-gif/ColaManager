"""Development reference model for native actions. Never runs on the iPhone."""
from copy import deepcopy
from datetime import datetime, timedelta
import json
import re
from zoneinfo import ZoneInfo


class StateError(ValueError):
    pass


def instant(value):
    if not isinstance(value, str) or not re.fullmatch(
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})', value
    ):
        raise StateError('timestamp requires timezone')
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise StateError('invalid timestamp') from exc


def validate(state, now):
    if not isinstance(state, dict) or type(state.get('schema_version')) is not int or state['schema_version'] not in (1, 2):
        raise StateError('unsupported schema')
    start = instant(state.get('started_at'))
    if not 0 <= (now-start).total_seconds() <= 630720000:
        raise StateError('invalid history range')
    for field in ('deadline_time', 'reminder_time'):
        value = state.get(field, '23:00' if field == 'reminder_time' else None)
        if not isinstance(value, str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', value):
            raise StateError('invalid clock')
    if state.get('deadline_next_day') not in (0, 1, '0', '1'):
        raise StateError('invalid deadline day')
    if state['schema_version'] == 2:
        if not re.fullmatch(r'\d{1,9}', str(state.get('revision', ''))):
            raise StateError('invalid revision')
        for field in ('created_at', 'updated_at'):
            if instant(state.get(field)) > now:
                raise StateError('future metadata timestamp')
    records = state.get('records')
    if not isinstance(records, dict):
        raise StateError('records must be a dictionary')
    for key, record in records.items():
        if not isinstance(record, dict) or record.get('record_id') != key:
            raise StateError('record ID mismatch')
        consumed, due = instant(record.get('consumed_at')), instant(record.get('brushing_deadline'))
        if consumed < start or consumed > now or not 0 <= (due-consumed).total_seconds() <= 172800:
            raise StateError('invalid consumption/deadline')
        for field in ('rinsed_at', 'brushed_at'):
            if field not in record or not isinstance(record[field], str):
                raise StateError('missing check-in field')
            if record[field] and not consumed <= instant(record[field]) <= now:
                raise StateError('invalid check-in time')
    return state


def migrate(state, now):
    validate(state, now)
    result = deepcopy(state)
    if result['schema_version'] == 1:
        result.update(schema_version=2, created_at=result['started_at'], revision=0)
        result.setdefault('updated_at', result['started_at'])
    result['app_version'] = '2.0.0'
    result.setdefault('reminder_time', '23:00')
    return result


def load(raw, now):
    if not raw or not raw.strip():
        raise StateError('empty data; never initialize implicitly')
    if '__COLA_EMPTY__' in raw:
        raise StateError('reserved marker')
    try:
        return migrate(json.loads(raw), now)
    except json.JSONDecodeError as exc:
        raise StateError('damaged JSON; preserve original') from exc


def initialize(now, confirmed=False):
    if not confirmed:
        raise StateError('explicit first-install confirmation required')
    stamp = now.isoformat(timespec='seconds')
    return dict(schema_version=2, app_version='2.0.0', revision=0, started_at=stamp,
                created_at=stamp, updated_at=stamp, deadline_time='02:00',
                deadline_next_day=1, reminder_time='23:00', records={})


def monday(value, zone):
    d = value.astimezone(zone).date()
    return d - timedelta(days=d.weekday())


def summary(state, now, timezone='Asia/Shanghai'):
    validate(state, now)
    zone = ZoneInfo(timezone)
    current = monday(now, zone)
    weeks, bad_weeks = {}, set()
    today = dict(drinks=0, rinses=0, brushes=0)
    pending_previous = False
    for record in state['records'].values():
        consumed, due = instant(record['consumed_at']), instant(record['brushing_deadline'])
        week = monday(consumed, zone)
        if week in weeks:
            raise StateError('duplicate consumption week')
        brush = instant(record['brushed_at']) if record['brushed_at'] else None
        status = ('compliant' if brush <= due else 'late') if brush else ('missed' if now >= due else 'pending')
        weeks[week] = status
        if status in ('missed', 'late'):
            bad_weeks.add(week + timedelta(days=7))
        if status == 'pending' and week + timedelta(days=7) == current:
            pending_previous = True
        for field, target in [('consumed_at','drinks'), ('rinsed_at','rinses'), ('brushed_at','brushes')]:
            if record[field] and instant(record[field]).astimezone(zone).date() == now.astimezone(zone).date():
                today[target] += 1
    return dict(total=len(weeks), banned=current in bad_weeks,
                remaining=max(0, (0 if current in bad_weeks else 1) - int(current in weeks)),
                pending_previous=pending_previous, today=today)


def check_in(state, record_id, field, now):
    validate(state, now)
    if field not in ('rinsed_at', 'brushed_at'):
        raise StateError('unknown check-in')
    record = state['records'][record_id]
    if record[field]:
        return deepcopy(state)
    if not 0 <= (now-instant(record['consumed_at'])).total_seconds() <= 172800:
        raise StateError('outside 48-hour window')
    result = deepcopy(state)
    result['records'][record_id][field] = now.isoformat(timespec='seconds')
    return result


def restore_preview(raw, now, timezone='Asia/Shanghai'):
    state = load(raw, now)
    return state, summary(state, now, timezone)
