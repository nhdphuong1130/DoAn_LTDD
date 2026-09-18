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

  factory AppConfig.fromDartDefine() => AppConfig.fromEnvironment(const {
    'API_BASE_URL': String.fromEnvironment('API_BASE_URL'),
    'IMAGE_POLL_INTERVAL_MS': String.fromEnvironment('IMAGE_POLL_INTERVAL_MS'),
    'IMAGE_POLL_MAX_ATTEMPTS': String.fromEnvironment(
      'IMAGE_POLL_MAX_ATTEMPTS',
    ),
  });

  Uri resolve(String path) {
    final normalizedPath = path.startsWith('/') ? path : '/$path';
    return apiBaseUrl.replace(path: '${apiBaseUrl.path}$normalizedPath');
  }
}
