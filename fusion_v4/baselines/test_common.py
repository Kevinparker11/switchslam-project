#!/usr/bin/env python3
"""Offline tests of baselines/common.sh and of the stock LIO-SAM runner's drive and lock checks (no ROS, no docker).
python3 test_common.py   (from fusion_v4/baselines/). Needs a tmpfs mount at /dev/shm for the "mounted" case."""
import os
import shutil
import subprocess
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
COMMON = os.path.join(HERE, "common.sh")
RUNNER = os.path.join(HERE, "..", "stock_liosam", "run_liosam.sh")
SHM = "/dev/shm"
HAVE_SHM = subprocess.call(["mountpoint", "-q", SHM]) == 0


def sh(script, env=None, timeout=30):
    e = dict(os.environ)
    e.update(env or {})
    return subprocess.run(["bash", "-c", "set -u; source '%s'; %s" % (COMMON, script)], env=e,
                          capture_output=True, text=True, timeout=timeout)


class Mount(unittest.TestCase):
    def setUp(self):
        self.local = tempfile.mkdtemp(dir="/tmp")          # /tmp is on / in the sandbox
        self.env = {"ALLOW_LOCAL_BAGS": "0"}

    def tearDown(self):
        shutil.rmtree(self.local, ignore_errors=True)

    def test_system_disk_is_refused(self):
        if subprocess.call(["mountpoint", "-q", "/tmp"]) == 0:
            self.skipTest("/tmp is a mount here")
        r = sh("bl_require_mounted '%s'; echo PASSED" % self.local, self.env)
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn("PASSED", r.stdout)
        self.assertIn("not on a mounted drive", r.stderr)

    def test_allow_local_bags(self):
        r = sh("bl_require_mounted '%s'; echo PASSED" % self.local, {"ALLOW_LOCAL_BAGS": "1"})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("PASSED", r.stdout)

    def test_missing_folder_is_refused(self):
        r = sh("bl_require_mounted '%s/nope'; echo PASSED" % self.local, {"ALLOW_LOCAL_BAGS": "1"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not found", r.stderr)

    @unittest.skipUnless(HAVE_SHM, "no tmpfs at /dev/shm")
    def test_mounted_drive_passes_with_spaces(self):
        d = tempfile.mkdtemp(dir=SHM, prefix="One Touch2 ")
        try:
            os.makedirs(os.path.join(d, "laptop_bags", "GEODE"))
            r = sh("bl_require_mounted '%s/laptop_bags/GEODE'; echo PASSED" % d, self.env)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("bags on mount %s" % SHM, r.stdout)
        finally:
            shutil.rmtree(d)

    def test_find_skips_leftover_folder_on_system_disk(self):
        u = "bltest%d" % os.getpid()
        leftover = "/media/%s/One Touch1/laptop_bags" % u
        try:
            os.makedirs(leftover)
        except PermissionError:
            self.skipTest("cannot write /media")
        try:
            r = sh("unset BAGS_ROOT; bl_find_bags_root; echo \"GOT=$BAGS_ROOT\"", {"USER": u})
            if subprocess.call(["mountpoint", "-q", "/media"]) != 0:
                self.assertNotEqual(r.returncode, 0)
                self.assertNotIn("GOT=", r.stdout)
                self.assertIn("no mounted drive", r.stderr)
        finally:
            shutil.rmtree("/media/%s" % u)

    def test_preset_bags_root_is_kept(self):
        r = sh("bl_find_bags_root; echo \"GOT=$BAGS_ROOT\"", {"BAGS_ROOT": "/some/where"})
        self.assertEqual(r.returncode, 0)
        self.assertIn("GOT=/some/where", r.stdout)


class Lock(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.lock = os.path.join(self.d, "replay.lock")

    def tearDown(self):
        shutil.rmtree(self.d, ignore_errors=True)

    def test_waits_for_a_plain_flock_holder(self):
        # the F35 runner may use the plain form "flock ~/.replay.lock <cmd>"; ours must wait for it
        holder = subprocess.Popen(["flock", self.lock, "sleep", "2"])
        time.sleep(0.3)
        t0 = time.time()
        r = sh("bl_lock; echo IN; bl_unlock", {"REPLAY_LOCK": self.lock})
        waited = time.time() - t0
        holder.wait()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("waiting for", r.stdout)
        self.assertGreater(waited, 1.2)

    def test_held_during_and_free_after(self):
        r = sh("bl_lock; flock -n '%s' true && echo FREE_INSIDE || echo HELD_INSIDE; bl_unlock; "
               "flock -n '%s' true && echo FREE_AFTER" % (self.lock, self.lock), {"REPLAY_LOCK": self.lock})
        self.assertIn("HELD_INSIDE", r.stdout)
        self.assertIn("FREE_AFTER", r.stdout)

    def test_no_wait_when_free(self):
        r = sh("bl_lock; bl_unlock; echo OK", {"REPLAY_LOCK": self.lock})
        self.assertNotIn("waiting", r.stdout)
        self.assertIn("OK", r.stdout)


STUB = """#!/usr/bin/env bash
# stand-in docker: logs each call and whether the replay lock is held at that moment
echo "$*" >> "$STUB_LOG"
case "$1" in
  info|image) exit 0 ;;
  run)
    if flock -n "$REPLAY_LOCK" true; then echo "LOCK=free $*" >> "$STUB_LOG"; else echo "LOCK=held $*" >> "$STUB_LOG"; fi
    case "$*" in *preflight.py*) echo "VERDICT=OK" ;; esac
    exit 0 ;;
esac
exit 0
"""


class RunnerDryRun(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.bin = os.path.join(self.tmp, "bin")
        os.makedirs(self.bin)
        with open(os.path.join(self.bin, "docker"), "w") as f:
            f.write(STUB)
        os.chmod(os.path.join(self.bin, "docker"), 0o755)
        self.log = os.path.join(self.tmp, "docker.log")
        self.gt = os.path.join(self.tmp, "gt.txt")
        with open(self.gt, "w") as f:
            f.write("0 0 0 0 0 0 0 1\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_runner(self, bag_dir, extra=None):
        env = dict(os.environ, PATH=self.bin + ":" + os.environ["PATH"], STUB_LOG=self.log,
                   REPLAY_LOCK=os.path.join(self.tmp, "replay.lock"), BAG_DIR=bag_dir, GT=self.gt,
                   OUT_ROOT=os.path.join(self.tmp, "out"), REPEAT="2", ALLOW_LOCAL_BAGS="0")
        env.update(extra or {})
        return subprocess.run(["bash", RUNNER, "geode"], env=env, capture_output=True, text=True, timeout=60)

    def calls(self):
        if not os.path.exists(self.log):
            return []
        with open(self.log) as f:
            return f.read().splitlines()

    def test_unmounted_bags_never_reach_docker(self):
        if subprocess.call(["mountpoint", "-q", "/tmp"]) == 0:
            self.skipTest("/tmp is a mount here")
        bags = os.path.join(self.tmp, "GEODE")
        os.makedirs(bags)
        open(os.path.join(bags, "stairs_alpha.bag"), "w").close()
        r = self.run_runner(bags)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not on a mounted drive", r.stderr)
        self.assertEqual(self.calls(), [])

    @unittest.skipUnless(HAVE_SHM, "no tmpfs at /dev/shm")
    def test_every_docker_run_holds_the_lock(self):
        d = tempfile.mkdtemp(dir=SHM, prefix="One Touch2 ")
        try:
            bags = os.path.join(d, "GEODE")
            os.makedirs(bags)
            open(os.path.join(bags, "stairs_alpha.bag"), "w").close()
            self.run_runner(bags)
            runs = [c for c in self.calls() if c.startswith("LOCK=")]
            self.assertEqual(len(runs), 3, self.calls())               # preflight + 2 runs
            self.assertTrue(all(c.startswith("LOCK=held") for c in runs), runs)
            self.assertEqual(sum("inside.sh" in c for c in runs), 2)
            self.assertIn("info", self.calls())
        finally:
            shutil.rmtree(d)


if __name__ == "__main__":
    unittest.main(verbosity=1)
