import os
import sys
import unittest
from contextlib import ExitStack
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from services import mysql_storage  # noqa: E402


class FakeCursor:
    """Cursor en memoria que registra SQL y params ejecutados."""

    def __init__(self, rows=None, rowcount=1, fail=False):
        self.rows = rows or []
        self.rowcount = rowcount
        self.executed = []
        self.fail = fail

    def execute(self, sql, params=None):
        if self.fail:
            raise RuntimeError("connection lost")
        self.executed.append((sql, params))

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeConnection:
    def __init__(self, cursor=None, alive=True):
        self._cursor = cursor or FakeCursor()
        self.closed = False
        self.commits = 0
        self.open = alive

    def cursor(self):
        return self._cursor

    def commit(self):
        self.commits += 1

    def close(self):
        self.closed = True
        self.open = False


def _fake_db(fake):
    """Parchea el pool para que devuelva la conexión fake dada."""
    stack = ExitStack()
    stack.enter_context(
        mock.patch.object(mysql_storage, "_acquire_connection", return_value=fake)
    )
    stack.enter_context(
        mock.patch.object(mysql_storage, "_release_connection", lambda conn: None)
    )
    return stack


class MysqlStorageTest(unittest.TestCase):
    def test_decode_cards_handles_str(self):
        self.assertEqual(mysql_storage._decode_cards('{"a": 1}'), {"a": 1})

    def test_decode_cards_handles_list(self):
        self.assertEqual(mysql_storage._decode_cards([{"a": 1}]), [{"a": 1}])

    def test_decode_cards_handles_none(self):
        self.assertEqual(mysql_storage._decode_cards(None), [])

    def test_decode_cards_invalid_json(self):
        self.assertEqual(mysql_storage._decode_cards("no es json"), [])

    def test_create_project_inserts_and_returns(self):
        fake = FakeConnection()
        with _fake_db(fake):
            project = mysql_storage.create_project(
                "Mi proyecto", "Cusco", "dato-curioso", "instagram_portrait",
                [{"title": "T", "body": "B"}],
            )
        self.assertEqual(project["name"], "Mi proyecto")
        self.assertTrue(project["id"])
        self.assertEqual(project["cards"], [{"title": "T", "body": "B"}])
        self.assertEqual(fake.commits, 1)
        sql, params = fake._cursor.executed[0]
        self.assertTrue(sql.lstrip().upper().startswith("INSERT INTO PROJECTS"))
        self.assertEqual(params[0], project["id"])
        self.assertEqual(params[6], project["created_at"])

    def test_list_projects_builds_cards_count(self):
        cursor = FakeCursor(rows=[{
            "id": "abc", "name": "N", "destination": "D", "template": "t",
            "format": "f", "created_at": "c", "updated_at": "u",
            "cards": '[{"title": "T"}, {"title": "B"}]',
        }])
        fake = FakeConnection(cursor=cursor)
        with _fake_db(fake):
            projects = mysql_storage.list_projects()
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["cards_count"], 2)
        self.assertNotIn("cards", projects[0])

    def test_get_project_parses_cards(self):
        cursor = FakeCursor(rows=[{
            "id": "abc", "name": "N", "destination": "D", "template": "t",
            "format": "f", "created_at": "c", "updated_at": "u",
            "cards": '[{"title": "T"}]',
        }])
        fake = FakeConnection(cursor=cursor)
        with _fake_db(fake):
            project = mysql_storage.get_project("abc")
        self.assertEqual(project["cards"], [{"title": "T"}])
        self.assertEqual(project["id"], "abc")

    def test_get_project_not_found(self):
        fake = FakeConnection(cursor=FakeCursor(rows=[]))
        with _fake_db(fake):
            self.assertIsNone(mysql_storage.get_project("nada"))

    def test_update_project_dynamic_set(self):
        fake = FakeConnection()
        with _fake_db(fake):
            mysql_storage.update_project("abc", name="Nuevo", cards=[{"x": 1}])
        sql, params = fake._cursor.executed[0]
        self.assertIn("SET name=%s", sql)
        self.assertIn("cards=%s", sql)
        self.assertIn("updated_at=%s", sql)
        self.assertEqual(params[0], "Nuevo")
        self.assertEqual(params[-1], "abc")

    def test_update_project_empty_updates_returns_current(self):
        cursor = FakeCursor(rows=[{
            "id": "abc", "name": "N", "destination": "D", "template": "t",
            "format": "f", "created_at": "c", "updated_at": "u", "cards": "[]",
        }])
        fake = FakeConnection(cursor=cursor)
        with _fake_db(fake):
            project = mysql_storage.update_project("abc")
        self.assertIsNotNone(project)
        # Sin cambios no hace UPDATE; solo el SELECT de get_project.
        sql, _ = fake._cursor.executed[0]
        self.assertTrue(sql.lstrip().upper().startswith("SELECT"))

    def test_delete_project_uses_rowcount(self):
        fake = FakeConnection(cursor=FakeCursor(rowcount=1))
        with _fake_db(fake):
            self.assertTrue(mysql_storage.delete_project("abc"))
        fake2 = FakeConnection(cursor=FakeCursor(rowcount=0))
        with _fake_db(fake2):
            self.assertFalse(mysql_storage.delete_project("abc"))

    def test_export_all_returns_full_rows(self):
        cursor = FakeCursor(rows=[{
            "id": "abc", "name": "N", "destination": "D", "template": "t",
            "format": "f", "created_at": "c", "updated_at": "u",
            "cards": '[{"title": "T"}]',
        }])
        fake = FakeConnection(cursor=cursor)
        with _fake_db(fake):
            projects = mysql_storage.export_all()
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["cards"], [{"title": "T"}])

    def test_restore_upserts_rows(self):
        fake = FakeConnection()
        with _fake_db(fake):
            n = mysql_storage.restore([
                {"id": "x", "name": "N", "destination": "D", "cards": [{"a": 1}]}
            ])
        self.assertEqual(n, 1)
        self.assertEqual(fake.commits, 1)
        sql, params = fake._cursor.executed[0]
        self.assertIn("ON DUPLICATE KEY UPDATE", sql)
        self.assertEqual(params[0], "x")


