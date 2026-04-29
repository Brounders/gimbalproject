"""Tests for RuntimeConfigView — BUG-001 fix."""
from uav_tracker.config import Config
from uav_tracker.runtime_config import RuntimeConfigView


class TestRuntimeConfigView:
    def test_reads_base_when_no_override(self):
        cfg = Config()
        view = RuntimeConfigView(cfg)
        assert view.CONF_THRESH == cfg.CONF_THRESH

    def test_override_shadows_base(self):
        cfg = Config()
        original = cfg.CONF_THRESH
        view = RuntimeConfigView(cfg, {"CONF_THRESH": 0.05})
        assert view.CONF_THRESH == 0.05
        assert cfg.CONF_THRESH == original  # base unchanged

    def test_with_overrides_returns_new_view(self):
        cfg = Config()
        view = RuntimeConfigView(cfg)
        new_view = view.with_overrides(CONF_THRESH=0.05, NIGHT_MOT_THRESH=12)
        assert new_view.CONF_THRESH == 0.05
        assert new_view.NIGHT_MOT_THRESH == 12
        # original view unchanged
        assert view.CONF_THRESH == cfg.CONF_THRESH

    def test_base_cfg_never_mutated(self):
        cfg = Config()
        original_conf = cfg.CONF_THRESH
        view = RuntimeConfigView(cfg)
        view = view.with_overrides(CONF_THRESH=0.05)
        assert cfg.CONF_THRESH == original_conf  # base still intact

    def test_clear_overrides_restores_base(self):
        cfg = Config()
        view = RuntimeConfigView(cfg, {"CONF_THRESH": 0.05})
        cleared = RuntimeConfigView(cfg)  # new view without overrides
        assert cleared.CONF_THRESH == cfg.CONF_THRESH

    def test_active_overrides_returns_copy(self):
        cfg = Config()
        view = RuntimeConfigView(cfg, {"CONF_THRESH": 0.05})
        overrides = view.active_overrides()
        assert overrides == {"CONF_THRESH": 0.05}
        overrides["CONF_THRESH"] = 99  # mutating copy doesn't affect view
        assert view.CONF_THRESH == 0.05

    def test_non_overridden_field_proxies_to_base(self):
        cfg = Config()
        view = RuntimeConfigView(cfg, {"CONF_THRESH": 0.05})
        assert view.IMG_SIZE == cfg.IMG_SIZE
        assert view.DEVICE == cfg.DEVICE
