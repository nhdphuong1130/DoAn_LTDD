import 'dart:async';
import 'dart:typed_data';

import 'package:flutter/material.dart';

import '../../app/learning_api.dart';
import '../../api/api_error.dart';
import '../../services/speech_recorder.dart';

class SpeakingScreen extends StatefulWidget {
  final LearningApi api;
  final Flashcard card;
  final SpeechRecorder? recorder;
  const SpeakingScreen({
    super.key,
    required this.api,
    required this.card,
    this.recorder,
  });
  @override
  State<SpeakingScreen> createState() => _SpeakingScreenState();
}

class _SpeakingScreenState extends State<SpeakingScreen> {
  late final SpeechRecorder _recorder =
      widget.recorder ?? NativeSpeechRecorder();
  SpeakingVoices? _voices;
  String? _voice, _error, _requestId, _submittedVoice;
  Uint8List? _audio;
  SpeakingResult? _result;
  Timer? _timer;
  bool _busy = false, _recording = false;
  @override
  void initState() {
    super.initState();
    _loadVoices();
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
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final card = widget.card;
    final ready = _voices?.available == true && _voice != null;
    return Scaffold(
      appBar: AppBar(title: const Text('Luyện nói')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(card.word, style: Theme.of(context).textTheme.headlineMedium),
          Text(card.meaning),
          Text(card.sourceLabel ?? 'Nội dung cá nhân'),
          const SizedBox(height: 16),
          if (card.audioUrl == null)
            const Text('Chưa có audio tiếng Anh đã kiểm duyệt cho từ này.')
          else
            OutlinedButton(
              onPressed: _busy || _recording
                  ? null
                  : () => _run(
                      () => _playResponse(
                        widget.api.loadSampleAudio(card.audioUrl!),
                      ),
                    ),
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
              initialValue: _voice,
              decoration: const InputDecoration(labelText: 'Giọng gia sư'),
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
            Text(
              _error!,
              style: TextStyle(color: Theme.of(context).colorScheme.error),
            ),
          if (_busy) const LinearProgressIndicator(),
          if (_recording)
            FilledButton(
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
            OutlinedButton(
              onPressed: _busy
                  ? null
                  : () => _run(() => _recorder.play(_audio!)),
              child: const Text('Nghe bản thu'),
            ),
            FilledButton(
              onPressed: _busy || !ready ? null : _send,
              child: const Text('Gửi bản thu'),
            ),
          ],
          if (_result != null) ...[
            const Divider(),
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
}
