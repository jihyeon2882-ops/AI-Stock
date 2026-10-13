from unittest.mock import Mock

import pytest
import requests

from backend import dart_client
from backend.config import get_setting


def disclosure(number="20261013000001"):
    return {"rcept_no": number, "corp_name": "테스트기업", "report_nm": "사업보고서", "rcept_dt": "20261013"}


@pytest.fixture(autouse=True)
def settings(monkeypatch):
    monkeypatch.setattr(dart_client, "get_setting", lambda name: "dummy-key")


def response(payload):
    result = Mock()
    result.json.return_value = payload
    return result


def test_fetches_all_pages_and_deduplicates(monkeypatch):
    first, second = disclosure(), disclosure("20261013000002")
    get = Mock(side_effect=[
        response({"status": "000", "total_page": 2, "list": [first]}),
        response({"status": "000", "total_page": 2, "list": [first, second]}),
    ])
    monkeypatch.setattr(dart_client.requests, "get", get)
    results = dart_client.get_disclosures("20261013")
    assert [item["rcept_no"] for item in results] == [first["rcept_no"], second["rcept_no"]]
    assert [call.kwargs["params"]["page_no"] for call in get.call_args_list] == [1, 2]
    assert all(item["data_source"] == "dart" for item in results)


def test_no_disclosures_is_empty_not_sample(monkeypatch):
    monkeypatch.setattr(dart_client.requests, "get", Mock(return_value=response({"status": "013"})))
    assert dart_client.get_disclosures("20261013") == []


@pytest.mark.parametrize("status", ["010", "011", "012", "020", "800", "900"])
def test_dart_errors_never_return_sample(monkeypatch, status):
    monkeypatch.setattr(dart_client.requests, "get", Mock(return_value=response({"status": status, "message": "secret-value"})))
    with pytest.raises(dart_client.DisclosureFetchError) as error:
        dart_client.get_disclosures("20261013")
    assert "secret-value" not in str(error.value)


def test_partial_fetch_does_not_claim_complete(monkeypatch):
    monkeypatch.setattr(dart_client.requests, "get", Mock(side_effect=[
        response({"status": "000", "total_page": 2, "list": [disclosure()]}),
        requests.Timeout("URL containing dummy-key"),
    ]))
    with pytest.raises(dart_client.DisclosureFetchError) as error:
        dart_client.get_disclosures("20261013")
    assert "dummy-key" not in str(error.value)


def test_missing_key_does_not_attempt_network(monkeypatch):
    monkeypatch.setattr(dart_client, "get_setting", lambda name: "")
    get = Mock()
    monkeypatch.setattr(dart_client.requests, "get", get)
    with pytest.raises(dart_client.DisclosureFetchError):
        dart_client.get_disclosures("20261013")
    get.assert_not_called()


@pytest.mark.parametrize("value", ["20260230", "2026-10-13", "123", "２０２６１０１３"])
def test_invalid_date_rejected(value):
    with pytest.raises(ValueError):
        dart_client.get_disclosures(value)


def test_sample_mode_explicitly_labelled(monkeypatch):
    monkeypatch.setattr(dart_client, "USE_SAMPLE_DATA", True)
    rows = dart_client.get_disclosures("20261013")
    assert all(row["data_source"] == "sample" and row["rcept_dt"] == "20261013" for row in rows)


def test_env_settings_do_not_require_secrets_file(monkeypatch):
    monkeypatch.setenv("DART_API_KEY", "  dummy-key  ")
    assert get_setting("DART_API_KEY") == "dummy-key"


def test_missing_secrets_file_returns_default(monkeypatch):
    from backend import config
    monkeypatch.delenv("NONEXISTENT_SETTING", raising=False)
    monkeypatch.setattr(config.st, "secrets", Mock(get=Mock(side_effect=FileNotFoundError)))
    assert get_setting("NONEXISTENT_SETTING", "fallback") == "fallback"


@pytest.mark.parametrize("payload", [[], {"status": "000", "total_page": "bad", "list": []}, {"status": "000", "total_page": 1, "list": [{}]}])
def test_malformed_responses_are_controlled_errors(monkeypatch, payload):
    monkeypatch.setattr(dart_client.requests, "get", Mock(return_value=response(payload)))
    with pytest.raises(dart_client.DisclosureFetchError):
        dart_client.get_disclosures("20261013")
