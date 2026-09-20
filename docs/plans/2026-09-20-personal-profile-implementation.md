# Personal Profile and Logout Implementation Plan

**Goal:** Add a student profile tab with editable personal information, password change, secure session restoration, and confirmed logout.

**Architecture:** SQL Server remains authoritative for profile data and password hashes. The existing auth module gains profile/password commands scoped exclusively to the authenticated JWT subject; Flutter exposes those commands through `StudentApi`, restores the stored session at app startup, and owns logout at the root authentication state.

**Tech Stack:** Python 3.12, FastAPI, Pydantic 2, SQLAlchemy 2, Alembic, pytest, Flutter/Dart, Material 3, flutter_secure_storage, flutter_test

**Design:** `docs/plans/2026-09-20-personal-profile-and-logout-design.md`

---

### Task 1: Persist Unicode Personal Profile Fields

**Files:**
- Create: `backend/alembic/versions/0006_user_personal_profile.py`
- Modify: `backend/src/english7/db/models.py`
- Modify: `backend/src/english7/modules/auth/domain.py`
- Modify: `backend/src/english7/modules/auth/repository.py`
- Modify: `backend/tests/db/test_models.py`
- Modify: `backend/tests/integration/test_migrations.py`
- Create: `backend/tests/modules/auth/test_repository.py`

**Step 1: Write failing model and repository tests**

Add to `backend/tests/db/test_models.py`:

```python
from sqlalchemy import Unicode

from english7.db.models import User


def test_user_profile_text_columns_are_nullable_unicode() -> None:
    columns = User.__table__.c
    assert isinstance(columns.full_name.type, Unicode)
    assert isinstance(columns.school_name.type, Unicode)
    assert isinstance(columns.class_name.type, Unicode)
    assert columns.full_name.nullable is True
    assert columns.date_of_birth.nullable is True
```

Create `backend/tests/modules/auth/test_repository.py` using an in-memory SQLite
engine, seeded `student` role, and this behavior:

```python
def test_repository_updates_only_requested_profile_fields(repository) -> None:
    user = repository.create(
        AuthUser.new(
            email="student@example.com",
            password_hash="hash",
        )
    )

    updated = repository.update_profile(
        user.id,
        {"full_name": "Nguyễn An", "class_name": "7A1"},
    )

    assert updated.full_name == "Nguyễn An"
    assert updated.class_name == "7A1"
    assert updated.email == "student@example.com"
```

Extend the integration migration assertion:

```python
user_columns = {column["name"] for column in inspect(get_engine()).get_columns("users")}
assert {"full_name", "date_of_birth", "gender", "school_name", "class_name"} <= user_columns
```

**Step 2: Run tests to verify RED**

Run:

```bash
cd backend
uv run pytest tests/db/test_models.py tests/modules/auth/test_repository.py -q
```

Expected: FAIL because the profile columns and repository method do not exist.

**Step 3: Add the migration and model fields**

Create revision `0006_user_personal_profile`, down revision
`0005_knowledge_graph_foundation`. Inspect existing `users` columns before each
`op.add_column` because `0001_initial_schema` creates current metadata on a new
database. Use:

```python
PROFILE_COLUMNS = (
    sa.Column("full_name", sa.Unicode(255), nullable=True),
    sa.Column("date_of_birth", sa.Date(), nullable=True),
    sa.Column("gender", sa.String(30), nullable=True),
    sa.Column("school_name", sa.Unicode(255), nullable=True),
    sa.Column("class_name", sa.Unicode(100), nullable=True),
)


def upgrade() -> None:
    existing = {
        item["name"] for item in sa.inspect(op.get_bind()).get_columns("users")
    }
    for column in PROFILE_COLUMNS:
        if column.name not in existing:
            op.add_column("users", column)


def downgrade() -> None:
    existing = {
        item["name"] for item in sa.inspect(op.get_bind()).get_columns("users")
    }
    for name in ("class_name", "school_name", "gender", "date_of_birth", "full_name"):
        if name in existing:
            op.drop_column("users", name)
```

