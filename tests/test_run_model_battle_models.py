from __future__ import annotations

from pathlib import Path

import app.qml_bridge.dts_bridge as dts_mod
import python_scripts.run_model_battle as battle


def test_parse_plain_baseline_keeps_alias() -> None:
    spec = battle._parse_model_spec("baseline")

    assert spec.label == "baseline"
    assert spec.path_spec == "baseline"


def test_parse_plain_path_uses_file_stem_label() -> None:
    spec = battle._parse_model_spec("/tmp/rtx_latest_best.pt")

    assert spec.label == "rtx_latest_best"
    assert spec.path_spec == "/tmp/rtx_latest_best.pt"


def test_parse_labeled_baseline_keeps_baseline_label_with_explicit_path() -> None:
    spec = battle._parse_model_spec("baseline=/tmp/rtx_latest_best.pt")

    assert spec.label == "baseline"
    assert spec.path_spec == "/tmp/rtx_latest_best.pt"


def test_parse_labeled_candidate_keeps_stable_candidate_label() -> None:
    spec = battle._parse_model_spec("candidate=/tmp/runs/dts_candidate_training/weights/best.pt")

    assert spec.label == "candidate"
    assert spec.path_spec == "/tmp/runs/dts_candidate_training/weights/best.pt"


def test_dts_compare_models_arg_pins_paths_but_preserves_labels() -> None:
    models_arg = dts_mod._battle_models_arg(
        Path("/models/checkpoints/rtx_latest_best.pt"),
        Path("/runs/dts_candidate_training/foo/weights/best.pt"),
    )

    assert models_arg == (
        "baseline=/models/checkpoints/rtx_latest_best.pt,"
        "candidate=/runs/dts_candidate_training/foo/weights/best.pt"
    )


def test_smoke_regression_pack_paths_match_battle_contexts(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(dts_mod, "ROOT", tmp_path)

    packs = dts_mod._regression_pack_paths("smoke")

    assert packs["day"] == tmp_path / battle.CONTEXTS_SMOKE["day"].pack_file
    assert packs["night"] == tmp_path / battle.CONTEXTS_SMOKE["night"].pack_file
    assert packs["ir"] == tmp_path / battle.CONTEXTS_SMOKE["ir"].pack_file
