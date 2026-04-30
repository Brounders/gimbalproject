from uav_tracker.config import Config


class FocusModeController:
    """Focus-mode state machine: ACQUIRE streak → FOCUS → RELEASE streak → idle."""

    def __init__(self, cfg: Config):
        self._cfg = cfg
        self._active = False
        self._enter_streak = 0
        self._exit_streak = 0

    def is_active(self) -> bool:
        return bool(self._cfg.LOCK_FOCUS_ONLY and self._active)

    def update(self, confirmed: bool) -> bool:
        if not self._cfg.LOCK_FOCUS_ONLY:
            self._active = False
            self._enter_streak = 0
            self._exit_streak = 0
            return False

        enter_frames = max(1, int(self._cfg.LOCK_MODE_ACQUIRE_FRAMES))
        release_frames = max(1, int(self._cfg.LOCK_MODE_RELEASE_FRAMES))

        if confirmed:
            self._enter_streak += 1
            self._exit_streak = 0
            if not self._active and self._enter_streak >= enter_frames:
                self._active = True
            return self._active

        self._enter_streak = 0
        if self._active:
            self._exit_streak += 1
            if self._exit_streak >= release_frames:
                self._active = False
        else:
            self._exit_streak = 0
        return self._active

    def should_run_night_detector(self, frames_since_primary: int) -> bool:
        if not self._cfg.NIGHT_ENABLED:
            return False
        if self._cfg.DISABLE_NIGHT_ON_LOCK and self.is_active():
            return False
        if not self._cfg.NIGHT_RUN_WHEN_PRIMARY_SEEN:
            cooldown = max(0, int(self._cfg.NIGHT_PRIMARY_COOLDOWN))
            if frames_since_primary < cooldown:
                return False
        return True