class PoolTest(unittest.TestCase):
    def setUp(self):
        mysql_storage.close_pool()

    def tearDown(self):
        mysql_storage.close_pool()

    def test_acquire_creates_new_when_pool_empty(self):
        fake = FakeConnection()
        with mock.patch.object(mysql_storage, "_connect", return_value=fake):
            conn = mysql_storage._acquire_connection()
        self.assertIs(conn, fake)

    def test_acquire_reuses_released_connection(self):
        fake = FakeConnection()
        with mock.patch.object(mysql_storage, "_connect", return_value=fake):
            conn1 = mysql_storage._acquire_connection()
            mysql_storage._release_connection(conn1)
            conn2 = mysql_storage._acquire_connection()
        self.assertIs(conn1, conn2)

    def test_release_closes_when_pool_full(self):
        mysql_storage.POOL_MAXSIZE = 1
        mysql_storage.close_pool()  # recrea el pool con maxsize 1
        c1 = FakeConnection()
        c2 = FakeConnection()
        with mock.patch.object(mysql_storage, "_connect", side_effect=[c1, c2]):
            a1 = mysql_storage._acquire_connection()
            self.assertIs(a1, c1)
            mysql_storage._release_connection(a1)  # el pool queda lleno (1)
            # Liberar una conexión extra: no cabe -> se cierra
            mysql_storage._release_connection(c2)
        self.assertTrue(c2.closed)

    def test_acquire_reconnects_dead_connection(self):
        stale = FakeConnection()
        fresh = FakeConnection()
        with mock.patch.object(mysql_storage, "_connect", side_effect=[stale, fresh]):
            mysql_storage._acquire_connection()  # crea el pool y toma stale
            mysql_storage._release_connection(stale)  # viva -> al pool
            stale.open = False  # el servidor la dejó caer entre peticiones
            conn = mysql_storage._acquire_connection()
        self.assertIs(conn, fresh)
        self.assertTrue(stale.closed)

    def test_connection_alive_returns_false_when_open_false(self):
        conn = FakeConnection(alive=False)
        self.assertFalse(mysql_storage._connection_alive(conn))

    def test_connection_alive_detects_execute_failure(self):
        conn = FakeConnection(cursor=FakeCursor(fail=True))
        self.assertFalse(mysql_storage._connection_alive(conn))
        self.assertTrue(conn.closed)


if __name__ == "__main__":
    unittest.main()
