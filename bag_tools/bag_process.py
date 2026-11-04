"""Shared helpers: run a `ros2 bag` subprocess for the lifetime of an action goal."""
import os
from pathlib import Path
import signal
import subprocess
import time

from rclpy.action import CancelResponse, GoalResponse

DEFAULT_DATASETS_DIR = os.environ.get('DATASETS_DIR', '/opt/workspace/datasets')


class BagProcessServer:
    """Mixin for an action server node that runs one `ros2 bag` subprocess at a time."""

    def _init_bag_process(self):
        self._proc = None
        self.datasets_dir = Path(self.declare_parameter('datasets_dir', DEFAULT_DATASETS_DIR).value)
        self.datasets_dir.mkdir(parents=True, exist_ok=True)

    def _on_goal(self, _goal_request):
        if self._proc is not None and self._proc.poll() is None:
            self.get_logger().warn('Rejecting goal: a bag process is already running')
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def _on_cancel(self, _goal_handle):
        return CancelResponse.ACCEPT

    def _run(self, goal_handle, cmd, feedback_type, duration=0.0):
        """Run cmd until it exits, the goal is cancelled or duration (s) has elapsed.

        Returns (exit_code, cancelled).
        """
        self.get_logger().info('Running: ' + ' '.join(cmd))
        self._proc = subprocess.Popen(cmd)
        start = time.monotonic()
        cancelled = False
        while self._proc.poll() is None:
            elapsed = time.monotonic() - start
            if goal_handle.is_cancel_requested:
                cancelled = True
                break
            if duration > 0 and elapsed >= duration:
                break
            goal_handle.publish_feedback(feedback_type(elapsed=elapsed))
            time.sleep(0.5)
        code = self._stop()
        return code, cancelled

    def _stop(self):
        """SIGINT the subprocess so rosbag2 closes the MCAP file cleanly."""
        proc = self._proc
        if proc is None:
            return None
        if proc.poll() is None:
            proc.send_signal(signal.SIGINT)
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.get_logger().error('ros2 bag did not exit after SIGINT, killing it')
                proc.kill()
                proc.wait()
        return proc.returncode
