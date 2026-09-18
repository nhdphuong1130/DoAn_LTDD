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
    });

    expect(config.apiBaseUrl.toString(), 'http://10.0.2.2:8000');
    expect(config.resolve('/api/v1/health').toString(),
        'http://10.0.2.2:8000/api/v1/health');
  });
}
