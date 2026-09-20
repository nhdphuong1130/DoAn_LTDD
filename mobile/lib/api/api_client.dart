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

  Future<ApiResponse<Map<String, Object?>>> patchJson(
    String path,
    Map<String, Object?> payload,
  ) {
    return _requestJson('PATCH', path, payload);
  }

  Future<void> postNoContent(String path, Map<String, Object?> payload) async {
    final token = await _tokens.read();
    final response = await _transport.send(
      TransportRequest('POST', _config.resolve(path), {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        if (token != null && token.isNotEmpty) 'Authorization': 'Bearer $token',
      }, Uint8List.fromList(utf8.encode(jsonEncode(payload)))),
    );
    if (response.statusCode < 200 || response.statusCode >= 300) {
      _decodeResponse(response);
    }
  }

  Future<ApiResponse<Map<String, Object?>>> postMultipart(
    String path, {
    required String fieldName,
    required String filename,
    required String mediaType,
    required Uint8List bytes,
  }) async {
    final token = await _tokens.read();
    final boundary =
        'english7-${DateTime.now().microsecondsSinceEpoch.toRadixString(16)}';
    final safeFilename = filename.replaceAll(RegExp(r'[\r\n"]'), '_');
    final prefix = utf8.encode(
      '--$boundary\r\n'
      'Content-Disposition: form-data; name="$fieldName"; filename="$safeFilename"\r\n'
      'Content-Type: $mediaType\r\n\r\n',
    );
    final suffix = utf8.encode('\r\n--$boundary--\r\n');
    final body = Uint8List(prefix.length + bytes.length + suffix.length)
      ..setRange(0, prefix.length, prefix)
      ..setRange(prefix.length, prefix.length + bytes.length, bytes)
      ..setRange(
        prefix.length + bytes.length,
        prefix.length + bytes.length + suffix.length,
        suffix,
      );
    final response = await _transport.send(
      TransportRequest('POST', _config.resolve(path), {
        'Accept': 'application/json',
        'Content-Type': 'multipart/form-data; boundary=$boundary',
        if (token != null && token.isNotEmpty) 'Authorization': 'Bearer $token',
      }, body),
    );
    return _decodeResponse(response);
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
    return _decodeResponse(response);
  }

  ApiResponse<Map<String, Object?>> _decodeResponse(
    TransportResponse response,
  ) {
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