Add matching nullable fields to `User` and `AuthUser`. Use `Unicode` for
Vietnamese text and `date`/`Date` for date of birth. Extend `_to_domain`,
`create`, and `AuthRepository` with:

```python
def update_profile(
    self, user_id: UUID, changes: dict[str, object]
) -> AuthUser | None: ...

def update_password_hash(self, user_id: UUID, password_hash: str) -> bool: ...
```

The SQL repository loads the row, assigns only keys in the service-owned
allowlist, commits, and re-reads the domain value. Password update writes only
`password_hash` and returns false if the user is missing.

**Step 4: Run tests to verify GREEN**

Run:

```bash
cd backend
uv run pytest tests/db/test_models.py tests/modules/auth/test_repository.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/alembic/versions/0006_user_personal_profile.py \
  backend/src/english7/db/models.py \
  backend/src/english7/modules/auth/domain.py \
  backend/src/english7/modules/auth/repository.py \
  backend/tests/db/test_models.py \
  backend/tests/integration/test_migrations.py \
  backend/tests/modules/auth/test_repository.py
git commit -m "feat: persist student personal profiles"
```

### Task 2: Add Profile and Password Business Rules

**Files:**
- Modify: `backend/src/english7/modules/auth/domain.py`
- Modify: `backend/src/english7/modules/auth/service.py`
- Modify: `backend/tests/modules/auth/test_service.py`

**Step 1: Extend the in-memory repository and write failing tests**

Add `update_profile` and `update_password_hash` to the test repository by using
`dataclasses.replace`. Add these tests:

```python
def test_update_profile_normalizes_optional_text() -> None:
    service, _, _ = build_service()
    user = service.register("student@example.com", "secure-password")

    updated = service.update_profile(
        user.id,
        {
            "full_name": "  Nguyễn An  ",
            "school_name": "   ",
            "class_name": " 7A1 ",
            "gender": "female",
            "date_of_birth": date(2013, 5, 10),
        },
    )

    assert updated.full_name == "Nguyễn An"
    assert updated.school_name is None
    assert updated.class_name == "7A1"


def test_update_profile_rejects_unknown_gender() -> None:
    service, _, _ = build_service()
    user = service.register("student@example.com", "secure-password")

    with pytest.raises(ApplicationError) as captured:
        service.update_profile(user.id, {"gender": "unknown"})

    assert captured.value.code == "profile_gender_invalid"


def test_change_password_requires_current_password_and_updates_login() -> None:
    service, _, _ = build_service()
    user = service.register("student@example.com", "secure-password")

    service.change_password(
        user.id,
        current_password="secure-password",
        new_password="new-secure-password",
        confirm_password="new-secure-password",
    )

    assert service.login("student@example.com", "new-secure-password")
    with pytest.raises(ApplicationError):
        service.login("student@example.com", "secure-password")


@pytest.mark.parametrize(
    ("current", "new", "confirmation", "code"),
    [
        ("wrong-password", "new-secure-password", "new-secure-password", "current_password_invalid"),
        ("secure-password", "different-password", "mismatch-password", "password_confirmation_mismatch"),
        ("secure-password", "secure-password", "secure-password", "password_unchanged"),
    ],
)
def test_change_password_rejects_invalid_requests(
    current: str, new: str, confirmation: str, code: str
) -> None:
    service, _, _ = build_service()
    user = service.register("student@example.com", "secure-password")

    with pytest.raises(ApplicationError) as captured:
        service.change_password(
            user.id,
            current_password=current,
            new_password=new,
            confirm_password=confirmation,
        )

    assert captured.value.code == code
```

**Step 2: Run tests to verify RED**

Run:

```bash
cd backend
uv run pytest tests/modules/auth/test_service.py -q
```

Expected: FAIL because profile/password service methods do not exist.

**Step 3: Implement service rules**

Define `ProfileGender(StrEnum)` with `male`, `female`, `other`, and
`prefer_not_to_say`. Implement:

