import 'package:english7_mobile/config/app_config.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('requires a configured API base URL', () {
    expect(
      () => AppConfig.fromEnvironment(const {}),
      throwsA(isA<ConfigurationException>()),
    );
  });

  test('normalizes the base URL without embedding API routes', () {
    final config = AppConfig.fromEnvironment(const {
      'API_BASE_URL': 'http://10.0.2.2:8000/',
      'IMAGE_POLL_INTERVAL_MS': '250',
      'IMAGE_POLL_MAX_ATTEMPTS': '20',
    });

    expect(config.apiBaseUrl.toString(), 'http://10.0.2.2:8000');
    expect(
      config.resolve('/api/v1/health').toString(),
      'http://10.0.2.2:8000/api/v1/health',
    );
    expect(config.imagePollInterval, const Duration(milliseconds: 250));
    expect(config.imagePollMaxAttempts, 20);
  });

  test('rejects missing image polling configuration', () {
    expect(
      () => AppConfig.fromEnvironment(const {
        'API_BASE_URL': 'http://10.0.2.2:8000',
      }),
      throwsA(isA<ConfigurationException>()),
    );
  });
}
