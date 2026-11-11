"""Tests for the Port Scanner v1 (lab targets only).

Run from the project folder:
    python -m unittest discover -s tests -v

All network activity is against localhost only: tests spin up their own
throwaway TCP servers on 127.0.0.1 and scan those.
"""

import socket
import sys
import threading
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import port_scanner


def _free_port() -> int:
    """A port that is (almost certainly) closed: bind one, then close it."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class _TestServer:
    """A throwaway TCP server on 127.0.0.1 that accepts and drops."""

    def __init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(5)
        self.port = self.sock.getsockname()[1]
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()

    def _serve(self) -> None:
        while True:
            try:
                conn, _ = self.sock.accept()
                conn.close()
            except OSError:
                return

    def close(self) -> None:
        self.sock.close()


class TestParsePorts(unittest.TestCase):
    def test_single_port(self):
        self.assertEqual(port_scanner.parse_ports("80"), [80])

    def test_range(self):
        self.assertEqual(port_scanner.parse_ports("20-22"), [20, 21, 22])

    def test_list(self):
        self.assertEqual(port_scanner.parse_ports("443,22,80"), [22, 80, 443])

    def test_mixed_list_and_range(self):
        self.assertEqual(
            port_scanner.parse_ports("22,80-82,443"), [22, 80, 81, 82, 443]
        )

    def test_duplicates_removed(self):
        self.assertEqual(port_scanner.parse_ports("80,80,80-81"), [80, 81])

    def test_rejects_zero_and_too_big(self):
        for bad in ("0", "65536", "0-10", "10-65536"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                port_scanner.parse_ports(bad)

    def test_rejects_reversed_range_and_garbage(self):
        for bad in ("10-5", "abc", "80-", "-80", "", "80,,443", "80-abc"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                port_scanner.parse_ports(bad)


class TestAuthorization(unittest.TestCase):
    def test_localhost_allowed(self):
        allowed, _ = port_scanner.authorize_target("localhost", False)
        self.assertTrue(allowed)

    def test_loopback_ip_allowed(self):
        allowed, _ = port_scanner.authorize_target("127.0.0.1", False)
        self.assertTrue(allowed)

    def test_private_ranges_allowed(self):
        for target in ("10.0.0.5", "172.16.0.1", "172.31.255.254", "192.168.1.10"):
            with self.subTest(target=target):
                allowed, _ = port_scanner.authorize_target(target, False)
                self.assertTrue(allowed)

    def test_public_ip_refused_without_flag(self):
        # 8.8.8.8 is a public address — refused unless the flag is given.
        allowed, message = port_scanner.authorize_target("8.8.8.8", False)
        self.assertFalse(allowed)
        self.assertIn("--i-have-permission", message)

    def test_public_ip_allowed_with_flag_but_warned(self):
        allowed, message = port_scanner.authorize_target("8.8.8.8", True)
        self.assertTrue(allowed)
        self.assertIn("WARNING", message)

    def test_unresolvable_target_refused(self):
        # Force DNS failure directly: this environment has a wildcard
        # resolver, so a fake hostname may "resolve" — mock the failure.
        with unittest.mock.patch(
            "socket.getaddrinfo", side_effect=socket.gaierror("no such host")
        ):
            allowed, message = port_scanner.authorize_target(
                "this-host-does-not-exist.invalid", False
            )
        self.assertFalse(allowed)
        self.assertIn("cannot resolve", message)


class TestScanning(unittest.TestCase):
    def test_open_port_detected(self):
        server = _TestServer()
        try:
            self.assertTrue(port_scanner.scan_port("127.0.0.1", server.port))
        finally:
            server.close()

    def test_closed_port_detected(self):
        self.assertFalse(port_scanner.scan_port("127.0.0.1", _free_port()))

    def test_scan_reports_open_and_closed(self):
        server = _TestServer()
        closed = _free_port()
        try:
            results, elapsed = port_scanner.scan(
                "127.0.0.1", [server.port, closed]
            )
            by_port = {r.port: r.is_open for r in results}
            self.assertTrue(by_port[server.port])
            self.assertFalse(by_port[closed])
            self.assertGreaterEqual(elapsed, 0)
        finally:
            server.close()

    def test_format_results_lists_open_ports(self):
        results = [
            port_scanner.PortResult(22, True),
            port_scanner.PortResult(80, False),
        ]
        text = port_scanner.format_results("127.0.0.1", results, 0.01)
        self.assertIn("OPEN", text)
        self.assertIn("closed", text)
        self.assertIn("1 open, 1 closed", text)
        self.assertIn("Open ports: 22", text)


class TestCli(unittest.TestCase):
    def test_demo_exits_zero_and_finds_open_port(self):
        self.assertEqual(port_scanner.main(["--demo"]), 0)

    def test_public_target_without_flag_exits_2(self):
        self.assertEqual(port_scanner.main(["8.8.8.8", "--ports", "80"]), 2)

    def test_bad_port_spec_exits_2(self):
        self.assertEqual(
            port_scanner.main(["127.0.0.1", "--ports", "not-a-port"]), 2
        )


if __name__ == "__main__":
    unittest.main()
