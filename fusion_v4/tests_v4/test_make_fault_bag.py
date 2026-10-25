"""Logic test of faults/make_fault_bag.py with a fake rosbag module (the real one exists only in the ROS containers)."""
import json, os, sys, types, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "faults"))

class T:
    def __init__(s, x): s.x = x
    def to_sec(s): return s.x

STORE = {}
class Bag:
    def __init__(s, path, mode="r", compression=None): s.path, s.mode = path, mode
    def __enter__(s):
        if s.mode == "w": STORE[s.path] = []
        return s
    def __exit__(s, *a): return False
    def get_type_and_topic_info(s):
        ti = types.SimpleNamespace
        return ti(topics={"/cam": ti(msg_type="sensor_msgs/Image"), "/ci": ti(msg_type="sensor_msgs/CameraInfo"),
                          "/pk": ti(msg_type="velodyne_msgs/VelodyneScan"), "/imu": ti(msg_type="sensor_msgs/Imu")})
    def get_start_time(s): return 100.0
    def get_end_time(s): return 400.0
    def read_messages(s, raw=False, return_connection_header=False):
        for k in range(3000):
            t = 100.0 + k * 0.1
            for tp in ("/cam", "/ci", "/pk", "/imu"):
                yield (tp, ("d", b"x", "m", 0, None), T(t), {"latching": "0"}) if return_connection_header else (tp, ("d", b"x"), T(t))
    def write(s, topic, msg, t, raw=False, connection_header=None): STORE[s.path].append((topic, t.to_sec(), connection_header))

sys.modules["rosbag"] = types.SimpleNamespace(Bag=Bag)
import make_fault_bag as M

def test_windows():
    assert M.windows("none", 0, 100) == []
    w = M.windows("C10", 0, 100); assert [round(a) for a, b in w] == [30, 55, 80] and all(abs(b - a - 10) < 1e-9 for a, b in w)
    w = M.windows("L30", 0, 100); assert [round(a) for a, b in w] == [40, 75] and all(abs(b - a - 30) < 1e-9 for a, b in w)

def test_camera_drop():
    d = tempfile.mkdtemp(); STORE.clear()
    assert M.main(["--fault", "C10", "--out", d, "/x/a.bag"]) == 0
    msgs = STORE[os.path.join(d, "a.bag")]
    cam = [t for tp, t, h in msgs if tp == "/cam"]; imu = [t for tp, t, h in msgs if tp == "/imu"]; pk = [t for tp, t, h in msgs if tp == "/pk"]
    assert len(imu) == 3000 and len(pk) == 3000                       # untouched
    assert len(cam) == 3000 - 3 * 100                                # 3 windows x 10 s x 10 Hz
    assert not any(190 <= t < 200 or 265 <= t < 275 or 340 <= t < 350 for t in cam)
    assert all(h == {"latching": "0"} for tp, t, h in msgs)         # connection headers kept
    man = json.load(open(os.path.join(d, "fault_manifest.json")))
    assert man["dropped"] == {"/ci": 300, "/cam": 300} and man["windows_rel"][0] == [90.0, 100.0]

def test_lidar_and_none():
    d = tempfile.mkdtemp(); STORE.clear()
    assert M.main(["--fault", "L30", "--out", d, "/x/a.bag"]) == 0
    msgs = STORE[os.path.join(d, "a.bag")]
    assert len([1 for tp, t, h in msgs if tp == "/pk"]) == 3000 - 2 * 300 and len([1 for tp, t, h in msgs if tp == "/cam"]) == 3000
    d2 = tempfile.mkdtemp(); STORE.clear()
    assert M.main(["--fault", "none", "--out", d2, "/x/a.bag"]) == 0 and len(STORE[os.path.join(d2, "a.bag")]) == 12000
