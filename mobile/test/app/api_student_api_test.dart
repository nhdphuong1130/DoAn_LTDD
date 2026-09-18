import 'dart:convert';
import 'dart:typed_data';

import 'package:english7_mobile/api/api_client.dart';
import 'package:english7_mobile/api/http_transport.dart';
import 'package:english7_mobile/app/api_student_api.dart';
import 'package:english7_mobile/app/student_api.dart';
import 'package:english7_mobile/config/app_config.dart';
import 'package:flutter_test/flutter_test.dart';

class MemoryTokens implements TokenStore {
  @override
  Future<String?> read() async => 'token';

  @override
  Future<void> clear() async {}

  @override
  Future<void> write(String token) async {}
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
    final config = AppConfig.fromEnvironment(const {
      'API_BASE_URL': 'https://api.example.test',
      'IMAGE_POLL_INTERVAL_MS': '1',
      'IMAGE_POLL_MAX_ATTEMPTS': '3',
    });
    final api = ApiStudentApi(
      ApiClient(config, transport, tokens),
      tokens,
      imagePollInterval: config.imagePollInterval,
      imagePollMaxAttempts: config.imagePollMaxAttempts,
      delay: (_) async {},
    );

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
}
