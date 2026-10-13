from datetime import date
from pathlib import Path
from unittest.mock import Mock

import streamlit as st
from streamlit.testing.v1 import AppTest

import backend
from backend.dart_client import DisclosureFetchError

APP = Path(__file__).resolve().parents[1] / "frontend/app.py"


def fixture_rows():
    return [
        {"rcept_no": "20261013000001", "rcept_dt": "20261013", "corp_name": "테스트기업", "report_nm": "유상증자결정", "summary": "유상증자 결정", "importance": "high", "sentiment": "neg", "analysis_status": "complete", "data_source": "dart"},
        {"rcept_no": "20261013000002", "rcept_dt": "20261013", "corp_name": "다른기업", "report_nm": "사업보고서", "summary": "사업보고서 제출", "importance": "low", "sentiment": "neu", "analysis_status": "complete", "data_source": "dart"},
    ]


def init_app(monkeypatch, fetch):
    st.cache_data.clear()
    monkeypatch.setattr(backend, "get_classified_disclosures", fetch)
    app = AppTest.from_file(str(APP))
    app.session_state["search_date_input"] = date(2026, 10, 13)
    return app.run()


def click(app, label):
    next(button for button in app.button if button.label == label).click().run()
    assert not app.exception


def test_results_persist_through_filter_and_sort(monkeypatch):
    fetch = Mock(return_value=fixture_rows())
    app = init_app(monkeypatch, fetch)
    click(app, "공시 조회하기")
    assert app.metric[0].value == "2건"
    app.selectbox[0].select("높음").run()
    assert not app.exception
    assert app.metric[0].value == "1건"
    app.selectbox[0].select("전체").run()
    app.selectbox[2].select("영향도 부정 먼저").run()
    assert app.metric[0].value == "2건"
    assert fetch.call_count == 1
    assert app.session_state["saved_alerts"] == []  # 실조회의 자동 보관 정책은 유지


def test_refresh_actually_refetches(monkeypatch):
    fetch = Mock(return_value=fixture_rows())
    app = init_app(monkeypatch, fetch)
    click(app, "공시 조회하기")
    click(app, "🔄 최신화")
    assert fetch.call_count == 2
    assert app.metric[0].value == "2건"


def test_error_keeps_sample_and_stale_results_out(monkeypatch):
    fetch = Mock(side_effect=[fixture_rows(), DisclosureFetchError("DART 연결에 실패했습니다.")])
    app = init_app(monkeypatch, fetch)
    click(app, "공시 조회하기")
    click(app, "🔄 최신화")
    assert app.error[0].value == "DART 연결에 실패했습니다."
    assert not app.metric
    assert "disclosure_results" not in app.session_state


def test_failed_analysis_is_retryable_and_filterable(monkeypatch):
    rows = fixture_rows()
    rows[0].update(importance=None, sentiment=None, analysis_status="failed")
    fetch = Mock(return_value=rows)
    app = init_app(monkeypatch, fetch)
    click(app, "공시 조회하기")
    assert app.warning
    app.selectbox[0].select("미분류").run()
    assert app.metric[0].value == "1건"
    click(app, "공시 조회하기")
    assert fetch.call_count == 2


def test_date_change_requires_new_query(monkeypatch):
    app = init_app(monkeypatch, Mock(return_value=fixture_rows()))
    click(app, "공시 조회하기")
    app.date_input[0].set_value(date(2026, 10, 12)).run()
    assert not app.metric
    assert app.info


def test_demo_popup_and_inbox_navigation(monkeypatch):
    app = init_app(monkeypatch, Mock(return_value=fixture_rows()))
    click(app, "🚨 중요 공시(High) 강제 발생")
    assert len(app.session_state["saved_alerts"]) == 1
    app.run()
    click(app, "🔔 보관함 (1)")
    go = next(button for button in app.button if button.key and button.key.startswith("go_"))
    go.click().run()
    assert not app.exception
    assert app.metric[0].value == "2건"


def test_sample_data_is_labelled_without_dart_links(monkeypatch):
    rows = fixture_rows()
    for item in rows:
        item["data_source"] = "sample"
    app = init_app(monkeypatch, Mock(return_value=rows))
    click(app, "공시 조회하기")
    assert any("실제 공시가 아닙니다" in warning.value for warning in app.warning)
    assert not app.get("link_button")


def test_missing_gemini_key_shows_unclassified_not_low(monkeypatch):
    rows = fixture_rows()
    for item in rows:
        item.update(importance=None, sentiment=None, analysis_status="not_configured")
    app = init_app(monkeypatch, Mock(return_value=rows))
    click(app, "공시 조회하기")
    assert app.metric[3].value == "0건"
    assert any("Gemini 키" in warning.value for warning in app.warning)
    app.selectbox[0].select("미분류").run()
    assert app.metric[0].value == "2건"


def test_report_title_cannot_inject_html(monkeypatch):
    rows = fixture_rows()
    rows[0]["report_nm"] = '<img src=x onerror="alert(1)">'
    app = init_app(monkeypatch, Mock(return_value=rows))
    click(app, "공시 조회하기")
    assert any("&lt;img" in item.value for item in app.markdown)
    assert not any('<img src=x' in item.value for item in app.markdown)
