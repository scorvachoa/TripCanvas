import time
import unittest

from services import rate_limit


class _FakeClient:
    host = "203.0.113.7"


class _FakeRequest:
    client = _FakeClient()


class RateLimitTest(unittest.TestCase):
    def setUp(self):
        rate_limit._hits.clear()

    def tearDown(self):
        rate_limit._hits.clear()

    def test_allows_requests_within_limit(self):
        dep = rate_limit.rate_limit(max_requests=3, window_seconds=60)
        for _ in range(3):
            dep(_FakeRequest())  # no debe lanzar

    def test_blocks_over_limit(self):
        dep = rate_limit.rate_limit(max_requests=2, window_seconds=60)
        dep(_FakeRequest())
        dep(_FakeRequest())
        with self.assertRaises(Exception):
            dep(_FakeRequest())

    def test_expired_window_allows_again(self):
        dep = rate_limit.rate_limit(max_requests=1, window_seconds=1)
        dep(_FakeRequest())
        time.sleep(1.05)
        dep(_FakeRequest())  # no debe lanzar

    def test_separates_clients_by_ip(self):
        dep = rate_limit.rate_limit(max_requests=1, window_seconds=60)
        dep(_FakeRequest())
        other = _FakeRequest()
        other.client.host = "198.51.100.9"
        dep(other)  # distinta IP, no debe lanzar


if __name__ == "__main__":
    unittest.main()