```python
PROFILE_TEXT_LIMITS = {
    "full_name": 255,
    "school_name": 255,
    "class_name": 100,
}


def update_profile(self, user_id: UUID, changes: dict[str, object]) -> AuthUser:
    normalized = dict(changes)
    for field, limit in PROFILE_TEXT_LIMITS.items():
        if field in normalized:
            value = normalized[field]
            normalized[field] = value.strip() or None if isinstance(value, str) else None
            if normalized[field] is not None and len(normalized[field]) > limit:
                raise ApplicationError("profile_field_too_long", f"{field} is too long", 422)
    if "gender" in normalized and normalized["gender"] is not None:
        try:
            normalized["gender"] = ProfileGender(str(normalized["gender"])).value
        except ValueError as error:
            raise ApplicationError("profile_gender_invalid", "Gender is invalid", 422) from error
    updated = self.repository.update_profile(user_id, normalized)
    if updated is None:
        raise ApplicationError("user_not_found", "User was not found", 404)
    return updated
```

Implement password change in validation order: confirmation, user lookup,
current password verification, unchanged password, hash and repository update.
Raise stable `ApplicationError` codes from the tests and never expose hashes.

**Step 4: Run tests to verify GREEN**

Run:

```bash
cd backend
uv run pytest tests/modules/auth/test_service.py -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/src/english7/modules/auth/domain.py \
  backend/src/english7/modules/auth/service.py \
  backend/tests/modules/auth/test_service.py
git commit -m "feat: manage profile and password rules"
```

### Task 3: Expose Authenticated Profile APIs

**Files:**
- Modify: `backend/src/english7/modules/auth/router.py`
- Modify: `backend/tests/api/test_auth.py`

**Step 1: Write failing API tests**

Extend the API test memory repository and add:

```python
def test_authenticated_user_can_read_and_update_only_own_profile(client) -> None:
    service = configured_service()
    user = service.register("student@example.com", "secure-password")
    token = service.token_service.issue(user)
    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        updated = client.patch(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "full_name": "Nguyễn An",
                "date_of_birth": "2013-05-10",
                "gender": "female",
                "school_name": "THCS Nguyễn Du",
                "class_name": "7A1",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert updated.status_code == 200
    assert updated.json()["full_name"] == "Nguyễn An"
    assert updated.json()["email"] == "student@example.com"
    assert "password_hash" not in updated.json()


def test_change_password_returns_no_content(client) -> None:
    service = configured_service()
    user = service.register("student@example.com", "secure-password")
    token = service.token_service.issue(user)
    app.dependency_overrides[get_auth_service] = lambda: service
    try:
        response = client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "secure-password",
                "new_password": "new-secure-password",
                "confirm_password": "new-secure-password",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    assert response.content == b""
```

Add negative tests for missing token, invalid gender, mismatched confirmation,
and an attempted payload containing `email` (Pydantic must reject extra fields).

**Step 2: Run tests to verify RED**

Run:

```bash
cd backend
uv run pytest tests/api/test_auth.py -q
```

Expected: FAIL because PATCH and change-password routes do not exist.

**Step 3: Add strict request and response schemas**

Use `ConfigDict(extra="forbid")`. Define `UserResponse` with nullable profile
fields and a `from_user` constructor. Define `ProfileUpdateRequest` and
`ChangePasswordRequest`; keep passwords at 8–128 characters. Route handlers:

