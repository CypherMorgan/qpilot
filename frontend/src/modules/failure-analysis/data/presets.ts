/** CI/CD failure log presets — one-click demo scenarios. */

import type { InputSourceType } from "@/modules/failure-analysis/types";

export interface FailurePreset {
  id: string;
  title: string;
  description: string;
  sourceType: InputSourceType;
  content: string;
  category: string;
}

export const FAILURE_PRESETS: FailurePreset[] = [
  {
    id: "assertion-error",
    title: "Assertion Error",
    description: "A pytest assertion failure in a login test",
    category: "assertion_error",
    sourceType: "stack_trace",
    content: `FAILED tests/integration/test_auth.py::test_login_success - AssertionError: assert 401 == 200

─── Test session summary ───────────────────────────────────────────
platform linux -- Python 3.12.4
rootdir: /workspace/app
plugins: asyncio-0.24.0, cov-5.0.0
collected 1 item

tests/integration/test_auth.py::test_login_success FAILED        [100%]

─── Log output ─────────────────────────────────────────────────────
INFO     2026-07-14 10:32:15 | test_auth.py:42 | Sending POST /api/v1/auth/login
INFO     2026-07-14 10:32:15 | test_auth.py:44 | Request body: {"email": "test@example.com", "password": "***"}
INFO     2026-07-14 10:32:15 | test_auth.py:46 | Response status: 401
INFO     2026-07-14 10:32:15 | test_auth.py:48 | Response body: {"detail":"Invalid credentials"}
ERROR    2026-07-14 10:32:15 | test_auth.py:50 | Expected 200, got 401

─── Stack trace ────────────────────────────────────────────────────
tests/integration/test_auth.py:60: in test_login_success
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
E   AssertionError: Expected 200, got 401
E   assert 401 == 200`,
  },
  {
    id: "timeout",
    title: "Test Timeout",
    description: "A long-running test that exceeded the time limit",
    category: "timeout",
    sourceType: "ci_log",
    content: `FAILED tests/integration/test_report_generation.py::test_generate_monthly_report - TimeoutError: Test exceeded 30s timeout

─── CI run details ─────────────────────────────────────────────────
Job: integration-tests (py3.12)
Runner: ubuntu-latest (GitHub Actions)
Duration: 32.4s
Timeout: 30s

─── Slow operations detected ───────────────────────────────────────
  • tests/integration/test_report_generation.py:85 — SQL query — 14.2s
  • tests/integration/test_report_generation.py:92 — PDF rendering — 8.7s
  • tests/integration/test_report_generation.py:103 — S3 upload — 5.1s

─── Last log lines ─────────────────────────────────────────────────
[10:45:12]  INFO | Generating report for period 2026-Q2...
[10:45:26]  INFO | Fetching 12,483 records from analytics_db
[10:45:40]  INFO | Aggregating data...
[10:45:42]  INFO | Rendering PDF template (A4, 24 pages)
[10:45:44] WARN  | Memory usage: 1.2 GB / 2.0 GB
[10:45:44]  INFO | Uploading to S3: reports/2026-Q2/monthly-report.pdf
[TIMEOUT] ❌ Job terminated after 30s`,
  },
  {
    id: "missing-dependency",
    title: "Missing Dependency",
    description: "A Python module not found during test collection",
    category: "dependency",
    sourceType: "ci_log",
    content: `ERROR collecting tests/unit/test_ml_pipeline.py
ModuleNotFoundError: No module named 'tensorflow'

─── CI run details ─────────────────────────────────────────────────
Job: unit-tests (py3.11)
Runner: ubuntu-latest
Trigger: push to feature/ml-refactor

─── Pip freeze (relevant) ──────────────────────────────────────────
numpy==1.26.4
pandas==2.2.1
scikit-learn==1.5.0
torch==2.3.0
# tensorflow is MISSING

─── requirements.txt ───────────────────────────────────────────────
# Found in repo root, but tensorflow only listed under [ml] extra
# Install with: pip install -e .[ml]

─── Error details ──────────────────────────────────────────────────
tests/unit/test_ml_pipeline.py:3: in <module>
    from tensorflow.keras.models import load_model
ModuleNotFoundError: No module named 'tensorflow'

─── CI step log ────────────────────────────────────────────────────
$ pip install -e .
  Successfully installed qpilot-0.4.0
$ pytest tests/unit/test_ml_pipeline.py -v
  ERROR: ModuleNotFoundError`,
  },
  {
    id: "flaky-test",
    title: "Flaky Test",
    description: "An intermittently failing integration test",
    category: "assertion_error",
    sourceType: "plain_text",
    content: `FLAKY: tests/integration/test_notifications.py::test_send_email_notification
  Status: FAILED on attempt 1/3, PASSED on retry 2/3

─── Test history (last 10 runs) ────────────────────────────────────
Run #  | Status  | Duration | Timestamp
───────|─────────|──────────|────────────────────
  1    | PASS    | 1.2s     | 2026-07-14 09:00
  2    | PASS    | 0.9s     | 2026-07-14 09:15
  3    | FAIL    | 3.1s     | 2026-07-14 09:30  ←
  4    | PASS    | 1.1s     | 2026-07-14 09:45
  5    | FAIL    | 2.8s     | 2026-07-14 10:00  ←
  6    | PASS    | 1.0s     | 2026-07-14 10:15
  7    | PASS    | 1.2s     | 2026-07-14 10:30
  8    | FAIL    | 3.5s     | 2026-07-14 10:45  ←
  9    | PASS    | 1.1s     | 2026-07-14 11:00
 10    | FAIL    | 2.9s     | 2026-07-14 11:15  ← current

─── Failure output ─────────────────────────────────────────────────
tests/integration/test_notifications.py:78: in test_send_email_notification
    assert mock_smtp.sendmsg.call_count == 1
E   assert 0 == 1
E   +  where 0 = <MagicMock name='smtp.sendmsg' call_count>.call_count

─── Observations ───────────────────────────────────────────────────
  • Fails ~40% of the time (4/10 recent runs)
  • Always passes on retry
  • Duration is ~3x longer on failures → likely race condition
  • Suspected: SMTP mock cleanup races with async fixture teardown`,
  },
  {
    id: "type-error",
    title: "Type Error",
    description: "A TypeError caused by an unexpected None value",
    category: "assertion_error",
    sourceType: "stack_trace",
    content: `FAILED tests/unit/test_data_processor.py::test_process_user_data - TypeError: 'NoneType' object is not subscriptable

─── Test ───────────────────────────────────────────────────────────
tests/unit/test_data_processor.py:42: in test_process_user_data
    result = processor.process(user_data)
                                        ^

─── Stack trace ────────────────────────────────────────────────────
  File "/workspace/app/src/data_processor.py:85", in process
    user_id = record["user"]["id"]
              ~~~~~~^^^^^^
TypeError: 'NoneType' object is not subscriptable

─── Relevant code ──────────────────────────────────────────────────
src/data_processor.py:85
    83  def process(self, records: list[dict]) -> list[ProcessedUser]:
    84      for record in records:
--> 85          user_id = record["user"]["id"]
    86          name = record["user"].get("name", "Unknown")
    87          processed.append(ProcessedUser(id=user_id, name=name))

─── Input record that caused the crash ─────────────────────────────
    {
      "id": "rec_789",
      "user": null,              # <-- Expected dict, got null
      "timestamp": "2026-07-14T10:00:00Z"
    }

─── Test data fixture ──────────────────────────────────────────────
tests/unit/test_data_processor.py:12:
    @pytest.fixture
    def user_data():
        return [
            {"id": "rec_001", "user": {"id": "u1", "name": "Alice"}},
            {"id": "rec_789", "user": None},  # ← Missing null guard
        ]`,
  },
  {
    id: "env-mismatch",
    title: "Environment Mismatch",
    description: "Different Python versions between CI and dev",
    category: "environment",
    sourceType: "ci_log",
    content: `ERROR: Python version mismatch detected

─── CI run details ─────────────────────────────────────────────────
Job: lint-and-test (py3.11)
Runner: ubuntu-latest
Python: 3.11.9 (CI)
Branch: feature/add-ml-models

─── Error ──────────────────────────────────────────────────────────
  tests/unit/test_config.py:28: in test_feature_flags
    assert config.get("ml_models_enabled") is True
E   AssertionError: assert None is True

─── Root cause ─────────────────────────────────────────────────────
src/config.py uses `sys.version_info` to conditionally enable
features. The `ml_models_enabled` flag requires Python ≥ 3.12:

  src/config.py:45
      @property
      def ml_models_enabled(self) -> bool:
          return sys.version_info >= (3, 12)  # ← False on 3.11

─── Environment comparison ─────────────────────────────────────────
                 CI (3.11)   Developer machine (3.12)
─────────────── ─────────── ─────────────────────────
Python          3.11.9      3.12.4
OS              Ubuntu 24   macOS 14.5 (ARM)
Dependencies    ✅ sync     ✅ sync
Feature flags   ML: OFF     ML: ON

─── Suggested fix ──────────────────────────────────────────────────
Option 1: Update CI matrix to include Python 3.12
Option 2: Remove version gate — test ML features independently`,
  },
  {
    id: "db-connection",
    title: "Database Connection Failure",
    description: "Database unavailable during integration tests",
    category: "configuration",
    sourceType: "ci_log",
    content: `FAILED tests/integration/test_user_repository.py::test_create_user - OperationalError: could not connect to server

─── CI run details ─────────────────────────────────────────────────
Job: integration-tests
Runner: ubuntu-latest
Service: postgres:16 (container)

─── Error trace ────────────────────────────────────────────────────
  File "/workspace/app/src/infrastructure/database.py:42", in get_session
    async with async_session_maker() as session:
  File "sqlalchemy/ext/asyncio.py:1234", in __aenter__
    ...
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError)
  could not connect to server: Connection refused
    Is the server running on host "localhost" (127.0.0.1) and
    accepting TCP/IP connections on port 5432?

─── CI logs ────────────────────────────────────────────────────────
[11:02:15]  Starting PostgreSQL service container...
[11:02:15]  Pulling postgres:16 from ghcr.io
[11:02:20]  Error: postgres:16 not found in ghcr.io cache
[11:02:22]  Falling back to Docker Hub...
[11:02:35]  PostgreSQL container started (port: 5432)
[11:02:35]  Running migrations...
[11:02:38]  ⚠ Connection refused — is postgres accepting connections?
[11:02:40]  Starting pytest...
[11:02:41]  FAILED test_create_user

─── Service health ─────────────────────────────────────────────────
$ docker ps
CONTAINER ID   IMAGE        STATUS         PORTS
a1b2c3d4e5f6   postgres:16  Up 8 seconds   0.0.0.0:5432->5432/tcp

$ docker logs a1b2c3d4e5f6
2026-07-14 11:02:30.512 UTC [1] LOG:  database system was interrupted
2026-07-14 11:02:30.518 UTC [1] LOG:  performing crash recovery
2026-07-14 11:02:30.612 UTC [1] LOG:  database system ready

→ Database was still in recovery when the test started.`,
  },
  {
    id: "compilation-error",
    title: "Compilation Error",
    description: "TypeScript build failure in CI pipeline",
    category: "compilation",
    sourceType: "ci_log",
    content: `ERROR: Failed to compile frontend

─── CI run details ─────────────────────────────────────────────────
Job: build-and-test
Runner: ubuntu-latest
Step: npm run build (frontend/)
Exit code: 2

─── Compiler output ────────────────────────────────────────────────
src/components/DataGrid.tsx:124:18 - error TS2322: Type 'string | undefined'
  is not assignable to type 'string'.

    122    >
    123      {columns.map((col) => (
    124        <th key={col.key}>{col.label?.toUpperCase()}</th>
                                        ~~~~~~~~~~
    'col.label' is possibly 'undefined'.

  src/types/report.ts:42:3
    42   label?: string;
           ~~~~~~~~~~~~~
    The expected type comes from property 'label' which is
    declared here in type 'ColumnConfig'.

─── Changed files in this PR ───────────────────────────────────────
  src/components/DataGrid.tsx    (modified)
  src/types/report.ts             (modified)
  src/hooks/use-report-data.ts   (added)

─── git diff (relevant) ────────────────────────────────────────────
  src/types/report.ts
  -  label: string;
  +  label?: string;     ← Changed to optional, broke DataGrid

─── Build step log ─────────────────────────────────────────────────
$ npm run build
> qpilot-frontend@0.4.0 build
> tsc --noEmit && vite build

src/components/DataGrid.tsx:124:18 - error TS2322: ...
  ✗ Build failed after 12.4s`,
  },
];
