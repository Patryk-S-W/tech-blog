"""Run shell scripts against a fake Docker CLI; never contact a Docker daemon."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTAINER = "a" * 64
FAKE_DOCKER = r'''#!/usr/bin/env python3
import json, os, pathlib, sys
args = sys.argv[1:]
with open(os.environ["DOCKER_LOG"], "a") as log:
    log.write(json.dumps(args) + "\n")
stage = next((name for name in ("pg_dump", "pg_restore", "pg_isready", "psql")
              if any(name in arg for arg in args)), args[0])
if stage == "pg_restore":
    stage = "list" if "--list" in args else "restore"
if stage == "pg_dump":
    if os.environ.get("COLLISION"):
        output = pathlib.Path(os.environ["OUTPUT"])
        dump = next(output.glob(".backup.*/*.dump"))
        (output / dump.name).write_bytes(b"existing-backup")
    sys.stdout.buffer.write(b"custom-test-dump")
if stage in ("restore", "list"):
    sys.stdin.buffer.read()
if os.environ.get("DOCKER_FAIL") == stage:
    sys.stderr.write("private-error-sentinel")
    sys.exit(9)
if stage == "create": print("a" * 64)
if stage == "psql": print("2")
'''


class BackupScriptTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        docker = self.directory / "docker"
        docker.write_text(FAKE_DOCKER)
        docker.chmod(0o700)
        sleep = self.directory / "sleep"
        sleep.write_text("#!/bin/sh\nexit 0\n")
        sleep.chmod(0o700)
        self.log = self.directory / "docker.jsonl"
        self.output = self.directory / "backups"
        self.manifest = self.directory / "compose.yml"
        self.manifest.touch()
        self.env_file = self.directory / "explicit.env"
        self.env_file.touch()
        self.environment = dict(os.environ, PATH=str(self.directory) + os.pathsep + os.environ["PATH"],
                                DOCKER_LOG=str(self.log), OUTPUT=str(self.output))

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def run_script(self, script, *args, **environment):
        return subprocess.run(["bash", str(ROOT / "scripts" / script), *map(str, args)],
                              env=dict(self.environment, **environment), capture_output=True, text=True)

    def backup(self, **environment):
        return self.run_script("backup-postgres.sh", self.manifest, self.directory, "disposable-project",
                               self.env_file, self.output, "15432", **environment)

    def test_dump_permissions_checksum_and_explicit_context(self):
        result = self.backup()
        self.assertEqual(result.returncode, 0, result.stderr)
        dump, = self.output.glob("*.dump")
        checksum = Path(str(dump) + ".sha256")
        self.assertEqual(checksum.read_text().split()[0], hashlib.sha256(dump.read_bytes()).hexdigest())
        self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o700)
        for path in (dump, checksum):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertFalse(list(self.output.glob(".backup.*")))
        for call in self.calls():
            self.assertEqual(call[:9], ["compose", "--project-directory", str(self.directory), "--env-file",
                                      str(self.env_file), "-f", str(self.manifest), "-p", "disposable-project"])
            self.assertIn("postgres", call)
            self.assertNotIn("config", call)
        self.assertIn("15432", self.calls()[0])
        self.assertNotIn("--password", self.calls()[0])

    def test_failed_dump_or_validation_leaves_no_partial_files(self):
        for stage in ("pg_dump", "list"):
            with self.subTest(stage=stage):
                result = self.backup(DOCKER_FAIL=stage)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(list(self.output.iterdir()), [])
                self.assertNotIn("private-error-sentinel", result.stdout + result.stderr)

    def test_existing_backup_is_not_overwritten(self):
        result = self.backup(COLLISION="1")
        self.assertNotEqual(result.returncode, 0)
        dump, = self.output.glob("*.dump")
        self.assertEqual(dump.read_bytes(), b"existing-backup")
        self.assertEqual(list(self.output.glob("*.sha256")), [])
        self.assertFalse(list(self.output.glob(".backup.*")))

    def restore(self, **environment):
        dump = self.directory / "trusted.dump"
        dump.write_bytes(b"test-only-dump")
        return self.run_script("verify-postgres-restore.sh", dump, **environment)

    def test_restore_is_isolated_and_cleans_only_owned_id(self):
        result = self.restore()
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.calls()
        create = calls[0]
        self.assertEqual(create[create.index("--network") + 1], "none")
        self.assertIn("postgres:17-alpine", create)
        self.assertIn("--tmpfs", create)
        for forbidden in ("--publish", "-p", "--volume", "-v", "--mount", "compose", "host"):
            self.assertNotIn(forbidden, create)
        restore = next(call for call in calls if "pg_restore" in call)
        for required in ("-i", "--exit-on-error", "--no-owner", "--no-privileges", "restore_check"):
            self.assertIn(required, restore)
        self.assertEqual(calls[-1], ["rm", "-f", CONTAINER])
        self.assertTrue(all(CONTAINER in call for call in calls[1:]))

    def test_invalid_restore_is_cleaned_and_creation_collision_is_not(self):
        result = self.restore(DOCKER_FAIL="restore")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.calls()[-1], ["rm", "-f", CONTAINER])
        self.assertNotIn("private-error-sentinel", result.stdout + result.stderr)
        self.log.unlink()
        result = self.restore(DOCKER_FAIL="create")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(self.calls()), 1)

    def test_start_readiness_and_verification_failures_clean_owned_container(self):
        for stage in ("start", "pg_isready", "psql"):
            with self.subTest(stage=stage):
                if self.log.exists():
                    self.log.unlink()
                result = self.restore(DOCKER_FAIL=stage)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(self.calls()[-1], ["rm", "-f", CONTAINER])
                self.assertNotIn("private-error-sentinel", result.stdout + result.stderr)

    def test_unknown_arguments_fail_without_echo_or_docker(self):
        for script in ("backup-postgres.sh", "verify-postgres-restore.sh"):
            result = self.run_script(script, "--private-secret-sentinel")
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn("private-secret-sentinel", result.stdout + result.stderr)
        self.assertEqual(self.calls(), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
