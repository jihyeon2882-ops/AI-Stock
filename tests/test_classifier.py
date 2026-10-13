import copy
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from backend import llm_classifier as classifier


def rows(count=1):
    return [{"rcept_no": f"20261013{i:06d}", "corp_name": "테스트기업", "report_nm": "유상증자결정", "rcept_dt": "20261013"} for i in range(count)]


def analysis(number):
    return {"rcept_no": number, "importance": "high", "summary": "유상증자 결정", "sentiment": "neu"}


def install_client(monkeypatch, generate):
    client = Mock()
    client.__enter__ = Mock(return_value=client)
    client.__exit__ = Mock(return_value=False)
    client.models.generate_content.side_effect = generate
    factory = Mock(return_value=client)
    monkeypatch.setattr(classifier.genai, "Client", factory)
    monkeypatch.setattr(classifier, "get_setting", lambda name, default="": "dummy-key" if name == "GEMINI_API_KEY" else default)
    return client


def test_valid_analysis_preserves_input(monkeypatch):
    original = rows()
    before = copy.deepcopy(original)
    client = install_client(monkeypatch, [SimpleNamespace(text=json.dumps({"results": [analysis(original[0]["rcept_no"])]}))])
    result = classifier.classify_disclosures(original)
    assert result[0]["importance"] == "high"
    assert result[0]["analysis_status"] == "complete"
    assert original == before
    client.__exit__.assert_called_once()


@pytest.mark.parametrize("change", [
    {"importance": "unknown"}, {"summary": "너무 긴 요약" * 10}, {"summary": ""},
    {"sentiment": "certain"}, {"rcept_no": "20261013000999"},
])
def test_invalid_response_is_unclassified(monkeypatch, change):
    item = analysis(rows()[0]["rcept_no"])
    item.update(change)
    install_client(monkeypatch, [SimpleNamespace(text=json.dumps({"results": [item]}))])
    result = classifier.classify_disclosures(rows())[0]
    assert result["importance"] is None and result["sentiment"] is None
    assert result["analysis_status"] == "failed"


@pytest.mark.parametrize("payload", ["not-json", '{"results": []}', None])
def test_unusable_response_is_unclassified(monkeypatch, payload):
    install_client(monkeypatch, [SimpleNamespace(text=payload)])
    assert classifier.classify_disclosures(rows())[0]["analysis_status"] == "failed"


def test_duplicate_ids_rejected(monkeypatch):
    item = analysis(rows()[0]["rcept_no"])
    install_client(monkeypatch, [SimpleNamespace(text=json.dumps({"results": [item, item]}))])
    assert classifier.classify_disclosures(rows())[0]["importance"] is None


def test_missing_key_and_empty_list_do_not_call_model(monkeypatch):
    factory = Mock()
    monkeypatch.setattr(classifier.genai, "Client", factory)
    monkeypatch.setattr(classifier, "get_setting", lambda *args: "")
    assert classifier.classify_disclosures([]) == []
    assert classifier.classify_disclosures(rows())[0]["analysis_status"] == "not_configured"
    factory.assert_not_called()


def test_failed_batch_does_not_erase_successful_batch(monkeypatch):
    def generate(**kwargs):
        payload = json.loads(kwargs["contents"])
        if payload[0]["rcept_no"] == rows()[0]["rcept_no"]:
            raise RuntimeError("private-key should never be displayed")
        return SimpleNamespace(text=json.dumps({"results": [analysis(item["rcept_no"]) for item in payload]}))
    client = install_client(monkeypatch, generate)
    results = classifier.classify_disclosures(rows(21))
    assert all(row["analysis_status"] == "failed" for row in results[:20])
    assert results[20]["analysis_status"] == "complete"
    assert client.models.generate_content.call_count == 2


def test_real_sdk_serializes_request_without_network(monkeypatch):
    # 모델 메서드 모의만으로 놓칠 수 있는 SDK 설정·스키마 변환도 실제 SDK로 검증한다.
    import httpx
    from google.genai import Client as RealClient
    from google.genai import types
    requests = []

    def respond(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={
            "candidates": [{"content": {"role": "model", "parts": [{"text": json.dumps({"results": [analysis(rows()[0]["rcept_no"])]})}]}, "finishReason": "STOP"}]
        })

    transport_client = httpx.Client(transport=httpx.MockTransport(respond))

    def create_client(**kwargs):
        options = kwargs["http_options"].model_dump(exclude_none=True)
        options["httpx_client"] = transport_client
        options["async_client_args"] = {"trust_env": False}
        return RealClient(api_key=kwargs["api_key"], http_options=types.HttpOptions(**options))

    monkeypatch.setattr(classifier.genai, "Client", create_client)
    monkeypatch.setattr(classifier, "get_setting", lambda name, default="": "dummy-key" if name == "GEMINI_API_KEY" else default)
    result = classifier.classify_disclosures(rows())
    assert len(requests) == 1
    assert result[0]["analysis_status"] == "complete"
