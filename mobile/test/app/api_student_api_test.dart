import 'dart:convert';
import 'dart:typed_data';

import 'package:english7_mobile/api/api_client.dart';
import 'package:english7_mobile/api/api_error.dart';
import 'package:english7_mobile/api/http_transport.dart';
import 'package:english7_mobile/app/api_student_api.dart';
import 'package:english7_mobile/app/student_api.dart';
import 'package:english7_mobile/config/app_config.dart';
import 'package:flutter_test/flutter_test.dart';

class MemoryTokens implements TokenStore {
  String? token = 'token';
  bool cleared = false;

  @override
  Future<String?> read() async => token;

  @override
  Future<void> clear() async {
    cleared = true;
    token = null;
  }

  @override
  Future<void> write(String token) async {
    this.token = token;
  }
}

class ScriptedTransport implements HttpTransport {
  final responses = <TransportResponse>[];
  final requests = <TransportRequest>[];

  @override
  Future<TransportResponse> send(TransportRequest request) async {
    requests.add(request);
    return responses.removeAt(0);
  }
}

TransportResponse jsonResponse(int status, Map<String, Object?> body) =>
    TransportResponse(
      status,
      const {},
      Uint8List.fromList(utf8.encode(jsonEncode(body))),
    );

void main() {
  final config = AppConfig.fromEnvironment(const {
    'API_BASE_URL': 'https://api.example.test',
    'IMAGE_POLL_INTERVAL_MS': '1',
    'IMAGE_POLL_MAX_ATTEMPTS': '3',
  });

  ApiStudentApi buildApi(ScriptedTransport transport, MemoryTokens tokens) =>
      ApiStudentApi(
        ApiClient(config, transport, tokens),
        tokens,
        imagePollInterval: config.imagePollInterval,
        imagePollMaxAttempts: config.imagePollMaxAttempts,
        delay: (_) async {},
      );

  test('uploads, polls until ready, then submits upload id to tutor', () async {
    final transport = ScriptedTransport()
      ..responses.addAll([
        jsonResponse(202, {
          'id': 'upload-1',
          'status': 'queued',
          'ocr_text': null,
          'ocr_confidence': null,
          'failure_code': null,
          'expires_at': '2026-09-20T00:00:00Z',
        }),
        jsonResponse(200, {
          'id': 'upload-1',
          'status': 'ready',
          'ocr_text': 'recognized question',
          'ocr_confidence': 0.9,
          'failure_code': null,
          'expires_at': '2026-09-20T00:00:00Z',
        }),
        jsonResponse(200, {
          'answer': 'Grounded answer',
          'language': 'en',
          'citations': <Object?>[],
        }),
      ]);
    final tokens = MemoryTokens();
    final api = buildApi(transport, tokens);

    final result = await api.askTutor(
      TutorQuery(
        'Help me',
        TutorLanguage.english,
        TutorImage('exercise.png', Uint8List.fromList([1, 2, 3]), 'image/png'),
      ),
    );

    expect(result.answer, 'Grounded answer');
    expect(transport.requests.map((request) => request.uri.path), [
      '/api/v1/tutor/images',
      '/api/v1/tutor/images/upload-1',
      '/api/v1/tutor/ask',
    ]);
    final tutorPayload = jsonDecode(
      utf8.decode(transport.requests.last.body!),
    ) as Map<String, dynamic>;
    expect(tutorPayload['upload_id'], 'upload-1');
    expect(tutorPayload.containsKey('image_path'), isFalse);
  });

  test('loads a profile with nullable personal values', () async {
    final transport = ScriptedTransport()
      ..responses.add(
        jsonResponse(200, {
          'id': 'user-1',
          'email': 'student@example.com',
          'role': 'student',
          'full_name': null,
          'date_of_birth': null,
          'gender': null,
          'school_name': null,
          'class_name': null,
        }),
      );

    final profile = await buildApi(transport, MemoryTokens()).loadProfile();

    expect(profile.email, 'student@example.com');
    expect(profile.fullName, isNull);
    expect(profile.dateOfBirth, isNull);
    expect(profile.gender, isNull);
  });

  test('updates a profile and serializes the date as YYYY-MM-DD', () async {
    final transport = ScriptedTransport()
      ..responses.add(
        jsonResponse(200, {
          'id': 'user-1',
          'email': 'student@example.com',
          'role': 'student',
          'full_name': 'Nguyễn An',
          'date_of_birth': '2013-05-10',
          'gender': 'female',
          'school_name': 'THCS Nguyễn Du',
          'class_name': '7A1',
        }),
      );

    final profile = await buildApi(transport, MemoryTokens()).updateProfile(
      ProfileUpdate(
        fullName: 'Nguyễn An',
        dateOfBirth: DateTime(2013, 5, 10),
        gender: ProfileGender.female,
        schoolName: 'THCS Nguyễn Du',
        className: '7A1',
      ),
    );

    final payload = jsonDecode(
      utf8.decode(transport.requests.single.body!),
    ) as Map<String, dynamic>;
    expect(payload['date_of_birth'], '2013-05-10');
    expect(payload['gender'], 'female');
    expect(profile.dateOfBirth, DateTime(2013, 5, 10));
  });

  test('logout clears the stored token', () async {
    final tokens = MemoryTokens();

    await buildApi(ScriptedTransport(), tokens).logout();

    expect(tokens.cleared, isTrue);
  });

  test('restore returns null and clears token on 401', () async {
    final transport = ScriptedTransport()
      ..responses.add(
        jsonResponse(401, {
          'code': 'invalid_token',
          'message': 'Token is invalid',
        }),
      );
    final tokens = MemoryTokens();

    final profile = await buildApi(transport, tokens).restoreSession();

    expect(profile, isNull);
    expect(tokens.cleared, isTrue);
  });

  test('restore rethrows non-401 errors without clearing token', () async {
    final transport = ScriptedTransport()
      ..responses.add(
        jsonResponse(503, {
          'code': 'unavailable',
          'message': 'Try again later',
        }),
      );
    final tokens = MemoryTokens();

    await expectLater(
      buildApi(transport, tokens).restoreSession(),
      throwsA(
        isA<ApiException>().having((error) => error.statusCode, 'status', 503),
      ),
    );
    expect(tokens.cleared, isFalse);
  });
}
