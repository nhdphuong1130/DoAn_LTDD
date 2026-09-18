class ConfigurationException implements Exception {
  final String message;
  const ConfigurationException(this.message);

  @override
  String toString() => 'ConfigurationException: $message';
}

class AppConfig {
  final Uri apiBaseUrl;

  const AppConfig._(this.apiBaseUrl);

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
    return AppConfig._(parsed.replace(path: normalizedPath));
  }

  factory AppConfig.fromDartDefine() => AppConfig.fromEnvironment(const {
        'API_BASE_URL': String.fromEnvironment('API_BASE_URL'),
      });

  Uri resolve(String path) {
    final normalizedPath = path.startsWith('/') ? path : '/$path';
    return apiBaseUrl.replace(path: '${apiBaseUrl.path}$normalizedPath');
  }
}
