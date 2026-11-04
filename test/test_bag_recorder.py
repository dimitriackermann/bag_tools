import rclpy

from bag_tools.bag_recorder import BagRecorder


def test_bag_path_is_sanitised_and_tagged_with_distro(tmp_path, monkeypatch):
    monkeypatch.setenv('ROS_DISTRO', 'jazzy')
    rclpy.init(args=['--ros-args', '-p', f'datasets_dir:={tmp_path}'])
    try:
        node = BagRecorder()
        path = node._bag_path('my run/1')
        assert path.parent == tmp_path
        assert path.name.startswith('my_run_1_jazzy_')
        assert node._bag_path('').name.startswith('bag_jazzy_')
        node.destroy_node()
    finally:
        rclpy.shutdown()
