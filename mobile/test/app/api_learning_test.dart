import 'dart:typed_data';
import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:english7_mobile/api/api_client.dart';
import 'package:english7_mobile/api/api_error.dart';
import 'package:english7_mobile/api/http_transport.dart';
import 'package:english7_mobile/app/api_student_api.dart';
import 'package:english7_mobile/config/app_config.dart';

import 'api_student_api_test.dart'
    show ScriptedTransport, MemoryTokens, jsonResponse;

void main() {
  late ScriptedTransport transport;
  late ApiStudentApi api;
  setUp(() {
    transport = ScriptedTransport();
    final tokens = MemoryTokens();
    final config = AppConfig.fromEnvironment({
      'API_BASE_URL': 'http://localhost:8000',
      'IMAGE_POLL_INTERVAL_MS': '1',
      'IMAGE_POLL_MAX_ATTEMPTS': '1',
    });
    api = ApiStudentApi(
      ApiClient(config, transport, tokens),
      tokens,
      imagePollInterval: const Duration(seconds: 1),
      imagePollMaxAttempts: 1,
    );
  });
  test('deck list uses authenticated API and parses counts', () async {
    transport.responses.add(
      jsonResponse(200, {
        'items': [
          {'id': 'd', 'name': 'My words', 'kind': 'personal', 'card_count': 2},
        ],
      }),
    );
    final decks = await api.loadDecks();
    expect(decks.single.cardCount, 2);
    expect(transport.requests.single.headers['Authorization'], 'Bearer token');
  });
  test('deletion accepts empty 204 response', () async {
    transport.responses.add(TransportResponse(204, {}, Uint8List(0)));
    await api.deleteCard('card-1');
    expect(transport.requests.single.method, 'DELETE');
  });
  test('voice preview plays bytes and never JSON decodes audio', () async {
    final bytes = Uint8List.fromList([82, 73, 70, 70]);
    transport.responses.add(
      TransportResponse(200, {'content-type': 'audio/wav'}, bytes),
    );
    expect(await api.previewVoice('voice-a'), bytes);
    expect(transport.requests.single.method, 'POST');
  });
  test('sample audio never sends token to a different origin', () async {
    await expectLater(
      api.loadSampleAudio('https://untrusted.example/audio.wav'),
      throwsA(isA<ApiException>()),
    );
    expect(transport.requests, isEmpty);
  });
  test('voice errors are propagated instead of played as audio', () async {
    transport.responses.add(
      jsonResponse(503, {
        'code': 'speech_unavailable',
        'message': 'Unavailable',
      }),
    );
    await expectLater(api.previewVoice('v'), throwsA(isA<ApiException>()));
  });
  test('speech upload identifies native PCM recording as WAV', () async {
    transport.responses.add(
      jsonResponse(503, {'code': 'offline', 'message': 'Offline'}),
    );
    await expectLater(
      api.submitSpeaking(
        requestId: 'r',
        cardId: 'c',
        voiceId: 'v',
        audio: Uint8List.fromList([82, 73, 70, 70]),
      ),
      throwsA(isA<ApiException>()),
    );
    final body = utf8.decode(transport.requests.single.body!);
    expect(body, contains('filename="recording.wav"'));
    expect(body, contains('Content-Type: audio/wav'));
  });
}
