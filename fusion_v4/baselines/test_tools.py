#!/usr/bin/env python3
"""Offline tests of check_isa.sh and load_image.sh (stand-in docker, no images): python3 test_tools.py  (from fusion_v4/baselines/)."""
import gzip
import hashlib
import os
import shutil
import subprocess
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ISA_SH = os.path.join(HERE, "check_isa.sh")
LOAD_SH = os.path.join(HERE, "load_image.sh")
HAVE_GCC = shutil.which("gcc") is not None and shutil.which("objdump") is not None

STUB = r"""#!/usr/bin/env bash
echo "$*" >> "$STUB_LOG"
case "$1" in
  info) case "$*" in *DockerRootDir*) echo "$STUB_ROOT" ;; esac; exit 0 ;;
  load) cat > /dev/null; touch "$STUB_LOADED"; exit 0 ;;
  image) [ "$2" = inspect ] || exit 0
         [ -f "$STUB_LOADED" ] || exit 1
         case "$*" in *--format*) echo "${STUB_LABEL:-0d822f6dcac3378312f6703b4f45829e049f221a}" ;; esac; exit 0 ;;
esac
exit 0
"""


class IsaCheck(unittest.TestCase):
    @unittest.skipUnless(HAVE_GCC, "no gcc/objdump")
    def test_avx512_fails_and_plain_passes(self):
        d = tempfile.mkdtemp()
        try:
            src = os.path.join(d, "t.c")
            with open(src, "w") as f:
                f.write("void f(float*a,float*b){for(int i=0;i<4096;i++)a[i]+=b[i]*2.0f;}\n")
            for name, flag in (("plain", []), ("wide", ["-mavx512f"])):
                os.makedirs(os.path.join(d, name))
                out = os.path.join(d, name, "libx.so")
                r = subprocess.run(["gcc", "-O3", "-c", src, "-o", out] + flag, capture_output=True, text=True)
                if r.returncode != 0:
                    self.skipTest("compiler cannot build %s" % name)
                os.chmod(out, 0o755)
            p = subprocess.run(["bash", ISA_SH, os.path.join(d, "plain")], capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stdout)
            self.assertIn("ISA CHECK: PASS", p.stdout)
            w = subprocess.run(["bash", ISA_SH, os.path.join(d, "wide")], capture_output=True, text=True)
            self.assertEqual(w.returncode, 1, w.stdout)
            self.assertIn("ISA CHECK: FAIL", w.stdout)
        finally:
            shutil.rmtree(d)

    def test_nothing_to_scan(self):
        d = tempfile.mkdtemp()
        try:
            r = subprocess.run(["bash", ISA_SH, d], capture_output=True, text=True)
            self.assertEqual(r.returncode, 2)
        finally:
            shutil.rmtree(d)


class LoadImage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.bin = os.path.join(self.tmp, "bin")
        os.makedirs(self.bin)
        with open(os.path.join(self.bin, "docker"), "w") as f:
            f.write(STUB)
        os.chmod(os.path.join(self.bin, "docker"), 0o755)
        self.log = os.path.join(self.tmp, "docker.log")
        self.tar = os.path.join(self.tmp, "lvisam_stock_0d822f6d.tar.gz")
        with gzip.open(self.tar, "wb") as f:
            f.write(b"not a real image")
        with open(self.tar, "rb") as f:
            h = hashlib.sha256(f.read()).hexdigest()
        with open(self.tar + ".sha256", "w") as f:
            f.write("%s  %s\n" % (h, os.path.basename(self.tar)))
        self.size(10 ** 6)
        with open(self.tar[:-7] + ".commit", "w") as f:
            f.write("0d822f6dcac3378312f6703b4f45829e049f221a\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def size(self, n):
        with open(self.tar[:-7] + ".size", "w") as f:
            f.write("%d\n" % n)

    def load(self, extra=None):
        env = dict(os.environ, PATH=self.bin + ":" + os.environ["PATH"], STUB_LOG=self.log, STUB_ROOT=self.tmp,
                   STUB_LOADED=os.path.join(self.tmp, "loaded"))
        env.update(extra or {})
        return subprocess.run(["bash", LOAD_SH, "lvisam_stock", "--from", self.tar], env=env, capture_output=True, text=True, timeout=60)

    def test_load_ok(self):
        r = self.load()
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("LOAD OK", r.stdout)
        self.assertIn(": OK", r.stdout)       # the checksum line

    def test_corrupt_file_is_refused_before_loading(self):
        with open(self.tar, "ab") as f:
            f.write(b"x")
        r = self.load()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("checksum mismatch", r.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "loaded")))

    def test_full_disk_is_refused_before_loading(self):
        self.size(10 ** 15)
        r = self.load()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("not enough free disk space", r.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.tmp, "loaded")))

    def test_shared_layers_lower_the_need(self):
        free = shutil.disk_usage(self.tmp).free
        gb = int(free / 1e9)
        self.size(free + 2 * 10 ** 9)
        self.assertNotEqual(self.load().returncode, 0)                       # needs more than is free
        self.assertEqual(self.load({"LOAD_ASSUME_SHARED_GB": str(3)}).returncode, 0, "gb free: %d" % gb)

    def test_commit_label_mismatch_fails(self):
        r = self.load({"STUB_LABEL": "deadbeef"})
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("does not match", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=1)
