#!/usr/bin/env python3
"""Dry run of run_lvisam.sh with a stand-in docker (no ROS, no bags): python3 test_run_lvisam.py  (from fusion_v4/stock_lvisam/)."""
import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
RUNNER = os.path.join(HERE, "run_lvisam.sh")

STUB = r"""#!/usr/bin/env bash
echo "$*" >> "$STUB_LOG"
case "$1" in
  info) exit 0 ;;
  image)
    [ -n "${STUB_NO_IMAGE:-}" ] && exit 1
    case "$*" in *--format*) echo 0d822f6dcac3378312f6703b4f45829e049f221a ;; esac
    exit 0 ;;
  run)
    if flock -n "$REPLAY_LOCK" true; then echo "LOCK=free $*" >> "$STUB_LOG"; else echo "LOCK=held $*" >> "$STUB_LOG"; fi
    case "$*" in
      *preflight.py*) echo "VERDICT=OK"; echo "ADAPT_NAN=${STUB_NAN:-0}"; echo "ADAPT_TIME=0"
                      echo "CAMERA_TOPIC_OK=${STUB_CAM:-yes}" ;;
      *inside.sh*)    out=$(echo "$*" | sed -n 's/.*-v \([^ ]*\):\/out.*/\1/p'); for i in $(seq 1 150); do echo "$i 0 0 0 0 0 0 1" >> "$out/odom.tum"; done
                      echo 0 > "$out/crashes.txt"; echo 0 > "$out/vins_reboots.txt" ;;
    esac
    exit 0 ;;
esac
exit 0
"""


class Runner(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.bin = os.path.join(self.tmp, "bin")
        os.makedirs(self.bin)
        with open(os.path.join(self.bin, "docker"), "w") as f:
            f.write(STUB)
        os.chmod(os.path.join(self.bin, "docker"), 0o755)
        self.log = os.path.join(self.tmp, "docker.log")
        self.slices = os.path.join(self.tmp, "slices")
        os.makedirs(self.slices)
        for n in ("geode", "mf"):
            open(os.path.join(self.slices, n + "_70s.bag"), "w").close()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_runner(self, seq, extra=None):
        env = dict(os.environ, PATH=self.bin + ":" + os.environ["PATH"], STUB_LOG=self.log, REPLAY_LOCK=os.path.join(self.tmp, "replay.lock"),
                   OUT_ROOT=os.path.join(self.tmp, "out"), HOME=self.tmp)
        env.update(extra or {})
        return subprocess.run(["bash", RUNNER, seq], env=env, capture_output=True, text=True, timeout=60)

    def calls(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log) as f:
            return f.read().splitlines()

    def test_slice_smoke_geode(self):
        r = self.run_runner("geode", {"SLICE": "1", "BAG_DIR": self.slices})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("SMOKE TEST", r.stdout)
        self.assertIn("PASS", r.stdout)
        runs = [c for c in self.calls() if c.startswith("LOCK=")]
        self.assertEqual(len(runs), 2)                                  # preflight + one run
        self.assertTrue(all(c.startswith("LOCK=held") for c in runs), runs)
        inside = [c for c in runs if "inside.sh" in c][0]
        self.assertIn("-e BAGS=geode_70s.bag", inside)
        self.assertIn("-e PLAY_SECONDS=60", inside)
        self.assertIn("-e CAM_COMPRESSED=1", inside)
        self.assertIn("-e CAM_TOPIC=/left_camera/image_raw", inside)
        self.assertIn("-e CAM_CONFIG=fusion_v4/geode/geode_config.yaml", inside)
        self.assertIn("/cam_check.py --topic /left_camera/compressed", [c for c in runs if "preflight.py" in c][0])
        self.assertIn("upstream commit 0d822f6", r.stdout)

    def test_mf_raw_camera_and_packets(self):
        r = self.run_runner("mf", {"SLICE": "1", "BAG_DIR": self.slices})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        inside = [c for c in self.calls() if c.startswith("LOCK=") and "inside.sh" in c][0]
        self.assertIn("-e PACKETS_TOPIC=/cmu_sp1/velodyne_packets", inside)
        self.assertIn("-e CAM_COMPRESSED=0", inside)
        self.assertIn("-e CAM_TOPIC=/cmu_sp1/camera_1/image_raw", inside)

    def test_missing_image_is_not_built(self):
        r = self.run_runner("geode", {"SLICE": "1", "BAG_DIR": self.slices, "STUB_NO_IMAGE": "1"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("load_image.sh", r.stdout)
        self.assertFalse([c for c in self.calls() if c.startswith("build")])
        self.assertFalse([c for c in self.calls() if c.startswith("run")])

    def test_no_camera_topic_is_not_applicable(self):
        r = self.run_runner("geode", {"SLICE": "1", "BAG_DIR": self.slices, "STUB_CAM": "no"})
        self.assertEqual(r.returncode, 0)
        self.assertIn("not run on geode", r.stdout)
        self.assertFalse([c for c in self.calls() if "inside.sh" in c])
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "out", "geode", "NOT_APPLICABLE.txt")))

    def test_unmounted_full_bags_refused(self):
        if subprocess.call(["mountpoint", "-q", "/tmp"]) == 0:
            self.skipTest("/tmp is a mount here")
        bags = os.path.join(self.tmp, "GEODE")
        os.makedirs(bags)
        open(os.path.join(bags, "stairs_alpha.bag"), "w").close()
        r = self.run_runner("geode", {"BAG_DIR": bags, "GT": "/dev/null"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not on a mounted drive", r.stderr)
        self.assertEqual(self.calls(), [])

    def test_repeat_and_run_numbers(self):
        r = self.run_runner("geode", {"SLICE": "1", "BAG_DIR": self.slices, "REPEAT": "2", "RUN_START": "2"})
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "out", "geode", "run2", "odom.tum")))
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "out", "geode", "run3", "odom.tum")))
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "out", "geode", "run1")))


if __name__ == "__main__":
    unittest.main(verbosity=1)
