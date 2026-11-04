# bag_tools

| Node | Interface | Does |
|---|---|---|
| `bag_recorder` | action `/bag_recorder/record` (`num_interfaces/action/Record`) | `ros2 bag record -s mcap --all` (or given topics) into `datasets/<name>_<distro>_<timestamp>/`; stops after `duration` or on cancel |
| `bag_player` | action `/bag_player/replay` (`num_interfaces/action/Replay`) | `ros2 bag play datasets/<bag_name>` with rate/loop; stops on cancel |
| `bag_player` | service `/bag_player/list_bags` (`std_srvs/Trigger`) | lists bags in `datasets/` |

Parameter `datasets_dir` (default `$DATASETS_DIR` or `/opt/workspace/datasets`).
