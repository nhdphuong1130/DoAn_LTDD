import 'dart:convert';
import 'dart:typed_data';

import '../config/app_config.dart';
import 'api_error.dart';
import 'http_transport.dart';

abstract interface class TokenStore {
  Future<String?> read();
  Future<void> write(String token);
  Future<void> clear();
}

class ApiResponse<T> {
  final T body;
  final String? traceId;

  const ApiResponse(this.body, this.traceId);
}

class ApiClient {
  final AppConfig _config;
  final HttpTransport _transport;
  final TokenStore _tokens;

  const ApiClient(this._config, this._transport, this._tokens);

  Future<ApiResponse<Map<String, Object?>>> getJson(String path) {
    return _requestJson('GET', path);
  }

  Future<ApiResponse<Map<String, Object?>>> postJson(
    String path,
    Map<String, Object?> payload,
  ) {
    return _requestJson('POST', path, payload);
  }

  Future<ApiResponse<Map<String, Object?>>> _requestJson(
    String method,
    String path, [
    Map<String, Object?>? payload,
  ]) async {
    final token = await _tokens.read();
    final headers = <String, String>{
      'Accept': 'application/json',
      if (payload != null) 'Content-Type': 'application/json',
      if (token != null && token.isNotEmpty) 'Authorization': 'Bearer $token',
    };
    final body = payload == null
        ? null
        : Uint8List.fromList(utf8.encode(jsonEncode(payload)));
    final response = await _transport.send(
      TransportRequest(method, _config.resolve(path), headers, body),
    );
    final decoded = jsonDecode(utf8.decode(response.body));
    if (decoded is! Map<String, dynamic>) {
      throw ApiException(
        code: 'invalid_api_response',
        message: 'The API returned an invalid response',
        statusCode: response.statusCode,
        traceId: response.headers['x-trace-id'],
      );
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw ApiException(
        code: decoded['code'] as String? ?? 'http_error',
        message: decoded['message'] as String? ?? 'API request failed',
        details: decoded['details'],
        traceId:
            decoded['trace_id'] as String? ?? response.headers['x-trace-id'],
        statusCode: response.statusCode,
      );
    }
    return ApiResponse(
      Map<String, Object?>.from(decoded),
      response.headers['x-trace-id'],
    );
  }
}