```python
@router.patch("/me", response_model=UserResponse)
def update_me(payload: ProfileUpdateRequest, user=Depends(get_current_user), service=Depends(get_auth_service)):
    updated = service.update_profile(
        user.id, payload.model_dump(exclude_unset=True)
    )
    return UserResponse.from_user(updated)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(payload: ChangePasswordRequest, user=Depends(get_current_user), service=Depends(get_auth_service)) -> Response:
    service.change_password(
        user.id,
        current_password=payload.current_password,
        new_password=payload.new_password,
        confirm_password=payload.confirm_password,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

Update register and `/me` to use `UserResponse.from_user`.

**Step 4: Run auth API and full backend unit tests**

Run:

```bash
cd backend
uv run pytest tests/api/test_auth.py tests/modules/auth tests/db/test_models.py -q
uv run pytest tests --ignore=tests/integration -q
```

Expected: PASS.

**Step 5: Commit**

```bash
git add backend/src/english7/modules/auth/router.py backend/tests/api/test_auth.py
git commit -m "feat: expose personal profile APIs"
```

### Task 4: Add Mobile Profile Contracts, HTTP Methods, and Session Commands

**Files:**
- Modify: `mobile/lib/api/api_client.dart`
- Modify: `mobile/lib/app/student_api.dart`
- Modify: `mobile/lib/app/api_student_api.dart`
- Modify: `mobile/test/api/api_client_test.dart`
- Modify: `mobile/test/app/api_student_api_test.dart`
- Modify: `mobile/test/features/support/fakes.dart`

**Step 1: Write failing client tests**

Add tests asserting:

```dart
test('patchJson sends authenticated PATCH payload', () async {
  final transport = FakeTransport(jsonResponse(200, {'full_name': 'Nguyễn An'}));
  final client = ApiClient(config, transport, FakeTokenStore('token-123'));

  await client.patchJson('/api/v1/auth/me', {'full_name': 'Nguyễn An'});

  expect(transport.request!.method, 'PATCH');
  expect(transport.request!.headers['Authorization'], 'Bearer token-123');
});

test('postNoContent accepts a successful empty response', () async {
  final transport = FakeTransport(
    TransportResponse(204, const {}, Uint8List(0)),
  );
  final client = ApiClient(config, transport, FakeTokenStore('token-123'));

  await client.postNoContent('/api/v1/auth/change-password', {
    'current_password': 'old-password',
    'new_password': 'new-password',
    'confirm_password': 'new-password',
  });

  expect(transport.request!.method, 'POST');
});
```

Add `ApiStudentApi` tests that parse nullable profile values, serialize dates as
`YYYY-MM-DD`, clear tokens on logout, return null and clear tokens on a `401`
during restore, and rethrow non-401 restore errors without clearing the token.

**Step 2: Run tests to verify RED**

Run:

```bash
cd mobile
flutter test test/api/api_client_test.dart test/app/api_student_api_test.dart
```

Expected: FAIL because profile methods do not exist.

**Step 3: Add contracts and adapters**

Add immutable models:

```dart
enum ProfileGender { male, female, other, preferNotToSay }

class StudentProfile {
  final String id;
  final String email;
  final String role;
  final String? fullName;
  final DateTime? dateOfBirth;
  final ProfileGender? gender;
  final String? schoolName;
  final String? className;
  const StudentProfile({required this.id, required this.email, required this.role, this.fullName, this.dateOfBirth, this.gender, this.schoolName, this.className});
}

class ProfileUpdate {
  final String? fullName;
  final DateTime? dateOfBirth;
  final ProfileGender? gender;
  final String? schoolName;
  final String? className;
  const ProfileUpdate({this.fullName, this.dateOfBirth, this.gender, this.schoolName, this.className});
}
```

Extend `StudentApi` with:

```dart
Future<StudentProfile?> restoreSession();
Future<StudentProfile> loadProfile();
Future<StudentProfile> updateProfile(ProfileUpdate update);
Future<void> changePassword(String currentPassword, String newPassword, String confirmation);
Future<void> logout();
```

In `ApiClient`, add `patchJson` and `postNoContent`. The no-content method must
decode standard error JSON on non-2xx but never JSON-decode a successful empty
body. In `ApiStudentApi`, map profile JSON in one `_profile` helper. Catch only
`ApiException(statusCode: 401)` during restore; clear the token and return null.
Other errors propagate.

Update `FakeStudentApi` with a default profile, call counters, configurable
restore error, profile mutation, password arguments, and logout flag.

**Step 4: Run tests to verify GREEN**

Run:

```bash
cd mobile
dart format lib test
flutter test test/api/api_client_test.dart test/app/api_student_api_test.dart
```

Expected: PASS.

**Step 5: Commit**

```bash
git add mobile/lib/api/api_client.dart mobile/lib/app/student_api.dart \
  mobile/lib/app/api_student_api.dart mobile/test/api/api_client_test.dart \
  mobile/test/app/api_student_api_test.dart mobile/test/features/support/fakes.dart
