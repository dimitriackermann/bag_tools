"""Action server /bag_player/replay: replay a bag folder from datasets/.

Also offers /bag_player/list_bags (std_srvs/Trigger) returning the bag names, one per line.
"""
import rclpy
from rclpy.action import ActionServer
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node
from std_srvs.srv import Trigger

from bag_tools.bag_process import BagProcessServer
from num_interfaces.action import Replay


class BagPlayer(BagProcessServer, Node):
    def __init__(self):
        super().__init__('bag_player')
        self._init_bag_process()
        self._server = ActionServer(
            self, Replay, '~/replay', self._execute,
            goal_callback=self._on_goal, cancel_callback=self._on_cancel,
            callback_group=ReentrantCallbackGroup())
        self.create_service(Trigger, '~/list_bags', self._list_bags)

    def _bags(self):
        return sorted(p.name for p in self.datasets_dir.iterdir() if (p / 'metadata.yaml').exists())

    def _list_bags(self, _request, response):
        response.success = True
        response.message = '\n'.join(self._bags())
        return response

    def _execute(self, goal_handle):
        goal = goal_handle.request
        result = Replay.Result()
        if goal.bag_name not in self._bags():
            goal_handle.abort()
            result.message = f'unknown bag {goal.bag_name!r}; available: {", ".join(self._bags())}'
            self.get_logger().error(result.message)
            return result

        cmd = ['ros2', 'bag', 'play', str(self.datasets_dir / goal.bag_name),
               '-r', str(goal.rate or 1.0)]
        if goal.loop:
            cmd.append('--loop')
        code, cancelled = self._run(goal_handle, cmd, Replay.Feedback)

        # A non-zero exit right away usually means the bag cannot be opened, e.g. it was
        # written by a newer rosbag2 (Lyrical bag replayed on Jazzy).
        result.success = cancelled or code == 0
        result.message = 'cancelled' if cancelled else (
            'finished' if code == 0 else f'ros2 bag play exited with {code}, see node log')
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
    node = BagPlayer()
    try:
        rclpy.spin(node, executor=MultiThreadedExecutor())
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node._stop()
