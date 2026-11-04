"""Action server /bag_recorder/record: record topics and services into datasets/ as MCAP."""
from datetime import datetime
import os
import re

import rclpy
from rclpy.action import ActionServer
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node

from bag_tools.bag_process import BagProcessServer
from num_interfaces.action import Record


class BagRecorder(BagProcessServer, Node):
    def __init__(self):
        super().__init__('bag_recorder')
        self._init_bag_process()
        self._server = ActionServer(
            self, Record, '~/record', self._execute,
            goal_callback=self._on_goal, cancel_callback=self._on_cancel,
            callback_group=ReentrantCallbackGroup())

    def _bag_path(self, name):
        prefix = re.sub(r'[^A-Za-z0-9_-]', '_', name) or 'bag'
        distro = os.environ.get('ROS_DISTRO', 'ros')
        stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        return self.datasets_dir / f'{prefix}_{distro}_{stamp}'

    def _execute(self, goal_handle):
        goal = goal_handle.request
        path = self._bag_path(goal.name)
        result = Record.Result(bag_path=str(path))
        if path.exists():
            goal_handle.abort()
            result.message = f'{path.name} already exists'
            return result

        cmd = ['ros2', 'bag', 'record', '-s', 'mcap', '-o', str(path)]
        cmd += ['--topics', *goal.topics] if goal.topics else ['--all']
        code, cancelled = self._run(goal_handle, cmd, Record.Feedback, goal.duration)

        result.success = path.exists() and code in (0, -2)
        result.message = f'recorded to {path.name}' if result.success else f'ros2 bag exited with {code}'
        self.get_logger().info(result.message)
        if cancelled:
            goal_handle.canceled()
        elif result.success:
            goal_handle.succeed()
        else:
            goal_handle.abort()
        return result


def main():
    rclpy.init()
    node = BagRecorder()
    try:
        rclpy.spin(node, executor=MultiThreadedExecutor())
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node._stop()
