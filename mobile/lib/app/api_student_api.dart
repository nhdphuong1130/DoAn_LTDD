import 'dart:async';
import 'dart:typed_data';

import '../api/api_client.dart';
import '../api/api_error.dart';
import 'student_api.dart';

class ApiStudentApi implements StudentApi {
  final ApiClient _client;
  final TokenStore _tokens;

  final Duration imagePollInterval;
  final int imagePollMaxAttempts;
  final Future<void> Function(Duration) _delay;

  ApiStudentApi(
    this._client,
    this._tokens, {
    required this.imagePollInterval,
    required this.imagePollMaxAttempts,
    Future<void> Function(Duration)? delay,
  }) : _delay = delay ?? Future<void>.delayed;

  @override
  Future<void> login(String email, String password) async {
    final response = await _client.postJson('/api/v1/auth/login', {
      'email': email,
      'password': password,
    });
    final token = response.body['access_token'] as String?;
    if (token == null || token.isEmpty) {
      throw const ApiException(
        code: 'invalid_login_response',
        message: 'Login response did not include an access token',
        statusCode: 502,
      );
    }
    await _tokens.write(token);
  }

  @override
  Future<List<LessonSummary>> loadLessons() async {
    final response = await _client.getJson('/api/v1/textbooks/units?limit=100');
    final items = response.body['items'] as List<dynamic>? ?? const [];
    return items
        .map((raw) {
          final item = raw as Map<String, dynamic>;
          return LessonSummary(
            item['number'] as int,
            item['title'] as String,
            item['section_title'] as String? ?? 'Bài học',
            id: item['id'] as String? ?? '',
          );
        })
        .toList(growable: false);
  }

  @override
  Future<List<LessonFragment>> loadFragments(String unitId) async {
    final response = await _client.getJson('/api/v1/lessons/$unitId/fragments');
    final items = response.body['items'] as List<dynamic>? ?? const [];
    return items
        .map((raw) {
          final item = raw as Map<String, dynamic>;
          return LessonFragment(
            id: item['id'] as String? ?? '',
            printedPage: item['printed_page'] as int?,
            pdfPage: item['pdf_page'] as int? ?? 0,
            text: item['normalized_text'] as String? ?? '',
            sectionTitle: item['section_title'] as String?,
            activityNumber: item['activity_number'] as String?,
            activityType: item['activity_type'] as String?,
            activityInstruction: item['activity_instruction'] as String?,
          );
        })
        .toList(growable: false);
  }

  @override
  Future<LessonDetail> loadLessonDetail(String unitId) async {
    final response = await _client.getJson('/api/v1/lessons/$unitId/structure');
    final body = response.body;
    final sectionsRaw = body['sections'] as List<dynamic>? ?? const [];
    final sections = sectionsRaw.map((sRaw) {
      final s = sRaw as Map<String, dynamic>;
      final activitiesRaw = s['activities'] as List<dynamic>? ?? const [];
      final activities = activitiesRaw.map((aRaw) {
        final a = aRaw as Map<String, dynamic>;
        final fragmentsRaw = a['fragments'] as List<dynamic>? ?? const [];
        final fragments = fragmentsRaw.map((fRaw) {
          final f = fRaw as Map<String, dynamic>;
          return LessonFragment(
            id: f['id'] as String? ?? '',
            printedPage: f['printed_page'] as int?,
            pdfPage: f['pdf_page'] as int? ?? 0,
            text: f['normalized_text'] as String? ?? '',
            sectionTitle: s['title'] as String?,
            activityNumber: a['number'] as String?,
            activityType: a['activity_type'] as String?,
            activityInstruction: a['instruction'] as String?,
          );
        }).toList(growable: false);
        final audioTracksRaw = a['audio_tracks'] as List<dynamic>? ?? const [];
        final audioTracks = audioTracksRaw.map((tRaw) {
          final t = tRaw as Map<String, dynamic>;
          return LessonAudioTrack(
            id: t['id'] as String? ?? '',
            trackNumber: t['track_number'] as int? ?? 0,
            audioUrl: t['audio_url'] as String? ?? '',
          );
        }).toList(growable: false);
        return LessonActivity(
          id: a['id'] as String? ?? '',
          number: a['number'] as String?,
          activityType: a['activity_type'] as String? ?? 'general',
          instruction: a['instruction'] as String?,
          audioTracks: audioTracks,
          fragments: fragments,
        );
      }).toList(growable: false);
      return LessonSection(
        id: s['id'] as String? ?? '',
        title: s['title'] as String? ?? '',
        sectionType: s['section_type'] as String? ?? 'lesson',
        position: s['position'] as int? ?? 0,
        activities: activities,
      );
    }).toList(growable: false);

    return LessonDetail(
      id: body['id'] as String? ?? unitId,
      unitNumber: body['number'] as int? ?? 0,
      title: body['title'] as String? ?? '',
      sections: sections,
    );
  }

