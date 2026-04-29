"""Tests for Config.validate() — A1d."""
import pytest
from uav_tracker.config import Config


class TestConfigValidate:
    def test_default_config_is_valid(self):
        Config().validate()  # must not raise

    def test_conf_thresh_zero_raises(self):
        with pytest.raises(ValueError, match="CONF_THRESH"):
            Config(CONF_THRESH=0.0).validate()

    def test_conf_thresh_one_raises(self):
        with pytest.raises(ValueError, match="CONF_THRESH"):
            Config(CONF_THRESH=1.0).validate()

    def test_conf_thresh_negative_raises(self):
        with pytest.raises(ValueError, match="CONF_THRESH"):
            Config(CONF_THRESH=-5.0).validate()

    def test_img_size_zero_raises(self):
        with pytest.raises(ValueError, match="IMG_SIZE"):
            Config(IMG_SIZE=0).validate()

    def test_img_size_negative_raises(self):
        with pytest.raises(ValueError, match="IMG_SIZE"):
            Config(IMG_SIZE=-640).validate()

    def test_night_confirm_zero_raises(self):
        with pytest.raises(ValueError, match="NIGHT_CONFIRM"):
            Config(NIGHT_CONFIRM=0).validate()

    def test_budget_fps_zero_raises(self):
        with pytest.raises(ValueError, match="BUDGET_TARGET_FPS"):
            Config(BUDGET_TARGET_FPS=0.0).validate()

    def test_budget_fps_negative_raises(self):
        with pytest.raises(ValueError, match="BUDGET_TARGET_FPS"):
            Config(BUDGET_TARGET_FPS=-1.0).validate()

    def test_smooth_alpha_out_of_range_raises(self):
        with pytest.raises(ValueError, match="SMOOTH_BBOX_ALPHA"):
            Config(SMOOTH_BBOX_ALPHA=1.5).validate()

    def test_valid_edge_values_pass(self):
        Config(CONF_THRESH=0.01, IMG_SIZE=32, NIGHT_CONFIRM=1,
               BUDGET_TARGET_FPS=0.1, SMOOTH_BBOX_ALPHA=0.0).validate()