git commit -m "feat: add mobile profile API contracts"
```

### Task 5: Restore Authentication State and Implement Logout

**Files:**
- Modify: `mobile/lib/app/english7_app.dart`
- Modify: `mobile/test/features/lesson_flow_test.dart`
- Create: `mobile/test/features/session_flow_test.dart`

**Step 1: Write failing app-state widget tests**

Create tests for these behaviors:

```dart
testWidgets('valid stored session opens student shell without login', (tester) async {
  final api = FakeStudentApi()..restoredProfile = FakeStudentApi.defaultProfile;
  await tester.pumpWidget(English7App(api: api, imageSelector: FakeImageSelector()));
  await tester.pumpAndSettle();

  expect(find.text('Bài học'), findsOneWidget);
  expect(find.text('Đăng nhập'), findsNothing);
});

testWidgets('missing session opens login', (tester) async {
  final api = FakeStudentApi()..restoredProfile = null;
  await tester.pumpWidget(English7App(api: api, imageSelector: FakeImageSelector()));
  await tester.pumpAndSettle();

  expect(find.text('Đăng nhập'), findsOneWidget);
});

testWidgets('restore network error shows retry without clearing session', (tester) async {
  final api = FakeStudentApi()..restoreError = Exception('offline');
  await tester.pumpWidget(English7App(api: api, imageSelector: FakeImageSelector()));
  await tester.pumpAndSettle();

  expect(find.text('Không thể kiểm tra phiên đăng nhập'), findsOneWidget);
  expect(find.text('Thử lại'), findsOneWidget);
  expect(api.logoutCalled, isFalse);
});
```

Adapt existing flow tests so their fake starts with no stored session and logs in
through the existing form.

**Step 2: Run tests to verify RED**

Run:

```bash
cd mobile
flutter test test/features/session_flow_test.dart test/features/lesson_flow_test.dart
```

Expected: FAIL because the app does not restore sessions.

**Step 3: Implement the root session state machine**

Use:

```dart
enum _SessionState { checking, authenticated, unauthenticated, failed }
```

Call `_restoreSession` from `initState`. Render a centered progress indicator
for checking, a retry scaffold for failed, `LoginScreen` for unauthenticated,
and `StudentShell` for authenticated. Pass `onLogout` into `StudentShell`; it
sets root state to unauthenticated only after `api.logout()` completes. Do not
use Navigator pushes for authentication transitions.

**Step 4: Run tests to verify GREEN**

Run:

```bash
cd mobile
dart format lib test
flutter test test/features/session_flow_test.dart test/features/lesson_flow_test.dart
```

Expected: PASS.

**Step 5: Commit**

```bash
git add mobile/lib/app/english7_app.dart \
  mobile/test/features/session_flow_test.dart \
  mobile/test/features/lesson_flow_test.dart
git commit -m "feat: restore and clear student sessions"
```

### Task 6: Build the Personal Profile Tab

**Files:**
- Create: `mobile/lib/features/profile/profile_screen.dart`
- Create: `mobile/test/features/profile_screen_test.dart`
- Modify: `mobile/lib/app/english7_app.dart`

**Step 1: Write failing widget tests**

Cover load/display, editing, save failure retention, password change, and
confirmed logout:

```dart
testWidgets('profile tab displays and updates student information', (tester) async {
  final api = FakeStudentApi()..restoredProfile = FakeStudentApi.defaultProfile;
  await tester.pumpWidget(English7App(api: api, imageSelector: FakeImageSelector()));
  await tester.pumpAndSettle();
  await tester.tap(find.text('Cá nhân'));
  await tester.pumpAndSettle();

  expect(find.text('student@example.com'), findsOneWidget);
  await tester.tap(find.text('Chỉnh sửa hồ sơ'));
  await tester.enterText(find.byKey(const Key('profile-full-name')), 'Nguyễn An');
  await tester.enterText(find.byKey(const Key('profile-class-name')), '7A1');
  await tester.tap(find.text('Lưu thay đổi'));
  await tester.pumpAndSettle();

  expect(api.profile.fullName, 'Nguyễn An');
  expect(api.profile.className, '7A1');
});

