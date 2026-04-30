"""Unit tests for uav_tracker.exceptions — BUG-008 typed exceptions."""
import unittest

from uav_tracker.exceptions import (
    InferenceDeviceError,
    ModelNotFoundError,
    SourceOpenError,
    TrackerError,
)


class TestTrackerErrorHierarchy(unittest.TestCase):
    def test_model_not_found_is_tracker_error(self):
        self.assertTrue(issubclass(ModelNotFoundError, TrackerError))

    def test_source_open_is_tracker_error(self):
        self.assertTrue(issubclass(SourceOpenError, TrackerError))

    def test_inference_device_is_tracker_error(self):
        self.assertTrue(issubclass(InferenceDeviceError, TrackerError))


class TestModelNotFoundError(unittest.TestCase):
    def setUp(self):
        self.err = ModelNotFoundError("/models/best.pt")

    def test_path_attribute(self):
        self.assertEqual(self.err.path, "/models/best.pt")

    def test_message_contains_path(self):
        self.assertIn("/models/best.pt", str(self.err))

    def test_is_runtime_error(self):
        self.assertIsInstance(self.err, RuntimeError)


class TestSourceOpenError(unittest.TestCase):
    def test_string_source_attribute(self):
        err = SourceOpenError("/dev/video0")
        self.assertEqual(err.source, "/dev/video0")

    def test_int_source_attribute(self):
        err = SourceOpenError(0)
        self.assertEqual(err.source, 0)

    def test_message_contains_source(self):
        err = SourceOpenError("clip.mp4")
        self.assertIn("clip.mp4", str(err))


class TestInferenceDeviceError(unittest.TestCase):
    def setUp(self):
        self.cause = RuntimeError("CUDA OOM")
        self.err = InferenceDeviceError("cuda:0", self.cause)

    def test_device_attribute(self):
        self.assertEqual(self.err.device, "cuda:0")

    def test_cause_attribute(self):
        self.assertIs(self.err.cause, self.cause)

    def test_message_contains_device(self):
        self.assertIn("cuda:0", str(self.err))


if __name__ == '__main__':
    unittest.main()
