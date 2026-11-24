import importlib.util
import sys
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

_spec = importlib.util.spec_from_file_location(
    'tool_credentials_export',
    Path(__file__).resolve().parents[2] / 'open_webui' / 'tool_credentials_export.py',
)
m = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = m  # dataclasses look the module up while the class is built
_spec.loader.exec_module(m)

COSEC = 'cosec_attendance:cosec_username:cosec_password'


def test_parse_specs():
    specs = m.parse_specs(f' {COSEC} , other:user:pass ')
    assert specs['cosec_attendance'] == m.ExportSpec('cosec_attendance', 'cosec_username', 'cosec_password')
    assert set(specs) == {'cosec_attendance', 'other'}
    assert m.parse_specs('') == {}
    assert m.parse_specs(None) == {}


@pytest.mark.parametrize('bad', ['cosec_attendance', 'a:b', 'a::c', 'a:b:c:d'])
def test_parse_specs_rejects_bad_entries(bad):
    with pytest.raises(ValueError):
        m.parse_specs(bad)


def test_credentials_from_valves():
    spec = m.parse_specs(COSEC)['cosec_attendance']
    assert m.credentials_from_valves(spec, {'cosec_username': ' E123 ', 'cosec_password': 'p w'}) == ('E123', 'p w')
    assert m.credentials_from_valves(spec, {'cosec_username': 'E123', 'cosec_password': ''}) is None
    assert m.credentials_from_valves(spec, {'cosec_password': 'x'}) is None
    assert m.credentials_from_valves(spec, None) is None


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv('TOOL_CREDENTIALS_EXPORT', raising=False)
    monkeypatch.delenv('TOOL_CREDENTIALS_EXPORT_KEY', raising=False)
    assert not m._load().configured


def test_key_required_and_validated(monkeypatch):
    monkeypatch.setenv('TOOL_CREDENTIALS_EXPORT', COSEC)
    monkeypatch.delenv('TOOL_CREDENTIALS_EXPORT_KEY', raising=False)
    with pytest.raises(RuntimeError, match='TOOL_CREDENTIALS_EXPORT_KEY'):
        m._load()
    monkeypatch.setenv('TOOL_CREDENTIALS_EXPORT_KEY', 'not-a-key')
    with pytest.raises(RuntimeError, match='not a valid Fernet key'):
        m._load()


def test_password_round_trip_with_shared_key(monkeypatch):
    key = Fernet.generate_key().decode()
    monkeypatch.setenv('TOOL_CREDENTIALS_EXPORT', COSEC)
    monkeypatch.setenv('TOOL_CREDENTIALS_EXPORT_KEY', key)
    exporter = m._load()
    assert exporter.configured and not exporter.ready
    token = exporter.fernet.encrypt(b'secret')
    # The reading app only needs the same key.
    assert Fernet(key.encode()).decrypt(token) == b'secret'
