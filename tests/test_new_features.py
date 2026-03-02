"""
Lightweight unit tests for the new features:
  - audit_targets forks filtering in github_api
  - kCTF saved entries DB helpers
  - create_audit_embed forks/releases fields
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Ensure repo root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---------------------------------------------------------------------------
# DB / CRUD tests (use a temp file so we don't touch the real DB)
# ---------------------------------------------------------------------------
class TestKCTFCrud(unittest.TestCase):
    def setUp(self):
        self._db_fd, self._db_path = tempfile.mkstemp(suffix=".db")
        # Patch the DB_PATH used by setup and crud modules
        import db.setup as setup_mod
        import db.crud as crud_mod
        self._orig_setup_path = setup_mod.DB_PATH
        self._orig_crud_path = crud_mod.DB_PATH
        setup_mod.DB_PATH = self._db_path
        crud_mod.DB_PATH = self._db_path
        setup_mod.init_db()

    def tearDown(self):
        import db.setup as setup_mod
        import db.crud as crud_mod
        setup_mod.DB_PATH = self._orig_setup_path
        crud_mod.DB_PATH = self._orig_crud_path
        os.close(self._db_fd)
        os.unlink(self._db_path)

    def test_save_kctf_entry_new(self):
        from db.crud import save_kctf_entry, get_saved_kctf_entries
        result = save_kctf_entry("user1", "issue-123", "commit-abc", "2024-01-01", "Alice", "500")
        self.assertTrue(result)
        entries = get_saved_kctf_entries("user1")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["issue"], "issue-123")
        self.assertEqual(entries[0]["submitter"], "Alice")
        self.assertEqual(entries[0]["reward"], "500")

    def test_save_kctf_entry_duplicate(self):
        from db.crud import save_kctf_entry
        save_kctf_entry("user1", "issue-123", "", "", "", "")
        result = save_kctf_entry("user1", "issue-123", "", "", "", "")
        self.assertFalse(result, "Duplicate save should return False")

    def test_save_kctf_entry_different_users(self):
        from db.crud import save_kctf_entry, get_saved_kctf_entries
        save_kctf_entry("user1", "issue-123", "", "", "", "")
        save_kctf_entry("user2", "issue-123", "", "", "", "")
        self.assertEqual(len(get_saved_kctf_entries("user1")), 1)
        self.assertEqual(len(get_saved_kctf_entries("user2")), 1)

    def test_delete_kctf_entry(self):
        from db.crud import save_kctf_entry, get_saved_kctf_entries, delete_kctf_entry
        save_kctf_entry("user1", "issue-123", "", "", "", "")
        delete_kctf_entry("user1", "issue-123")
        self.assertEqual(get_saved_kctf_entries("user1"), [])

    def test_get_saved_kctf_entries_empty(self):
        from db.crud import get_saved_kctf_entries
        self.assertEqual(get_saved_kctf_entries("nobody"), [])


# ---------------------------------------------------------------------------
# github_api forks filter query construction
# ---------------------------------------------------------------------------
class TestFetchAuditTargetsForksFilter(unittest.TestCase):
    """Verify that forks qualifiers are included in the GitHub search query."""

    def _run_fetch(self, min_forks, max_forks, mock_get):
        """Helper: run fetch_audit_targets and return all query strings used."""
        from github_api import GITHUBAPI
        api = GITHUBAPI(github_key=None)
        import asyncio
        asyncio.run(api.fetch_audit_targets(min_forks=min_forks, max_forks=max_forks, page=1))
        queries = [call.args[0] for call in mock_get.call_args_list]
        # Also check keyword args
        queries += [call.kwargs.get("params", {}).get("q", "") for call in mock_get.call_args_list]
        return queries

    def _mock_response(self):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"items": []}
        return resp

    @patch("github_api.requests.get")
    def test_no_forks_filter_when_both_zero(self, mock_get):
        mock_get.return_value = self._mock_response()
        from github_api import GITHUBAPI
        import asyncio
        api = GITHUBAPI(github_key=None)
        asyncio.run(api.fetch_audit_targets(min_forks=0, max_forks=0))
        for call in mock_get.call_args_list:
            q = call.kwargs.get("params", {}).get("q", "")
            self.assertNotIn("forks:", q)

    @patch("github_api.requests.get")
    def test_min_forks_only(self, mock_get):
        mock_get.return_value = self._mock_response()
        from github_api import GITHUBAPI
        import asyncio
        api = GITHUBAPI(github_key=None)
        asyncio.run(api.fetch_audit_targets(min_forks=5, max_forks=0))
        for call in mock_get.call_args_list:
            q = call.kwargs.get("params", {}).get("q", "")
            self.assertIn("forks:>=5", q)

    @patch("github_api.requests.get")
    def test_max_forks_only(self, mock_get):
        mock_get.return_value = self._mock_response()
        from github_api import GITHUBAPI
        import asyncio
        api = GITHUBAPI(github_key=None)
        asyncio.run(api.fetch_audit_targets(min_forks=0, max_forks=100))
        for call in mock_get.call_args_list:
            q = call.kwargs.get("params", {}).get("q", "")
            self.assertIn("forks:0..100", q)

    @patch("github_api.requests.get")
    def test_min_and_max_forks(self, mock_get):
        mock_get.return_value = self._mock_response()
        from github_api import GITHUBAPI
        import asyncio
        api = GITHUBAPI(github_key=None)
        asyncio.run(api.fetch_audit_targets(min_forks=5, max_forks=100))
        for call in mock_get.call_args_list:
            q = call.kwargs.get("params", {}).get("q", "")
            self.assertIn("forks:5..100", q)

    @patch("github_api.requests.get")
    def test_forks_included_in_returned_repo(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"items": [{
            "name": "myrepo",
            "owner": {"login": "owner1"},
            "html_url": "https://github.com/owner1/myrepo",
            "stargazers_count": 50,
            "forks_count": 12,
            "size": 500,
            "language": "C",
            "pushed_at": "2020-01-01T00:00:00Z",
            "description": "A test repo",
        }]}
        mock_get.return_value = resp
        from github_api import GITHUBAPI
        import asyncio
        api = GITHUBAPI(github_key=None)
        repos = asyncio.run(api.fetch_audit_targets())
        self.assertTrue(any(r.get("forks") == 12 for r in repos))


# ---------------------------------------------------------------------------
# create_audit_embed forks and releases fields
# ---------------------------------------------------------------------------
class TestCreateAuditEmbed(unittest.TestCase):
    def _make_repo(self, **kwargs):
        base = {
            "name": "testrepo",
            "url": "https://github.com/owner/testrepo",
            "description": "Test",
            "owner": "owner",
            "language": "C",
            "stars": 42,
            "size_kb": 100,
            "last_push": "2020-01-01",
        }
        base.update(kwargs)
        return base

    def test_forks_field_present(self):
        from pagination import create_audit_embed
        repo = self._make_repo(forks=7)
        embed = create_audit_embed(repo)
        field_names = [f.name for f in embed.fields]
        self.assertIn("Forks", field_names)
        forks_field = next(f for f in embed.fields if f.name == "Forks")
        self.assertEqual(forks_field.value, "7")

    def test_forks_field_na_when_missing(self):
        from pagination import create_audit_embed
        repo = self._make_repo()  # no 'forks' key
        embed = create_audit_embed(repo)
        field_names = [f.name for f in embed.fields]
        self.assertIn("Forks", field_names)
        forks_field = next(f for f in embed.fields if f.name == "Forks")
        self.assertEqual(forks_field.value, "N/A")

    def test_releases_field_shown_when_true(self):
        from pagination import create_audit_embed
        repo = self._make_repo(forks=0, has_releases=True)
        embed = create_audit_embed(repo)
        field_names = [f.name for f in embed.fields]
        self.assertIn("Releases", field_names)
        rel_field = next(f for f in embed.fields if f.name == "Releases")
        self.assertIn("✅", rel_field.value)

    def test_releases_field_shown_when_false(self):
        from pagination import create_audit_embed
        repo = self._make_repo(forks=0, has_releases=False)
        embed = create_audit_embed(repo)
        field_names = [f.name for f in embed.fields]
        self.assertIn("Releases", field_names)
        rel_field = next(f for f in embed.fields if f.name == "Releases")
        self.assertIn("❌", rel_field.value)

    def test_releases_field_absent_when_not_checked(self):
        from pagination import create_audit_embed
        repo = self._make_repo(forks=0)  # no 'has_releases' key
        embed = create_audit_embed(repo)
        field_names = [f.name for f in embed.fields]
        self.assertNotIn("Releases", field_names)


# ---------------------------------------------------------------------------
# fetch_has_releases
# ---------------------------------------------------------------------------
class TestFetchHasReleases(unittest.TestCase):
    @patch("github_api.requests.get")
    def test_returns_true_when_releases_found(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = [{"id": 1}]
        mock_get.return_value = resp
        from github_api import GITHUBAPI
        api = GITHUBAPI(github_key=None)
        self.assertTrue(api.fetch_has_releases("owner", "repo"))

    @patch("github_api.requests.get")
    def test_returns_false_when_no_releases(self, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = []
        mock_get.return_value = resp
        from github_api import GITHUBAPI
        api = GITHUBAPI(github_key=None)
        self.assertFalse(api.fetch_has_releases("owner", "repo"))

    @patch("github_api.requests.get")
    def test_returns_false_on_api_error(self, mock_get):
        resp = MagicMock()
        resp.status_code = 404
        resp.json.return_value = {}
        mock_get.return_value = resp
        from github_api import GITHUBAPI
        api = GITHUBAPI(github_key=None)
        self.assertFalse(api.fetch_has_releases("owner", "repo"))

    @patch("github_api.requests.get", side_effect=Exception("timeout"))
    def test_returns_false_on_exception(self, mock_get):
        from github_api import GITHUBAPI
        api = GITHUBAPI(github_key=None)
        self.assertFalse(api.fetch_has_releases("owner", "repo"))


if __name__ == "__main__":
    unittest.main()
