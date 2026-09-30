import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

abstract interface class SpeechRecorder {
  Future<void> start();
  Future<Uint8List> stop();
  Future<void> play(Uint8List bytes);
  Future<void> dispose();
}

class NativeSpeechRecorder implements SpeechRecorder {
  static const _channel = MethodChannel('english7/speech');
  void _supported() {
    if (kIsWeb || defaultTargetPlatform != TargetPlatform.android) {
      throw const SpeechRecordingException(
        'Thu âm hiện được hỗ trợ trên Android. Bạn vẫn có thể học flashcard.',
      );
    }
  }

  @override
  Future<void> start() async {
    _supported();
    try {
      await _channel.invokeMethod<void>('start');
    } on PlatformException catch (e) {
      throw SpeechRecordingException(
        e.code == 'permission_denied'
            ? 'Chưa có quyền microphone. Hãy cho phép microphone trong Cài đặt ứng dụng rồi thử lại.'
            : 'Không thể thu âm. Vui lòng thử lại.',
      );
    }
  }

  @override
  Future<Uint8List> stop() async {
    _supported();
    final bytes = await _channel.invokeMethod<Uint8List>('stop');
    if (bytes == null || bytes.isEmpty) {
      throw const SpeechRecordingException('Bản thu trống. Vui lòng thu lại.');
    }
    return bytes;
  }

  @override
  Future<void> play(Uint8List bytes) async {
    _supported();
    await _channel.invokeMethod<void>('play', bytes);
  }

  @override
  Future<void> dispose() async {
    if (!kIsWeb && defaultTargetPlatform == TargetPlatform.android) {
      try {
        await _channel.invokeMethod<void>('dispose');
      } on PlatformException catch (_) {
        /* Native activity also cleans up. */
      } on MissingPluginException catch (_) {
        /* No native channel in widget tests. */
      }
    }
  }
}

class SpeechRecordingException implements Exception {
  final String message;
  const SpeechRecordingException(this.message);
  @override
  String toString() => message;
}
