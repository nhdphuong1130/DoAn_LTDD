import 'dart:async';
import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../../app/learning_api.dart';
import '../../api/api_error.dart';
import '../../services/speech_recorder.dart';
import '../../services/tts_service.dart';

class SpeakingScreen extends StatefulWidget {
  final LearningApi api;
  final Flashcard card;
  final SpeechRecorder? recorder;
  final TtsService? ttsService;

  const SpeakingScreen({
    super.key,
    required this.api,
    required this.card,
    this.recorder,
    this.ttsService,
  });

  @override
  State<SpeakingScreen> createState() => _SpeakingScreenState();
}

class _SpeakingScreenState extends State<SpeakingScreen> {
  late final SpeechRecorder _recorder =
      widget.recorder ?? NativeSpeechRecorder();
  late final TtsService _tts = widget.ttsService ?? NativeTtsService();

  SpeakingVoices? _voices;
  String? _voice, _error, _requestId, _submittedVoice;
  Uint8List? _audio;
  SpeakingResult? _result;
  Timer? _timer;
  bool _busy = false, _recording = false;
  late bool _isSentenceMode;
  String? _activeTappedWord;

  @override
  void initState() {
    super.initState();
    _isSentenceMode = widget.card.example.trim().isNotEmpty;
    _loadVoices();
  }

  String get _effectivePrompt {
    if (_isSentenceMode && widget.card.example.trim().isNotEmpty) {
      return widget.card.example.trim();
    }
    return widget.card.word.trim();
  }

  List<String> get _promptWords {
    return _effectivePrompt
        .split(RegExp(r'\s+'))
        .where((w) => w.trim().isNotEmpty)
        .toList();
  }

  String _clean(String w) =>
      w.toLowerCase().replaceAll(RegExp(r"[^a-z0-9']"), '');

  WordEvaluation? _getWordEvaluation(String word, int index) {
    final evals = _result?.wordEvaluations;
    if (evals == null || evals.isEmpty) return null;
    final clean = _clean(word);
    if (clean.isEmpty) return null;

    if (index < evals.length && _clean(evals[index].word) == clean) {
      return evals[index];
    }
    for (final e in evals) {
      if (_clean(e.word) == clean) return e;
    }
    return null;
  }

