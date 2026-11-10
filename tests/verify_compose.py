"""Validate both manifests with Docker Compose; never start containers."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ComposeConfigurationTests(unittest.TestCase):
    def test_deployment_boundaries(self):
        environment = dict(os.environ, POSTGRES_PASSWORD="configuration-check-only",
                           JWT_SECRET="configuration-check-only-" + "x" * 64,
                           RELEASE="configuration-check")
        with tempfile.TemporaryDirectory() as directory:
            empty_env = Path(directory) / ".env"
            empty_env.touch()
            for manifest in ("docker-compose.yml", "compose.production.yml"):
                with self.subTest(manifest=manifest):
                    result = subprocess.run(
                        ["docker", "compose", "--env-file", str(empty_env),
                         "--project-directory", str(ROOT), "-f", str(ROOT / manifest),
                         "config", "--format", "json"],
                        env=environment, check=True, capture_output=True, text=True)
                    config = json.loads(result.stdout)
                    services = config["services"]
                    for name in ("postgres", "backend"):
                        self.assertFalse(services[name].get("ports"))
                    backend = services["backend"]["environment"]
                    self.assertEqual(backend["ASPNETCORE_ENVIRONMENT"], "Production")
                    self.assertEqual(backend["AppSettings__Token"], environment["JWT_SECRET"])
                    self.assertIn("Database=techblog;Username=techblog;Password=configuration-check-only",
                                  backend["ConnectionStrings__Postgres_Db"])
                    self.assertEqual(config["volumes"]["postgres_data"]["name"], "tech-blog_postgres_data")
                    for name in ("backend", "frontend"):
                        self.assertEqual(Path(services[name]["build"]["context"]).resolve(), ROOT / name)
                    if manifest == "compose.production.yml":
                        for service in services.values():
                            self.assertEqual(service["network_mode"], "host")
                            self.assertFalse(service.get("ports"))
                        self.assertIn("listen_addresses=127.0.0.1", services["postgres"]["command"])
                        self.assertIn("15432", services["postgres"]["command"])
                        self.assertEqual(backend["ASPNETCORE_URLS"], "http://127.0.0.1:18080")
                        self.assertIn("Host=127.0.0.1;Port=15432;", backend["ConnectionStrings__Postgres_Db"])
                        self.assertEqual(services["frontend"]["environment"]["BACKEND_UPSTREAM"], "127.0.0.1:18080")
                    else:
                        ports = services["frontend"]["ports"]
                        self.assertEqual(len(ports), 1)
                        self.assertEqual(ports[0]["host_ip"], "127.0.0.1")
                        self.assertEqual(str(ports[0]["published"]), "4200")
                        self.assertEqual(ports[0]["target"], 80)
                        self.assertEqual(services["frontend"]["environment"]["BACKEND_UPSTREAM"], "backend:8080")


if __name__ == "__main__":
    unittest.main(verbosity=2)
