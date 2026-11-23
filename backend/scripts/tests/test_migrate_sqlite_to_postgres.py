import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

_spec = importlib.util.spec_from_file_location(
    'migrate_sqlite_to_postgres', Path(__file__).resolve().parent.parent / 'migrate_sqlite_to_postgres.py'
)
m = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(m)


def test_json_text_is_parsed_and_nul_stripped():
    assert m.convert_value('{"a": [1, "x\\u0000y"]}', postgresql.JSON()) == {'a': [1, 'xy']}
    assert m.convert_value(b'[1, 2]', postgresql.JSONB()) == [1, 2]
    assert m.convert_value({'already': 'parsed'}, sa.JSON()) == {'already': 'parsed'}


def test_invalid_json_raises():
    with pytest.raises(ValueError):
        m.convert_value('{broken', sa.JSON())


@pytest.mark.parametrize(
    'raw, expected',
    [(1, True), (0, False), ('true', True), ('0', False), ('', False), (True, True)],
)
def test_boolean(raw, expected):
    assert m.convert_value(raw, sa.Boolean()) is expected


def test_boolean_rejects_unknown_string():
    with pytest.raises(ValueError):
        m.convert_value('maybe', sa.Boolean())


def test_text_and_integer():
    assert m.convert_value('a\x00b', sa.Text()) == 'ab'
    assert m.convert_value(12, sa.String()) == '12'
    assert m.convert_value('42', sa.BigInteger()) == 42
    assert m.convert_value(None, sa.Text()) is None


def test_build_plan_orders_and_reports():
    meta = sa.MetaData()
    sa.Table('user', meta, sa.Column('id', sa.Text, primary_key=True))
    sa.Table(
        'chat',
        meta,
        sa.Column('id', sa.Text, primary_key=True),
        sa.Column('user_id', sa.Text, sa.ForeignKey('user.id')),
    )
    sa.Table('alembic_version', meta, sa.Column('version_num', sa.Text))

    src = {'chat': ['id', 'user_id', 'legacy'], 'user': ['id'], 'config_old': ['id'], 'alembic_version': ['version_num']}
    ordered, only_in_sqlite, problems = m.build_plan(src, meta)

    assert [t.name for t in ordered] == ['user', 'chat']
    assert only_in_sqlite == ['config_old']
    assert problems == ['chat: columns missing in Postgres: legacy']
