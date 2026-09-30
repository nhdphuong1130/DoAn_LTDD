import 'package:flutter_test/flutter_test.dart';
import 'package:english7_mobile/services/tts_service.dart';

void main() {
  test('FakeTtsService records spoken words and default language', () async {
    final tts = FakeTtsService();
    await tts.speak('gardening');
    await tts.speak('community', language: 'en-US');

    expect(tts.spoken.length, 2);
    expect(tts.spoken[0].text, 'gardening');
    expect(tts.spoken[0].language, 'en-GB');
    expect(tts.spoken[1].text, 'community');
    expect(tts.spoken[1].language, 'en-US');

    await tts.stop();
    expect(tts.stops, 1);

    await tts.dispose();
    expect(tts.disposed, isTrue);
  });

  test('FakeTtsService throws when configured with error', () async {
    final tts = FakeTtsService()..error = Exception('TTS unavailable');
    expect(() => tts.speak('hello'), throwsA(isA<Exception>()));
  });
}
