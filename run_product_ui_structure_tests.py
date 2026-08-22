from __future__ import annotations

import ast
from pathlib import Path


APP_PATH = Path("app.py")


def load_function_sources(source: str):
    tree = ast.parse(source)
    functions = {}

    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            functions[node.name] = ast.get_source_segment(
                source,
                node,
            )

    return functions


def run_tests():
    source = APP_PATH.read_text(encoding="utf-8")
    functions = load_function_sources(source)

    required_functions = [
        "render_hero",
        "render_weekly_plan_product",
        "render_decision_cards",
        "render_product_workspace",
        "main",
    ]

    for function_name in required_functions:
        assert function_name in functions, function_name

    hero_source = functions["render_hero"]
    assert "Haftalık koç özeti" not in hero_source

    plan_source = functions["render_weekly_plan_product"]
    assert "st.metric" not in plan_source
    assert "render_value_card" in plan_source
    assert "render_plan_empty_state" in plan_source
    assert "render_guidance_box" in plan_source
    assert "Check-in nasıl uygulandı?" in plan_source
    assert "Yarış niyeti hakkında" in plan_source

    decision_source = functions["render_decision_cards"]
    assert "st.metric" not in decision_source
    assert "render_value_card" in decision_source
    assert "#### Neden?" not in decision_source

    workspace_source = functions["render_product_workspace"]
    for tab_label in (
        "Haftalık Plan",
        "Veriler ve Karar",
        "Feedback",
        "Teknik Detaylar",
    ):
        assert tab_label in workspace_source, tab_label

    assert "render_weekly_plan_product" in workspace_source
    assert "render_primary_coach_message" in workspace_source
    assert "render_decision_cards" in workspace_source
    assert "render_compact_metrics" in workspace_source
    assert "render_context_summary" in workspace_source
    assert "render_feedback_form" in workspace_source
    assert "render_reports" in workspace_source

    main_source = functions["main"]
    assert "render_product_workspace" in main_source
    assert "render_weekly_plan_product" not in main_source
    assert "render_decision_cards" not in main_source
    assert "render_feedback_form" not in main_source

    assert ".product-value-content" in source
    assert "text-overflow: clip" in source
    assert "overflow-wrap: anywhere" in source
    assert "Check-in\'i kaydet ve planı oluştur" in source
    assert "render_sidebar_actions(current_manual_context)" in source

    print("All product UI structure tests passed.")


if __name__ == "__main__":
    run_tests()
