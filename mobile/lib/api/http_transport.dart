import 'dart:io';
import 'dart:typed_data';

class TransportRequest {
  final String method;
  final Uri uri;
  final Map<String, String> headers;
  final Uint8List? body;

  const TransportRequest(this.method, this.uri, this.headers, this.body);
}

class TransportResponse {
  final int statusCode;
  final Map<String, String> headers;
  final Uint8List body;

  const TransportResponse(this.statusCode, this.headers, this.body);
}

abstract interface class HttpTransport {
  Future<TransportResponse> send(TransportRequest request);
}

class IOHttpTransport implements HttpTransport {
  final HttpClient _client;

  IOHttpTransport([HttpClient? client]) : _client = client ?? HttpClient();

  @override
  Future<TransportResponse> send(TransportRequest request) async {
    final outgoing = await _client.openUrl(request.method, request.uri);
    request.headers.forEach(outgoing.headers.set);
    if (request.body != null) {
      outgoing.add(request.body!);
    }
    final incoming = await outgoing.close();
    final chunks = <int>[];
    await for (final chunk in incoming) {
      chunks.addAll(chunk);
    }
    final headers = <String, String>{};
    incoming.headers.forEach((name, values) {
      headers[name.toLowerCase()] = values.join(',');
    });
    return TransportResponse(
      incoming.statusCode,
      headers,
      Uint8List.fromList(chunks),
    );
  }
}
