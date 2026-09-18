class ApiException implements Exception {
  final String code;
  final String message;
  final Object? details;
  final String? traceId;
  final int statusCode;

  const ApiException({
    required this.code,
    required this.message,
    required this.statusCode,
    this.details,
    this.traceId,
  });

  @override
  String toString() => 'ApiException($code, traceId: $traceId): $message';
}
