import 'package:flutter/foundation.dart';

class ConfigurationException implements Exception {
  final String message;
  const ConfigurationException(this.message);

  @override
  String toString() => 'ConfigurationException: $message';
}

class AppConfig {
  final Uri apiBaseUrl;
  final Duration imagePollInterval;
  final int imagePollMaxAttempts;

  const AppConfig._(
    this.apiBaseUrl,
    this.imagePollInterval,
    this.imagePollMaxAttempts,
  );

  factory AppConfig.fromEnvironment(Map<String, String> environment) {
    final raw = environment['API_BASE_URL']?.trim();
    if (raw == null || raw.isEmpty) {
      throw const ConfigurationException(
        'API_BASE_URL must be supplied using --dart-define',
      );
    }
    final parsed = Uri.tryParse(raw);
    if (parsed == null ||
        !parsed.hasScheme ||
        parsed.host.isEmpty ||
        (parsed.scheme != 'http' && parsed.scheme != 'https')) {
      throw const ConfigurationException('API_BASE_URL is invalid');
    }
    final normalizedPath = parsed.path == '/'
        ? ''
        : parsed.path.replaceFirst(RegExp(r'/+$'), '');
    final pollMilliseconds = int.tryParse(
      environment['IMAGE_POLL_INTERVAL_MS'] ?? '',
    );
    final pollAttempts = int.tryParse(
      environment['IMAGE_POLL_MAX_ATTEMPTS'] ?? '',
    );
    if (pollMilliseconds == null ||
        pollMilliseconds <= 0 ||
        pollAttempts == null ||
        pollAttempts <= 0) {
      throw const ConfigurationException(
        'IMAGE_POLL_INTERVAL_MS and IMAGE_POLL_MAX_ATTEMPTS must be positive integers',
      );
    }
    return AppConfig._(
      parsed.replace(path: normalizedPath),
      Duration(milliseconds: pollMilliseconds),
      pollAttempts,
    );
  }

  factory AppConfig.fromDartDefine() {
    final baseUrl = const String.fromEnvironment('API_BASE_URL');
    final pollInterval = const String.fromEnvironment('IMAGE_POLL_INTERVAL_MS');
    final pollAttempts = const String.fromEnvironment('IMAGE_POLL_MAX_ATTEMPTS');

    final defaultBaseUrl = kIsWeb ? 'http://localhost:8000' : 'http://10.0.2.2:8000';

    return AppConfig.fromEnvironment({
      'API_BASE_URL': baseUrl.isNotEmpty ? baseUrl : defaultBaseUrl,
      'IMAGE_POLL_INTERVAL_MS': pollInterval.isNotEmpty ? pollInterval : '1000',
      'IMAGE_POLL_MAX_ATTEMPTS': pollAttempts.isNotEmpty ? pollAttempts : '30',
    });
  }

  Uri resolve(String path) {
    final uri = Uri.parse(path.startsWith('/') ? path : '/$path');
    return apiBaseUrl.replace(
      path: '${apiBaseUrl.path}${uri.path}',
      query: uri.hasQuery ? uri.query : null,
    );
  }
}