  @override
  Future<QuizOptions> loadQuizOptions() async {
    final response = await _client.getJson('/api/v1/quizzes/options');
    return QuizOptions(
      (response.body['preset_durations'] as List<dynamic>).cast<int>(),
      response.body['custom_minimum_minutes'] as int,
      response.body['custom_maximum_minutes'] as int,
      response.body['max_audio_plays'] as int,
    );
  }

  @override
  Future<TutorResult> askTutor(TutorQuery query) async {
    try {
      String? uploadId;
      if (query.image != null) {
        final uploaded = await _client.postMultipart(
          '/api/v1/tutor/images',
          fieldName: 'image',
          filename: query.image!.name,
          mediaType: query.image!.mediaType,
          bytes: Uint8List.fromList(query.image!.bytes),
        );
        uploadId = uploaded.body['id'] as String;
        var uploadStatus = uploaded.body;
        for (var attempt = 0; attempt < imagePollMaxAttempts; attempt++) {
          final status = uploadStatus['status'] as String?;
          if (status == 'ready') break;
          if (status == 'failed') {
            throw ApiException(
              code:
                  uploadStatus['failure_code'] as String? ??
                  'image_processing_failed',
              message: 'Image processing failed',
              statusCode: 422,
            );
          }
          await _delay(imagePollInterval);
          uploadStatus = (await _client.getJson(
            '/api/v1/tutor/images/$uploadId',
          )).body;
          if (attempt == imagePollMaxAttempts - 1 &&
              uploadStatus['status'] != 'ready') {
            throw const ApiException(
              code: 'image_processing_timeout',
              message: 'Image processing did not finish in time',
              statusCode: 408,
            );
          }
        }
      }
      final response = await _client.postJson('/api/v1/tutor/ask', {
        'question': query.question,
        'language': query.language == TutorLanguage.vietnamese ? 'vi' : 'en',
        'upload_id': ?uploadId,
      });
      final citations =
          response.body['citations'] as List<dynamic>? ?? const [];
      return TutorResult(
        response.body['answer'] as String,
        citations
            .map((raw) {
              final item = raw as Map<String, dynamic>;
              return SourceReference(
                item['fragment_id'] as String,
                item['pdf_page'] as int,
                item['printed_page'] as int?,
              );
            })
            .toList(growable: false),
      );
    } on ApiException catch (error) {
      if (error.code == 'out_of_scope') throw TutorRefusal(error.code);
      rethrow;
    }
  }

  @override
  Future<QuizSession> createQuiz(QuizSetup setup) async {
    final response = await _client.postJson('/api/v1/quizzes', {
      'duration_minutes': setup.durationMinutes,
      'difficulty': setup.difficulty,
    });
    final questionsList = (response.body['questions'] as List<dynamic>? ?? const [])
        .map((raw) {
          final item = raw as Map<String, dynamic>;
          return QuizQuestion(
            item['id'] as String,
            item['prompt'] as String,
          );
        })
        .toList(growable: false);
    return QuizSession(
      response.body['id'] as String,
      response.body['duration_minutes'] as int,
      response.body['difficulty'] as String,
      questionsList,
    );
  }

  @override
  Future<QuizResult> submitQuiz(String quizId) async {
    final response = await _client.postJson(
      '/api/v1/quizzes/$quizId/submit',
      const {},
    );
    return QuizResult(
      response.body['correct'] as int,
      response.body['total'] as int,
    );
  }
}
