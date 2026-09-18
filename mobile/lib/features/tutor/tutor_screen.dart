import 'package:flutter/material.dart';

import '../../app/student_api.dart';
import '../../widgets/source_citation.dart';
import 'image_selector.dart';

class TutorScreen extends StatefulWidget {
  final StudentApi api;
  final ImageSelector imageSelector;
  const TutorScreen({
    super.key,
    required this.api,
    required this.imageSelector,
  });

  @override
  State<TutorScreen> createState() => _TutorScreenState();
}

class _TutorScreenState extends State<TutorScreen> {
  final _question = TextEditingController();
  TutorLanguage _language = TutorLanguage.vietnamese;
  SelectedImage? _image;
  TutorResult? _result;
  bool _refused = false;
  bool _busy = false;

  @override
  void dispose() {
    _question.dispose();
    super.dispose();
  }

  Future<void> _selectImage() async {
    final selected = await widget.imageSelector.select();
    if (mounted && selected != null) setState(() => _image = selected);
  }

  Future<void> _ask() async {
    if (_question.text.trim().isEmpty) return;
    setState(() {
      _busy = true;
      _refused = false;
      _result = null;
    });
    try {
      final result = await widget.api.askTutor(
        TutorQuery(_question.text.trim(), _language, _image?.path),
      );
      if (mounted) setState(() => _result = result);
    } on TutorRefusal {
      if (mounted) setState(() => _refused = true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => ListView(
    padding: const EdgeInsets.all(16),
    children: [
      Text('AI Tutor', style: Theme.of(context).textTheme.headlineSmall),
      const SizedBox(height: 12),
      SegmentedButton<TutorLanguage>(
        segments: const [
          ButtonSegment(
            value: TutorLanguage.vietnamese,
            label: Text('Tiếng Việt'),
          ),
          ButtonSegment(value: TutorLanguage.english, label: Text('Tiếng Anh')),
        ],
        selected: {_language},
        onSelectionChanged: (selection) =>
            setState(() => _language = selection.first),
      ),
      const SizedBox(height: 16),
      TextField(
        key: const Key('tutor-question'),
        controller: _question,
        minLines: 2,
        maxLines: 5,
        decoration: const InputDecoration(
          labelText: 'Câu hỏi về Unit 1–2',
          alignLabelWithHint: true,
        ),
      ),
      const SizedBox(height: 12),
      OutlinedButton.icon(
        key: const Key('select-image'),
        onPressed: _selectImage,
        icon: const Icon(Icons.add_photo_alternate_outlined),
        label: Text(_image?.name ?? 'Chọn ảnh bài tập'),
      ),
      const SizedBox(height: 8),
      FilledButton.icon(
        onPressed: _busy ? null : _ask,
        icon: const Icon(Icons.auto_awesome),
        label: Text(_busy ? 'Đang đối chiếu SGK…' : 'Hỏi AI'),
      ),
      if (_refused) ...[
        const SizedBox(height: 16),
        Card(
          key: const Key('tutor-refusal'),
          color: Theme.of(context).colorScheme.errorContainer,
          child: const Padding(
            padding: EdgeInsets.all(16),
            child: Text(
              'Nội dung này không có trong phạm vi SGK Unit 1–2 đã xác minh.',
            ),
          ),
        ),
      ],
      if (_result != null) ...[
        const SizedBox(height: 16),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(_result!.answer),
                const SizedBox(height: 12),
                for (final citation in _result!.citations)
                  SourceCitation(source: citation),
              ],
            ),
          ),
        ),
      ],
    ],
  );
}
