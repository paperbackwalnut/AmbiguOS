import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from ambiguos.intent import IntentError, apply, infer, main, validate_decision


def decision(action='file', path='notes.txt'):
    return dict(version=1, action=action, path=path, reason='A record is indicated.')


class FilesystemTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name).resolve()
        self.root = self.base / 'root'

    def test_file_and_parents(self):
        apply(decision(path='a/b'), self.root)
        self.assertEqual((self.root / 'a/b').read_bytes(), b'')

    def test_directory(self):
        apply(decision('directory', 'notes'), self.root)
        self.assertTrue((self.root / 'notes').is_dir())

    def test_preview(self):
        self.assertTrue(apply(decision(), self.root, True))
        self.assertFalse(self.root.exists())

    def test_defer(self):
        self.assertFalse(apply(decision('defer'), self.root))
        self.assertFalse(self.root.exists())

    def test_existing_path(self):
        self.root.mkdir()
        target = self.root / 'notes.txt'
        target.write_text('preserve')
        with self.assertRaises(IntentError):
            apply(decision(), self.root)
        self.assertEqual(target.read_text(), 'preserve')

    def test_unsafe_paths(self):
        for path in ('../outside', '/tmp/outside', 'a/../b', './a', 'a//b', 'a/', '', 'a\\b', 'a\nb'):
            with self.subTest(path=path), self.assertRaises(IntentError):
                apply(decision(path=path), self.root)
        self.assertFalse(self.root.exists())

    def test_symlink_parent(self):
        self.root.mkdir()
        outside = self.base / 'outside'
        outside.mkdir()
        (self.root / 'link').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(IntentError):
            apply(decision(path='link/file'), self.root)
        self.assertFalse((outside / 'file').exists())

    def test_symlink_root_and_target(self):
        self.root.symlink_to(self.base / 'missing', target_is_directory=True)
        with self.assertRaises(IntentError):
            apply(decision(), self.root)
        self.root.unlink()
        self.root.mkdir()
        (self.root / 'notes.txt').symlink_to(self.base / 'missing')
        with self.assertRaises(IntentError):
            apply(decision(), self.root)

    def test_cli_replay(self):
        record = self.base / 'record.json'
        record.write_text(json.dumps(decision('defer')))
        with contextlib.redirect_stdout(io.StringIO()) as out:
            result = main(['requested', '--replay', str(record), '--root', str(self.root)])
        self.assertEqual(result, 3)
        self.assertFalse(json.loads(out.getvalue())['applied'])

    def test_cli_bad_record(self):
        record = self.base / 'record.json'
        for value in ('invalid', '{}', 'x' * 65537):
            record.write_text(value)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(['a', '--replay', str(record)]), 1)

    def test_staged_install(self):
        repo = Path(__file__).resolve().parents[1]
        stage = self.base / 'stage'
        subprocess.run(['make', 'install', 'DESTDIR=' + str(stage), 'PREFIX=/usr'],
                       cwd=repo, check=True, stdout=subprocess.DEVNULL)
        result = subprocess.run([str(stage / 'usr/bin/ambimk'), 'notes.txt',
                                 '--replay', str(repo / 'examples/decisions/file.json'),
                                 '--root', str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / 'notes.txt').is_file())


class ProtocolTests(unittest.TestCase):
    def test_schema(self):
        for value in (None, [], {}, dict(decision(), extra=1), dict(decision(), version=True),
                      dict(decision(), version=2), dict(decision(), action='shell'),
                      dict(decision(), reason=''), dict(decision(), reason='a' * 1025)):
            with self.subTest(value=value), self.assertRaises(IntentError):
                validate_decision(value)

    def test_endpoint_restrictions(self):
        for endpoint in ('https://127.0.0.1', 'http://example.com', 'http://localhost/api',
                         'http://user@localhost', 'http://localhost?x=1'):
            with self.subTest(endpoint=endpoint), self.assertRaises(IntentError):
                infer({}, endpoint, 'test', 1)

    def test_transport(self):
        captured = []
        replies = [json.dumps({'response': json.dumps(decision('directory', 'notes'))}).encode(),
                   b'{"response":"invalid"}', b'{}', b'x' * 65537]

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                captured.append((self.path, json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(replies.pop(0))

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            endpoint = 'http://127.0.0.1:' + str(server.server_port)
            request = dict(version=1, path='notes.txt', kind='file', context='a collection')
            self.assertEqual(infer(request, endpoint, 'smollm2:135m', 2)['action'], 'directory')
            path, payload = captured[0]
            self.assertEqual(path, '/api/generate')
            self.assertEqual(json.loads(payload['prompt']), request)
            self.assertFalse(payload['stream'])
            self.assertEqual(payload['model'], 'smollm2:135m')
            for _ in range(3):
                with self.assertRaises(IntentError):
                    infer(request, endpoint, 'test', 2)
        finally:
            server.shutdown()
            server.server_close()
            worker.join()


if __name__ == '__main__':
    unittest.main()