  Future<void> _loadVoices() async {
    try {
      final voices = await widget.api.loadVoices();
      if (!mounted) return;
      setState(() {
        _voices = voices;
        _voice = voices.items.any((v) => v.id == voices.selectedVoice)
            ? voices.selectedVoice
            : voices.items.firstOrNull?.id;
        _error = null;
      });
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Không tải được giọng đọc. Hãy thử lại.');
      }
    }
  }

  Future<void> _run(Future<void> Function() work) async {
    if (_busy) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await work();
    } catch (e) {
      if (mounted) {
        setState(
          () => _error = e is SpeechRecordingException
              ? e.message
              : e is ApiException &&
                    const {
                      'no_speech',
                      'invalid_recording',
                      'recording_too_large',
                    }.contains(e.code)
              ? 'Chưa nghe rõ bản thu. Em hãy chọn Thu lại và nói rõ trong 15 giây.'
              : 'Thao tác chưa thành công. Kiểm tra kết nối và thử lại.',
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _playResponse(Future<Uint8List> response) async {
    final bytes = await response;
    if (mounted) await _recorder.play(bytes);
  }

  Future<void> _speakPrompt({double rate = 0.48}) async {
    await _run(() async {
      try {
        await _tts.speak(_effectivePrompt, language: 'en-GB', rate: rate);
      } catch (_) {
        if (!_isSentenceMode) {
          await _playResponse(
            widget.card.audioUrl != null
                ? widget.api.loadSampleAudio(widget.card.audioUrl!)
                : widget.api.loadCardAudio(widget.card.id),
          );
        }
      }
    });
  }

  Future<void> _speakSingleWord(String word) async {
    final cleanWord = word.replaceAll(RegExp(r"[^a-zA-Z0-9']"), '');
    if (cleanWord.isEmpty) return;
    setState(() => _activeTappedWord = word);
    try {
      await _tts.speak(cleanWord, language: 'en-GB', rate: 0.42);
    } catch (_) {
      // Ignored if device TTS unavailable
    } finally {
      if (mounted) {
        Future.delayed(const Duration(milliseconds: 400), () {
          if (mounted) setState(() => _activeTappedWord = null);
        });
      }
    }
  }

  Future<void> _start() => _run(() async {
    await _recorder.start();
    if (!mounted) {
      await _recorder.dispose();
      return;
    }
    setState(() {
      _recording = true;
      _audio = null;
      _result = null;
      _requestId = null;
      _submittedVoice = null;
    });
    _timer = Timer(const Duration(seconds: 15), () {
      if (mounted) _stop();
    });
  });

  Future<void> _stop() => _run(() async {
    _timer?.cancel();
    try {
      final bytes = await _recorder.stop();
      if (mounted) setState(() => _audio = bytes);
    } finally {
      if (mounted) setState(() => _recording = false);
    }
  });

  Future<void> _send() => _run(() async {
    _requestId ??= learningRequestId();
    _submittedVoice ??= _voice;
    final result = await widget.api.submitSpeaking(
      requestId: _requestId!,
      cardId: widget.card.id,
      voiceId: _submittedVoice!,
      audio: _audio!,
      prompt: _effectivePrompt,
    );
    _audio = null;
    if (mounted) {
      setState(() => _result = result);
      await _recorder.dispose();
    }
  });

  @override
  void dispose() {
    _timer?.cancel();
    _audio = null;
    unawaited(_recorder.dispose());
    unawaited(_tts.dispose());
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final card = widget.card;
    final ready = _voices?.available == true && _voice != null;
    final hasExample = card.example.trim().isNotEmpty;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Luyện nói'),
        toolbarHeight: 48,
      ),
      body: ListView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        children: [
          // Word & Meaning Header
          Text(card.word, style: Theme.of(context).textTheme.headlineMedium),
          Text(card.meaning),
          Text(card.sourceLabel ?? 'Nội dung cá nhân'),

          // Duolingo Interactive Word Chips & Mode Toggle
          if (hasExample) ...[
            const SizedBox(height: 6),
            Row(
              children: [
                ChoiceChip(
                  visualDensity: VisualDensity.compact,
                  label: const Text('Cả câu'),
                  selected: _isSentenceMode,
                  onSelected: _busy || _recording
                      ? null
                      : (s) {
                          if (s) {
                            setState(() {
                              _isSentenceMode = true;
                              _result = null;
                              _audio = null;
                              _error = null;
                            });
                          }
                        },
                ),
                const SizedBox(width: 6),
                ChoiceChip(
                  visualDensity: VisualDensity.compact,
                  label: const Text('Từ vựng'),
                  selected: !_isSentenceMode,
                  onSelected: _busy || _recording
                      ? null
                      : (s) {
                          if (s) {
                            setState(() {
                              _isSentenceMode = false;
                              _result = null;
                              _audio = null;
                              _error = null;
                            });
                          }
                        },
                ),
              ],
            ),
          ],

          const SizedBox(height: 6),
          // Interactive Word Chips
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surfaceContainerHighest.withValues(alpha: 0.35),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: Theme.of(context).colorScheme.outlineVariant.withValues(alpha: 0.5),
              ),
            ),
            child: Wrap(
              spacing: 6,
              runSpacing: 4,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                for (int i = 0; i < _promptWords.length; i++)
                  _buildWordChip(_promptWords[i], i),
                // Slow Turtle Button
                IconButton(
                  visualDensity: VisualDensity.compact,
                  padding: EdgeInsets.zero,
                  constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
                  onPressed: _busy || _recording ? null : () => _speakPrompt(rate: 0.32),
                  icon: const Icon(Icons.slow_motion_video_rounded, size: 20),
                  tooltip: 'Nghe chậm (0.5x)',
                ),
              ],
            ),
          ),
          const SizedBox(height: 6),

          // Standard audio button (maintains test compatibility)
          OutlinedButton(
            onPressed: _busy || _recording ? null : () => _speakPrompt(rate: 0.48),
            child: const Text('Nghe mẫu tiếng Anh'),
          ),

          const Text(
            'Đọc từ mẫu, thu tối đa 15 giây. Bản thu chỉ được gửi khi bạn chọn gửi.',
          ),

          if (!ready)
            TextButton(
              onPressed: _busy || _recording ? null : () => _run(_loadVoices),
              child: const Text('Tải lại giọng đọc'),
            ),
          if (_voices != null && !ready)
            const Text(
              'Dịch vụ giọng nói chưa sẵn sàng. Bạn có thể tiếp tục học flashcard.',
            ),
          if (_voices != null && _voices!.items.isNotEmpty)
            DropdownButtonFormField<String>(
              isDense: true,
              initialValue: _voice,
              decoration: const InputDecoration(
                labelText: 'Giọng gia sư',
                isDense: true,
                contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 8),
              ),
              items: _voices!.items
                  .map(
                    (v) => DropdownMenuItem(value: v.id, child: Text(v.name)),
                  )
                  .toList(),
              onChanged: _busy || _recording || _requestId != null
                  ? null
                  : (value) {
                      if (value != null) {
                        _run(() async {
                          await widget.api.selectVoice(value);
                          if (mounted) setState(() => _voice = value);
                        });
                      }
                    },
            ),
          TextButton(
            onPressed: !ready || _busy || _recording
                ? null
                : () => _run(
                    () => _playResponse(widget.api.previewVoice(_voice!)),
                  ),
            child: const Text('Nghe thử giọng'),
          ),

          if (_error != null)
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 2),
              child: Text(
                _error!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              ),
            ),
          if (_busy) const LinearProgressIndicator(),
          const SizedBox(height: 6),

          // Primary Record / Stop Button
          if (_recording)
            FilledButton(
              style: FilledButton.styleFrom(
                backgroundColor: const Color(0xFFDC2626),
                foregroundColor: Colors.white,
              ),
              onPressed: _busy ? null : _stop,
              child: const Text('Dừng thu'),
            )
          else
            FilledButton(
              onPressed: _busy ? null : _start,
              child: Text(
                _audio == null && _result == null ? 'Thu âm' : 'Thu lại',
              ),
            ),

          if (_audio != null) ...[
            const SizedBox(height: 4),
            OutlinedButton(
              onPressed: _busy
                  ? null
                  : () => _run(() => _recorder.play(_audio!)),
              child: const Text('Nghe bản thu'),
            ),
            const SizedBox(height: 4),
            FilledButton(
              style: FilledButton.styleFrom(
                backgroundColor: const Color(0xFF16A34A),
                foregroundColor: Colors.white,
              ),
              onPressed: _busy || !ready ? null : _send,
              child: const Text('Gửi bản thu'),
            ),
          ],

          // Results Presentation (Duolingo Style Feedback)
          if (_result != null) ...[
            const Divider(height: 20),
            _buildResultBanner(context),
            const SizedBox(height: 8),
            Text('Câu mẫu: ${_result!.prompt}'),
            Text('Bản chép lời: ${_result!.transcript}'),
            Text(
              'Mức độ khớp câu mẫu: ${_result!.matchPercent.toStringAsFixed(0)}%',
            ),
            const Text(
              'Đây không phải điểm phát âm. Nhận dạng giọng nói có thể sai.',
            ),
            Text(
              'Từ chưa nhận ra: ${_result!.missingWords.isEmpty ? "Không có" : _result!.missingWords.join(", ")}',
            ),
            Text(
              'Từ thừa: ${_result!.extraWords.isEmpty ? "Không có" : _result!.extraWords.join(", ")}',
            ),
            Text(_result!.feedback),
            if (_result!.sourceLabel != null) Text(_result!.sourceLabel!),
            const SizedBox(height: 6),
            OutlinedButton(
              onPressed: _busy
                  ? null
                  : () => _run(
                      () => _playResponse(
                        widget.api.loadSpeakingAudio(_result!.id),
                      ),
                    ),
              child: const Text('Nghe phản hồi'),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildWordChip(String word, int index) {
    final eval = _getWordEvaluation(word, index);
    final isTapped = _activeTappedWord == word;

    Color bg = Theme.of(context).colorScheme.surface;
    Color border = Theme.of(context).colorScheme.outlineVariant;
    Color textColor = Theme.of(context).colorScheme.onSurface;
    IconData? badgeIcon;

    if (eval != null) {
      if (eval.status == 'correct') {
        bg = const Color(0xFFDCFCE7);
        border = const Color(0xFF22C55E);
        textColor = const Color(0xFF15803D);
        badgeIcon = Icons.check_circle_rounded;
      } else if (eval.status == 'near') {
        bg = const Color(0xFFFEF9C3);
        border = const Color(0xFFEAB308);
        textColor = const Color(0xFFA16207);
        badgeIcon = Icons.info_rounded;
      } else {
        bg = const Color(0xFFFEE2E2);
        border = const Color(0xFFEF4444);
        textColor = const Color(0xFFB91C1C);
        badgeIcon = Icons.cancel_rounded;
      }
    } else if (isTapped) {
      bg = Theme.of(context).colorScheme.primaryContainer;
      border = Theme.of(context).colorScheme.primary;
      textColor = Theme.of(context).colorScheme.onPrimaryContainer;
    }

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: () => _speakSingleWord(word),
        borderRadius: BorderRadius.circular(8),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          decoration: BoxDecoration(
            color: bg,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: border, width: eval != null ? 1.5 : 1.0),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                word,
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                  color: textColor,
                ),
              ),
              if (badgeIcon != null) ...[
                const SizedBox(width: 4),
                Icon(badgeIcon, size: 13, color: textColor),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildResultBanner(BuildContext context) {
    final match = _result!.matchPercent;
    Color bg;
    Color text;
    IconData icon;
    String title;

    if (match >= 80) {
      bg = const Color(0xFFDCFCE7);
      text = const Color(0xFF15803D);
      icon = Icons.check_circle_rounded;
      title = 'Xuất sắc! Phát âm rất chuẩn 🎉';
    } else if (match >= 50) {
      bg = const Color(0xFFE0F2FE);
      text = const Color(0xFF0369A1);
      icon = Icons.thumb_up_rounded;
      title = 'Rất tốt! Cố gắng luyện thêm nhé 👍';
    } else {
      bg = const Color(0xFFFEE2E2);
      text = const Color(0xFFB91C1C);
      icon = Icons.lightbulb_rounded;
      title = 'Hãy nghe lại câu mẫu và thử lại nhé! 🎯';
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          Icon(icon, color: text, size: 20),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              title,
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 13.5,
                color: text,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
