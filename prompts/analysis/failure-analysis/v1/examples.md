## Example Failure Analysis

### Input
```
FAILED tests/integration/test_auth.py::test_login_success - AssertionError: assert False
 +  where False = <built-in method startswith of str object at 0x...>('eyJ')

FAILED tests/integration/test_auth.py::test_login_invalid_credentials - ScopeError: Required scope 'session:write' is missing

FAILED tests/integration/test_auth.py::test_session_refresh - AttributeError: 'OpaqueToken' object has no attribute 'decode'

Platform: linux -- Python 3.12.2, pytest-8.0.0, pluggy-1.4.0
rootdir: /app
plugins: asyncio-0.23.5
collected 42 items / 3 failed / 39 passed in 12.5s
```

### Output
```json
{
  "input_summary": "CI test run failure in the user authentication module. 3 tests failed with assertion errors and attribute errors in the login flow.",
  "summary": "The authentication test suite failed due to a recent refactor of the session management layer. The session token validation logic was changed, causing existing login tests to fail because they expect the old JWT token format.",
  "root_causes": [
    {
      "id": "RC-001",
      "title": "Session token validation mismatch after refactor",
      "description": "The session management refactor changed the token structure from JWT to opaque tokens, but the test helpers still validate against the old JWT format.",
      "category": "assertion_error",
      "severity": "high",
      "failing_file": "tests/integration/test_auth.py",
      "failing_line": 42,
      "stack_trace": [
        {
          "file": "tests/integration/test_auth.py",
          "line": 42,
          "function": "test_login_success",
          "code": "assert response.json()['token'].startswith('eyJ')"
        },
        {
          "file": "app/auth/session.py",
          "line": 128,
          "function": "create_session",
          "code": "return OpaqueToken(user_id, expiry)"
        }
      ],
      "error_message": "AssertionError: assert False\n +  where False = <built-in method startswith of str object at 0x...>('eyJ')"
    },
    {
      "id": "RC-002",
      "title": "Missing session scope in test fixture",
      "description": "The test fixture for authenticated requests was not updated to request the new 'session:write' scope required by the refactored session service.",
      "category": "configuration",
      "severity": "medium",
      "failing_file": "tests/conftest.py",
      "failing_line": 15,
      "error_message": "ScopeError: Required scope 'session:write' is missing"
    },
    {
      "id": "RC-003",
      "title": "Test_session_refresh uses deprecated token.decode()",
      "description": "The session refresh test calls .decode() on the token object, which no longer exists in the new OpaqueToken class. The decode method was removed during the refactor.",
      "category": "assertion_error",
      "severity": "high",
      "failing_file": "tests/integration/test_auth.py",
      "failing_line": 78,
      "error_message": "AttributeError: 'OpaqueToken' object has no attribute 'decode'"
    }
  ],
  "suggested_fixes": [
    {
      "id": "FIX-001",
      "root_cause_id": "RC-001",
      "description": "Update test assertions to match the new opaque token format. Instead of checking for a JWT prefix, validate that the session ID is a valid UUID and that the token endpoint returns a 200 status.",
      "priority": "high",
      "effort_estimate": "30 minutes",
      "code_example": "# Before:\nassert response.json()['token'].startswith('eyJ')\n\n# After:\nimport uuid\nsession = response.json()\nassert 'session_id' in session\nuuid.UUID(session['session_id'])",
      "related_files": ["tests/integration/test_auth.py"]
    },
    {
      "id": "FIX-002",
      "root_cause_id": "RC-002",
      "description": "Add the 'session:write' scope to the authenticated test fixture in conftest.py.",
      "priority": "medium",
      "effort_estimate": "15 minutes",
      "code_example": "# Before:\nscopes=['session:read']\n\n# After:\nscopes=['session:read', 'session:write']",
      "related_files": ["tests/conftest.py"]
    },
    {
      "id": "FIX-003",
      "root_cause_id": "RC-003",
      "description": "Replace the .decode() call with the appropriate method on OpaqueToken. The token now exposes session data through the 'get_session_data()' method.",
      "priority": "high",
      "effort_estimate": "20 minutes",
      "code_example": "# Before:\ntoken_data = token.decode()\n\n# After:\ntoken_data = token.get_session_data()",
      "related_files": ["tests/integration/test_auth.py"]
    }
  ],
  "affected_components": [
    {
      "id": "CMP-001",
      "name": "Authentication Service",
      "impact": "Login flow is broken. Users cannot authenticate with the new session layer.",
      "related_root_causes": ["RC-001"]
    },
    {
      "id": "CMP-002",
      "name": "Test Fixtures",
      "impact": "All authenticated test requests fail due to missing scopes.",
      "related_root_causes": ["RC-002"]
    },
    {
      "id": "CMP-003",
      "name": "Session Refresh Endpoint",
      "impact": "Token refresh fails because the test uses the old API.",
      "related_root_causes": ["RC-003"]
    }
  ],
  "test_failures": [
    {
      "id": "TF-001",
      "test_name": "tests/integration/test_auth.py::test_login_success",
      "test_file": "tests/integration/test_auth.py",
      "error_message": "AssertionError: assert False",
      "duration_seconds": 1.2,
      "retry_count": 0
    },
    {
      "id": "TF-002",
      "test_name": "tests/integration/test_auth.py::test_login_invalid_credentials",
      "test_file": "tests/integration/test_auth.py",
      "error_message": "ScopeError: Required scope 'session:write' is missing",
      "duration_seconds": 0.8,
      "retry_count": 1
    },
    {
      "id": "TF-003",
      "test_name": "tests/integration/test_auth.py::test_session_refresh",
      "test_file": "tests/integration/test_auth.py",
      "error_message": "AttributeError: 'OpaqueToken' object has no attribute 'decode'",
      "duration_seconds": 0.5,
      "retry_count": 0
    }
  ],
  "environment_details": [
    "Python 3.12.2",
    "pytest 8.0.0",
    "CI runner: GitHub Actions ubuntu-latest",
    "Commit: a1b2c3d (feature/session-refactor)"
  ],
  "recommendations": [
    "Run the full test suite to check for additional failures before merging.",
    "Add a migration guide for the new session token format to the team wiki.",
    "Consider adding a compatibility shim during the transition period.",
    "Update test documentation to reflect the new token API."
  ],
  "related_tests": [
    "tests/integration/test_session_expiry.py",
    "tests/unit/test_token_validator.py",
    "tests/integration/test_logout.py",
    "tests/integration/test_multi_device_login.py"
  ]
}
```
