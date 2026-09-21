"""Legacy interactive integration test.

It is intentionally opt-in because it generates code; generated code must be
validated by DockerSandboxExecutor, never executed by unittest on the host.
"""
import os
import unittest


@unittest.skipUnless(
    os.environ.get("RUN_DOCKER_GATEWAY_INTEGRATION") == "1",
    "requires a Docker-only integration harness",
)
class GatewayIntegrationTests(unittest.TestCase):
    def test_agent_loop(self):
        # This legacy loop has no Docker-only harness yet, so even an explicit
        # opt-in fails closed instead of executing generated code on the host.
        self.skipTest("Docker gateway harness is not implemented; host execution is forbidden")
