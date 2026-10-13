"""환경변수 또는 Streamlit Secrets에서 실행 시점에 설정을 읽는다."""

import os

import streamlit as st


def get_setting(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value is not None:
        return value.strip()
    try:
        return str(st.secrets.get(name, default)).strip()
    except FileNotFoundError:
        return default
