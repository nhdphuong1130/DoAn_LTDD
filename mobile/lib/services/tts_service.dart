import 'package:flutter_tts/flutter_tts.dart';

abstract interface class TtsService {
  Future<void> speak(String text, {String language = 'en-GB'});
  Future<void> stop();
  Future<void> dispose();
}

class NativeTtsService implements TtsService {
  FlutterTts? _tts;
  bool _initialized = false;

  Future<FlutterTts> _getEngine() async {
    if (_tts != null) return _tts!;
    final tts = FlutterTts();
    await tts.setSpeechRate(0.45);
    await tts.setPitch(1.0);
    await tts.awaitSpeakCompletion(true);
    _tts = tts;
    _initialized = true;
    return tts;
  }

  @override
  Future<void> speak(String text, {String language = 'en-GB'}) async {
    final engine = await _getEngine();
    await engine.setLanguage(language);
    final result = await engine.speak(text);
    if (result == 0) {
      throw Exception('TTS engine failed to speak');
    }
  }

  @override
  Future<void> stop() async {
    if (_initialized && _tts != null) {
      await _tts!.stop();
    }
  }

  @override
  Future<void> dispose() async {
    if (_initialized && _tts != null) {
      await _tts!.stop();
      _tts = null;
      _initialized = false;
    }
  }
}

class FakeTtsService implements TtsService {
  final List<({String text, String language})> spoken = [];
  int stops = 0;
  bool disposed = false;
  Object? error;

  @override
  Future<void> speak(String text, {String language = 'en-GB'}) async {
    if (error != null) throw error!;
    spoken.add((text: text, language: language));
  }

  @override
  Future<void> stop() async {
    stops++;
  }

  @override
  Future<void> dispose() async {
    disposed = true;
  }
}
