"""Pure coordinate mapping tests for operator target selection UI."""
from __future__ import annotations

from app.ui.video_mapping import map_widget_bbox_to_frame, map_widget_point_to_frame


class TestMapWidgetPointToFrame:
    def test_maps_center_when_pixmap_is_letterboxed_horizontally(self):
        result = map_widget_point_to_frame(
            widget_size=(1000, 600),
            frame_size=(640, 480),
            point=(500, 300),
        )

        assert result == (320, 240)

    def test_rejects_point_in_left_letterbox(self):
        result = map_widget_point_to_frame(
            widget_size=(1000, 600),
            frame_size=(640, 480),
            point=(90, 300),
        )

        assert result is None

    def test_maps_bottom_right_inside_scaled_frame(self):
        result = map_widget_point_to_frame(
            widget_size=(1000, 600),
            frame_size=(640, 480),
            point=(899, 599),
        )

        assert result == (639, 479)

    def test_maps_when_pixmap_is_letterboxed_vertically(self):
        result = map_widget_point_to_frame(
            widget_size=(800, 800),
            frame_size=(640, 360),
            point=(400, 400),
        )

        assert result == (320, 180)

    def test_rejects_point_in_top_letterbox(self):
        result = map_widget_point_to_frame(
            widget_size=(800, 800),
            frame_size=(640, 360),
            point=(400, 100),
        )

        assert result is None


class TestMapWidgetBboxToFrame:
    def test_maps_drag_bbox_to_frame_bbox(self):
        result = map_widget_bbox_to_frame(
            widget_size=(1000, 600),
            frame_size=(640, 480),
            bbox=(200, 150, 800, 450),
        )

        assert result == (80, 120, 560, 360)

    def test_rejects_bbox_that_starts_in_letterbox(self):
        result = map_widget_bbox_to_frame(
            widget_size=(1000, 600),
            frame_size=(640, 480),
            bbox=(20, 150, 80, 220),
        )

        assert result is None
