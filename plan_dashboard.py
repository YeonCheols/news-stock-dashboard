"""Stable entry point for the AI-generated project-plan dashboard."""

from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parent
GENERATED_PATH = ROOT / "plan_dashboard_generated.py"


def load_generated_dashboard():
    if not GENERATED_PATH.exists():
        return None
    spec = spec_from_file_location("plan_dashboard_generated", GENERATED_PATH)
    if spec is None or spec.loader is None:
        return None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    generated = load_generated_dashboard()
    if generated is None or not hasattr(generated, "render"):
        st.set_page_config(page_title="구현 계획 추적기", page_icon="📋", layout="wide")
        st.title("구현 계획 추적기")
        st.warning("AI 분석 결과가 아직 생성되지 않았습니다.")
        st.code("plan-master-review 스킬을 실행한 뒤 이 대시보드를 다시 시작하세요.")
        return
    generated.render()


if __name__ == "__main__":
    main()