testWidgets('logout requires confirmation and returns to login', (tester) async {
  final api = FakeStudentApi()..restoredProfile = FakeStudentApi.defaultProfile;
  await tester.pumpWidget(English7App(api: api, imageSelector: FakeImageSelector()));
  await tester.pumpAndSettle();
  await tester.tap(find.text('Cá nhân'));
  await tester.pumpAndSettle();
  await tester.tap(find.text('Đăng xuất'));
  await tester.pumpAndSettle();

  expect(find.text('Bạn có chắc muốn đăng xuất?'), findsOneWidget);
  await tester.tap(find.widgetWithText(FilledButton, 'Đăng xuất'));
  await tester.pumpAndSettle();

  expect(api.logoutCalled, isTrue);
  expect(find.byKey(const Key('email-field')), findsOneWidget);
});
```

Also assert password mismatch is caught before API, API errors keep entered form
values, and the role/email controls are not editable.

**Step 2: Run tests to verify RED**

Run:

```bash
cd mobile
flutter test test/features/profile_screen_test.dart
```

Expected: FAIL because `ProfileScreen` and the fifth tab do not exist.

**Step 3: Implement ProfileScreen and fifth navigation destination**

`ProfileScreen` is stateful, loads once from `StudentApi`, disposes every text
controller, checks `mounted` after awaits, and uses separate busy/error state for
profile and password actions. Use a date picker limited to sensible student
dates, a Vietnamese-labelled gender dropdown, read-only email/role rows, and
`SnackBar` success feedback.

Add this destination after Tiến độ:

```dart
NavigationDestination(
  icon: Icon(Icons.person_outline),
  selectedIcon: Icon(Icons.person),
  label: 'Cá nhân',
)
```

The logout dialog has `Hủy` and a destructive `FilledButton`; await
`widget.onLogout()` only after confirmation.

**Step 4: Run widget tests and analyze**

Run:

```bash
cd mobile
dart format lib test
flutter analyze
flutter test
```

Expected: analyze clean and all Flutter tests PASS.

**Step 5: Commit**

```bash
git add mobile/lib/features/profile/profile_screen.dart \
  mobile/lib/app/english7_app.dart \
  mobile/test/features/profile_screen_test.dart
git commit -m "feat: add personal profile tab"
```

### Task 7: Verify Migration, Regression, and Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/setup-linux.md`

**Step 1: Document the user-facing feature and migration**

Add a short feature summary, `alembic upgrade head` requirement, profile API
routes, stateless logout limitation, and the commands below. Do not claim JWT
server-side revocation.

**Step 2: Run backend verification**

```bash
cd backend
uv run pytest tests --ignore=tests/integration -q
uv run python -m compileall -q src tests
```

Expected: all tests pass and compile succeeds.

When integration SQL Server and Neo4j are available, run:

```bash
cd ..
./scripts/test-knowledge-integration.sh
```

Expected: knowledge build gate remains green and the new migration reaches head.

**Step 3: Run mobile verification**

```bash
cd mobile
dart format --output=none --set-exit-if-changed lib test
flutter analyze
flutter test
```

Expected: format, analyze, and all widget/unit tests pass. If Flutter is absent,
record the exact environment blocker and do not claim these checks passed.

**Step 4: Validate repository state**

```bash
cd ..
git diff --check
docker compose --env-file .env.example config --quiet
git status --short
```

Expected: no whitespace errors, valid Compose, and only intended changes before
the final commit.

**Step 5: Commit**

```bash
git add README.md docs/setup-linux.md
git commit -m "docs: document personal profile operations"
```

## Plan Review Checklist

- Backend ownership is scoped to the authenticated user ID.
- Existing accounts remain valid because new columns are nullable.
- Vietnamese names, schools, and classes use Unicode SQL types.
- Email and role are read-only in the MVP.
- Password hashes never enter response schemas or mobile models.
- Successful 204 responses do not pass through JSON decoding.
- Only a 401 invalidates a restored local session; network/5xx errors are retryable.
- Logout awaits secure token deletion and replaces root state instead of pushing a route.
- Existing lesson, Tutor, quiz, progress, and knowledge graph behavior remains unchanged.
- Flutter verification is explicitly required on an environment with Flutter installed.
