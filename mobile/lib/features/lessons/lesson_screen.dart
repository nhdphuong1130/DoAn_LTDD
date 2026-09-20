import 'package:flutter/material.dart';

import '../../app/student_api.dart';
import '../../widgets/lesson_audio_player.dart';

class LessonScreen extends StatefulWidget {
  final StudentApi api;
  const LessonScreen({super.key, required this.api});

  @override
  State<LessonScreen> createState() => _LessonScreenState();
}

class _LessonScreenState extends State<LessonScreen> {
  late Future<List<LessonSummary>> _lessonsFuture;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    _lessonsFuture = widget.api.loadLessons();
  }

  Future<void> _refresh() async {
    setState(() {
      _load();
    });
    await _lessonsFuture;
  }

  @override
  Widget build(BuildContext context) => RefreshIndicator(
    onRefresh: _refresh,
    child: FutureBuilder<List<LessonSummary>>(
      future: _lessonsFuture,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return ListView(
            padding: const EdgeInsets.all(24),
            children: [
              const SizedBox(height: 60),
              const Icon(Icons.error_outline, size: 56, color: Colors.red),
              const SizedBox(height: 16),
              Text(
                'Lỗi khi tải danh sách bài học',
                textAlign: TextAlign.center,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(
                '${snapshot.error}',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.grey.shade700, fontSize: 13),
              ),
              const SizedBox(height: 20),
              Center(
                child: FilledButton.icon(
                  onPressed: () => setState(() => _load()),
                  icon: const Icon(Icons.refresh),
                  label: const Text('Thử lại'),
                ),
              ),
            ],
          );
        }
        final lessons = snapshot.data ?? [];
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text('Bài học', style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 12),
            for (final lesson in lessons)
              Card(
                elevation: 2,
                margin: const EdgeInsets.only(bottom: 12),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  leading: CircleAvatar(
                    backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                    foregroundColor: Theme.of(context).colorScheme.onPrimaryContainer,
                    child: Text(
                      lesson.title.toLowerCase().contains('review')
                          ? 'R${RegExp(r'Review\s*(\d+)', caseSensitive: false).firstMatch(lesson.title)?.group(1) ?? '1'}'
                          : '${lesson.unitNumber}',
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                  ),
                  title: Text(
                    lesson.title.toLowerCase().contains('review')
                        ? lesson.title
                        : 'Unit ${lesson.unitNumber}: ${lesson.title}',
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  subtitle: Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Row(
                      children: [
                        const Icon(Icons.verified, size: 16, color: Colors.green),
                        const SizedBox(width: 4),
                        Expanded(
                          child: Text(
                            lesson.sectionTitle,
                            style: TextStyle(color: Colors.grey.shade700),
                          ),
                        ),
                      ],
                    ),
                  ),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () => Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => LessonDetailScreen(lesson: lesson, api: widget.api),
                    ),
                  ),
                ),
              ),
          ],
        );
      },
    ),
  );
}

class LessonDetailScreen extends StatefulWidget {
  final LessonSummary lesson;
  final StudentApi? api;
  const LessonDetailScreen({super.key, required this.lesson, this.api});

  @override
  State<LessonDetailScreen> createState() => _LessonDetailScreenState();
}

class _LessonDetailScreenState extends State<LessonDetailScreen> {
  int? _selectedSectionIndex;
  Future<LessonDetail>? _detailFuture;

  @override
  void initState() {
    super.initState();
    _loadDetail();
  }

  @override
  void didUpdateWidget(covariant LessonDetailScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.lesson.id != widget.lesson.id) {
      _loadDetail();
    }
  }

  void _loadDetail() {
    if (widget.api != null && widget.lesson.id.isNotEmpty) {
      _detailFuture = widget.api!.loadLessonDetail(widget.lesson.id).catchError((err, stack) async {
        debugPrint('loadLessonDetail failed: $err\n$stack');
        final frags = await widget.api!.loadFragments(widget.lesson.id);
        return LessonDetail(
          id: widget.lesson.id,
          unitNumber: widget.lesson.unitNumber,
          title: widget.lesson.title,
          sections: [
            LessonSection(
              id: 'fallback-sec',
              title: widget.lesson.sectionTitle.isNotEmpty
                  ? widget.lesson.sectionTitle
                  : 'Nội dung bài học',
              sectionType: 'lesson',
              position: 1,
              activities: [
                LessonActivity(
                  id: 'fallback-act',
                  number: '1',
                  activityType: 'general',
                  instruction: 'Nội dung từ sách giáo khoa',
                  fragments: frags,
                ),
              ],
            ),
          ],
        );
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          widget.lesson.title.toLowerCase().contains('review')
              ? widget.lesson.title
              : 'Unit ${widget.lesson.unitNumber}: ${widget.lesson.title}',
        ),
      ),
      body: widget.api == null || widget.lesson.id.isEmpty || _detailFuture == null
          ? _buildEmptyState(context)
          : FutureBuilder<LessonDetail>(
              future: _detailFuture,
              builder: (context, snapshot) {
                if (snapshot.connectionState == ConnectionState.waiting) {
                  return const Center(child: CircularProgressIndicator());
                }
                if (snapshot.hasError) {
                  debugPrint('FutureBuilder snapshot error: ${snapshot.error}\n${snapshot.stackTrace}');
                  return Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          const Icon(Icons.error_outline, size: 48, color: Colors.red),
                          const SizedBox(height: 12),
                          Text(
                            'Lỗi tải nội dung bài học',
                            style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            '${snapshot.error}',
                            textAlign: TextAlign.center,
                            style: TextStyle(color: Colors.grey.shade700, fontSize: 13),
                          ),
                          const SizedBox(height: 16),
                          FilledButton.icon(
                            onPressed: () => setState(() => _loadDetail()),
                            icon: const Icon(Icons.refresh),
                            label: const Text('Thử lại'),
                          ),
                        ],
                      ),
                    ),
                  );
                }
                final detail = snapshot.data;
                if (detail == null || detail.sections.isEmpty) {
                  return _buildEmptyState(context);
                }
                return _buildStructuredView(context, detail);
              },
            ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildUnitBanner(context, widget.lesson.sectionTitle),
        const SizedBox(height: 16),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              children: [
                Icon(Icons.info_outline, size: 48, color: Colors.grey.shade400),
                const SizedBox(height: 12),
                const Text(
                  'Nội dung đã được xác minh từ sách giáo khoa.',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 15),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildUnitBanner(BuildContext context, String currentSectionTitle) {
    return Card(
      color: Theme.of(context).colorScheme.primaryContainer.withValues(alpha: 0.3),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: Theme.of(context).colorScheme.outlineVariant),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Icon(Icons.menu_book, color: Theme.of(context).colorScheme.primary),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        widget.lesson.title.toLowerCase().contains('review')
                            ? widget.lesson.title
                            : 'Unit ${widget.lesson.unitNumber}: ${widget.lesson.title}',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                      ),
                      Text(
                        currentSectionTitle.isNotEmpty ? currentSectionTitle : 'Sách Giáo Khoa Tiếng Anh 7',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                              color: Colors.grey.shade700,
                            ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.green.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.green.shade300),
              ),
              child: const Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.verified, size: 16, color: Colors.green),
                  SizedBox(width: 6),
                  Text(
                    'Nguồn: SGK Tiếng Anh 7',
                    style: TextStyle(
                      fontSize: 12,
                      color: Colors.green,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStructuredView(BuildContext context, LessonDetail detail) {
    final sections = detail.sections;
    final displayedSections = _selectedSectionIndex != null &&
            _selectedSectionIndex! < sections.length
        ? [sections[_selectedSectionIndex!]]
        : sections;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _buildUnitBanner(
          context,
          _selectedSectionIndex != null && _selectedSectionIndex! < sections.length
              ? sections[_selectedSectionIndex!].title
              : widget.lesson.sectionTitle,
        ),
        const SizedBox(height: 14),
        // Section selector chips
        SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: Row(
            children: [
              Padding(
                padding: const EdgeInsets.only(right: 8),
                child: ChoiceChip(
                  label: const Text('Tất cả các mục'),
                  selected: _selectedSectionIndex == null,
                  onSelected: (selected) {
                    if (selected) setState(() => _selectedSectionIndex = null);
                  },
                ),
              ),
              for (var i = 0; i < sections.length; i++)
                Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: ChoiceChip(
                    label: Text(
                      _shortSectionTitle(sections[i].title),
                      style: TextStyle(
                        fontWeight: _selectedSectionIndex == i ? FontWeight.bold : FontWeight.normal,
                      ),
                    ),
                    selected: _selectedSectionIndex == i,
                    onSelected: (selected) {
                      setState(() => _selectedSectionIndex = selected ? i : null);
                    },
                  ),
                ),
            ],
          ),
        ),
        const SizedBox(height: 18),
        for (final section in displayedSections) ...[
          _buildSectionHeader(context, section),
          const SizedBox(height: 10),
          for (final activity in section.activities) ...[
            _buildActivityCard(context, activity),
            const SizedBox(height: 14),
          ],
          const SizedBox(height: 12),
        ],
      ],
    );
  }

  String _shortSectionTitle(String title) {
    if (title.contains(' - ')) {
      return title.split(' - ').first;
    }
    return title;
  }

  Widget _buildSectionHeader(BuildContext context, LessonSection section) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerHighest,
        borderRadius: BorderRadius.circular(10),
        border: Border(
          left: BorderSide(color: Theme.of(context).colorScheme.primary, width: 4),
        ),
      ),
      child: Row(
        children: [
          Icon(Icons.folder_open_rounded, size: 20, color: Theme.of(context).colorScheme.primary),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              section.title,
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
            ),
          ),
        ],
      ),
    );
  }

  bool _isExerciseActivity(LessonActivity activity) {
    if (activity.activityType.contains('exercise') ||
        activity.activityType.contains('comprehension') ||
        activity.activityType.contains('quiz')) {
      return true;
    }
    final fullText = activity.fragments.map((f) => f.text).join('\n');
    return RegExp(r'^\s*\d+\.\s*.+?\s*->\s*.+?', multiLine: true).hasMatch(fullText);
  }

  int? _extractTrackNumber(LessonActivity activity) {
    final match = RegExp(r'Track\s*(\d+)', caseSensitive: false).firstMatch(activity.instruction ?? '');
    if (match != null) {
      return int.tryParse(match.group(1)!);
    }
    final lowerInst = (activity.instruction ?? '').toLowerCase();
    if (lowerInst.contains('listen and read')) return 2;
    if (lowerInst.contains('listen, check') || lowerInst.contains('listen and check')) return 3;
    if (lowerInst.contains('listen and repeat')) return 4;
    return null;
  }

  Widget _buildActivityCard(BuildContext context, LessonActivity activity) {
    final isDialogue = activity.activityType.contains('dialogue');
    final isGrammar = activity.activityType.contains('grammar');
    final isExercise = _isExerciseActivity(activity);
    final isVocabulary = activity.activityType.contains('vocabulary') && !isExercise;
    final isSpeaking = activity.activityType.contains('speaking');
    final isPronunciation = activity.activityType.contains('pronunciation');

    final badgeColor = isDialogue
        ? Colors.blue.shade700
        : isGrammar
            ? Colors.deepPurple
            : isVocabulary
                ? Colors.teal.shade700
                : isSpeaking
                    ? Colors.deepOrange.shade700
                    : isPronunciation
                        ? Colors.pink.shade700
                        : isExercise
                            ? Colors.orange.shade800
                            : Colors.indigo;

    final firstFrag = activity.fragments.isNotEmpty ? activity.fragments.first : null;
    final pageNum = firstFrag?.printedPage ?? firstFrag?.pdfPage;
    final detectedTrack = _extractTrackNumber(activity);

    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Activity Title Bar
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: badgeColor,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    activity.number != null ? 'HĐ ${activity.number}' : 'Hoạt động',
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    activity.instruction ?? 'Nội dung',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                      color: Colors.grey.shade900,
                    ),
                  ),
                ),
                if (pageNum != null)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade100,
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: Colors.grey.shade300),
                    ),
                    child: Text(
                      'Trang $pageNum',
                      style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
                    ),
                  ),
              ],
            ),
            const Divider(height: 20),

            // Authentic Audio Player for Listening Activities
            if (activity.audioTracks.isNotEmpty)
              for (final track in activity.audioTracks)
                LessonAudioPlayerWidget(
                  key: Key('audio-track-${track.trackNumber}'),
                  trackNumber: track.trackNumber,
                  title: 'Track ${track.trackNumber}: ${activity.instruction ?? 'Nghe bài học'}',
                  audioUrl: track.audioUrl,
                )
            else if (detectedTrack != null)
              LessonAudioPlayerWidget(
                key: Key('audio-track-$detectedTrack'),
                trackNumber: detectedTrack,
                title: 'Track $detectedTrack: ${activity.instruction ?? 'Nghe bài học'}',
                audioUrl: '/api/v1/media/audio/$detectedTrack',
              ),

            // Activity Content
            if (isDialogue)
              _buildDialogueContent(activity.fragments)
            else if (isGrammar)
              _buildGrammarContent(activity.fragments)
            else if (isVocabulary)
              _buildVocabularyContent(activity.fragments)
            else if (isSpeaking)
              _buildSpeakingContent(activity.fragments)
            else if (isPronunciation)
              _buildPronunciationContent(activity.fragments)
            else if (isExercise)
              _InteractiveExerciseWidget(activity: activity)
            else
              _buildGeneralContent(activity.fragments),
            const SizedBox(height: 12),
            // Verification tag
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                const Icon(Icons.check_circle_outline, size: 14, color: Colors.green),
                const SizedBox(width: 4),
                Text(
                  'Chuẩn nội dung SGK Tiếng Anh 7',
                  style: TextStyle(
                    fontSize: 11,
                    color: Colors.green.shade700,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDialogueContent(List<LessonFragment> fragments) {
    final fullText = fragments.map((f) => f.text).join('\n');
    final lines = fullText.split('\n');

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(
            color: Colors.blue.shade50,
            borderRadius: BorderRadius.circular(6),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.headphones_rounded, size: 16, color: Colors.blue.shade800),
              const SizedBox(width: 6),
              Text(
                'Đoạn hội thoại (Dialogue)',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color: Colors.blue.shade800,
                ),
              ),
            ],
          ),
        ),
        for (final line in lines)
          if (line.trim().isNotEmpty) _buildDialogueLine(line),
      ],
    );
  }

  Widget _buildDialogueLine(String rawLine) {
    final colonIndex = rawLine.indexOf(':');
    if (colonIndex == -1) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 4),
        child: Text(
          rawLine,
          style: const TextStyle(fontSize: 14, fontStyle: FontStyle.italic),
        ),
      );
    }

    final speaker = rawLine.substring(0, colonIndex).trim();
    final speech = rawLine.substring(colonIndex + 1).trim();

    final isPrimary = speaker.toLowerCase().contains('ann') || speaker.toLowerCase().contains('mi');
    final avatarColor = isPrimary ? Colors.indigo.shade600 : Colors.deepOrange.shade600;
    final bubbleColor = isPrimary ? Colors.indigo.shade50 : Colors.deepOrange.shade50;

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          CircleAvatar(
            radius: 15,
            backgroundColor: avatarColor,
            child: Text(
              speaker.isNotEmpty ? speaker[0].toUpperCase() : '?',
              style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: bubbleColor,
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: isPrimary ? Colors.indigo.shade200 : Colors.deepOrange.shade200,
                  width: 0.8,
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    speaker,
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                      color: avatarColor,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    speech,
                    style: const TextStyle(
                      fontSize: 14,
                      height: 1.4,
                      color: Colors.black87,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGrammarContent(List<LessonFragment> fragments) {
    final fullText = fragments.map((f) => f.text).join('\n\n');
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.deepPurple.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.deepPurple.shade200),
      ),
      child: Text(
        fullText,
        style: const TextStyle(
          fontSize: 14,
          height: 1.5,
          fontFamily: 'monospace',
          color: Colors.black87,
        ),
      ),
    );
  }

  Widget _buildVocabularyContent(List<LessonFragment> fragments) {
    final fullText = fragments.map((f) => f.text).join('\n\n');
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.teal.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.teal.shade200),
      ),
      child: Text(
        fullText,
        style: const TextStyle(
          fontSize: 14,
          height: 1.6,
          color: Colors.black87,
        ),
      ),
    );
  }

  Widget _buildGeneralContent(List<LessonFragment> fragments) {
    final fullText = fragments.map((f) => f.text).join('\n\n');
    final lines = fullText.split('\n');
    final List<Widget> widgets = [];
    final textBuffer = StringBuffer();

    void flushText() {
      if (textBuffer.isNotEmpty) {
        final content = textBuffer.toString().trim();
        if (content.isNotEmpty) {
          widgets.add(
            Text(
              content,
              style: const TextStyle(
                fontSize: 15,
                height: 1.6,
                color: Colors.black87,
              ),
            ),
          );
        }
        textBuffer.clear();
      }
    }

    for (final rawLine in lines) {
      final line = rawLine.trim();
      final mdImgMatch = RegExp(r'^!\[(.*?)\]\((.*?)\)$').firstMatch(line);
      final tagImgMatch = RegExp(r'^\[(?:image|img):\s*(.+?)\]$', caseSensitive: false).firstMatch(line);
      if (mdImgMatch != null || tagImgMatch != null) {
        flushText();
        final alt = mdImgMatch?.group(1)?.trim() ?? '';
        final url = mdImgMatch?.group(2)?.trim() ?? tagImgMatch!.group(1)!.trim();
        widgets.add(
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.grey.shade300),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (alt.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.only(left: 12, top: 8, bottom: 4),
                        child: Text(
                          alt,
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: Colors.grey.shade700,
                          ),
                        ),
                      ),
                    Image.network(
                      _resolveMediaUrl(url),
                      fit: BoxFit.contain,
                      errorBuilder: (context, error, stackTrace) => const SizedBox.shrink(),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
      } else {
        textBuffer.writeln(rawLine);
      }
    }
    flushText();

    if (widgets.isEmpty) {
      return const SizedBox.shrink();
    }
    if (widgets.length == 1) {
      return widgets.first;
    }
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: widgets,
    );
  }

  Widget _buildPronunciationContent(List<LessonFragment> fragments) {
    final fullText = fragments.map((f) => f.text).join('\n\n');
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildPronunciationTable(fullText),
        const SizedBox(height: 14),
        _buildPronunciationGuideBox(),
      ],
    );
  }

  Widget _buildPronunciationTable(String text) {
    List<String> headers = ['/ə/', '/ɜː/'];
    List<List<String>> rows = [
      ['**a**mazing', 'l**ear**n'],
      ['yog**a**', 's**ur**f'],
      ['c**o**llect', 'w**or**k'],
      ['col**u**mn', 'th**ir**teen'],
    ];

    // Markdown table parsing if present
    final lines = text.split('\n');
    final parsedRows = <List<String>>[];
    for (final rawLine in lines) {
      final line = rawLine.trim();
      if (!line.startsWith('|') || !line.endsWith('|')) continue;
      if (RegExp(r'^\|[\s\-:|]+\|$').hasMatch(line)) continue;
      final cells = line
          .substring(1, line.length - 1)
          .split('|')
          .map((c) => c.trim())
          .toList();
      if (cells.length >= 2) {
        parsedRows.add(cells);
      }
    }
    if (parsedRows.length >= 2) {
      headers = parsedRows[0];
      rows = parsedRows.sublist(1);
    }

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.pink.shade300, width: 1.5),
        boxShadow: [
          BoxShadow(
            color: Colors.pink.shade50.withOpacity(0.5),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      clipBehavior: Clip.antiAlias,
      child: Table(
        border: TableBorder(
          horizontalInside: BorderSide(color: Colors.pink.shade100, width: 1),
          verticalInside: BorderSide(color: Colors.pink.shade300, width: 1.5),
        ),
        columnWidths: const {
          0: FlexColumnWidth(1),
          1: FlexColumnWidth(1),
        },
        children: [
          TableRow(
            decoration: BoxDecoration(color: Colors.pink.shade100),
            children: [
              for (final h in headers)
                Container(
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  alignment: Alignment.center,
                  child: Text(
                    h,
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: Colors.pink.shade900,
                    ),
                  ),
                ),
            ],
          ),
          for (final row in rows)
            TableRow(
              decoration: const BoxDecoration(color: Colors.white),
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  alignment: Alignment.center,
                  child: _buildHighlightedWord(row[0]),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(vertical: 10),
                  alignment: Alignment.center,
                  child: _buildHighlightedWord(row.length > 1 ? row[1] : ''),
                ),
              ],
            ),
        ],
      ),
    );
  }

  Widget _buildHighlightedWord(String text) {
    if (!text.contains('**')) {
      return Text(
        text,
        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500, color: Colors.black87),
      );
    }
    final spans = <TextSpan>[];
    final regex = RegExp(r'\*\*(.*?)\*\*');
    int lastEnd = 0;
    for (final match in regex.allMatches(text)) {
      if (match.start > lastEnd) {
        spans.add(TextSpan(
          text: text.substring(lastEnd, match.start),
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500, color: Colors.black87),
        ));
      }
      spans.add(TextSpan(
        text: match.group(1),
        style: TextStyle(
          fontSize: 16,
          fontWeight: FontWeight.bold,
          color: Colors.deepOrange.shade800,
        ),
      ));
      lastEnd = match.end;
    }
    if (lastEnd < text.length) {
      spans.add(TextSpan(
        text: text.substring(lastEnd),
        style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500, color: Colors.black87),
      ));
    }
    return RichText(text: TextSpan(children: spans));
  }

  Widget _buildPronunciationGuideBox() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.pink.shade50.withOpacity(0.5),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: Colors.pink.shade200),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.lightbulb, size: 16, color: Colors.pink.shade800),
              const SizedBox(width: 6),
              Text(
                'Hướng dẫn nhận biết âm (Pronunciation Tips):',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 13,
                  color: Colors.pink.shade900,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            '• Âm /ə/: Là nguyên âm ngắn (schwa), thả lỏng cơ miệng khi đọc (amazing, yoga, collect, column).\n'
            '• Âm /ɜː/: Là nguyên âm dài, hơi mở miệng và hơi cong lưỡi (learn, surf, work, thirteen).',
            style: TextStyle(
              fontSize: 12.5,
              height: 1.5,
              color: Colors.pink.shade900,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSpeakingContent(List<LessonFragment> fragments) {
    final fullText = fragments.map((f) => f.text).join('\n\n');
    final lines = fullText.split('\n');

    final List<Widget> widgets = [];

    // Header badge
    final hasImages = fullText.contains('![') || fullText.toLowerCase().contains('[image:');
    final isGame = fullText.toLowerCase().contains('game') || fullText.toLowerCase().contains('trò chơi');
    final headerTitle = isGame
        ? 'Trò chơi / Hoạt động (Game & Activity) - Thực hành theo nhóm'
        : hasImages
            ? 'Luyện nói (Speaking Practice) - Quan sát hình và tự nói theo mẫu'
            : 'Luyện nói (Speaking Practice) - Thực hành theo cặp / nhóm';
    final headerIcon = isGame ? Icons.sports_esports_outlined : Icons.record_voice_over_rounded;

    widgets.add(
      Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: Colors.orange.shade50,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: Colors.orange.shade200),
        ),
        child: Row(
          children: [
            Icon(headerIcon, size: 18, color: Colors.orange.shade900),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                headerTitle,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.bold,
                  color: Colors.orange.shade900,
                ),
              ),
            ),
          ],
        ),
      ),
    );

    int i = 0;
    while (i < lines.length) {
      final rawLine = lines[i];
      final line = rawLine.trim();
      if (line.isEmpty) {
        i++;
        continue;
      }

      // Check for markdown image: ![alt](url) or [image:url]
      final mdImgMatch = RegExp(r'^!\[(.*?)\]\((.*?)\)$').firstMatch(line);
      final tagImgMatch = RegExp(r'^\[(?:image|img):\s*(.+?)\]$', caseSensitive: false).firstMatch(line);
      if (mdImgMatch != null || tagImgMatch != null) {
        final alt = mdImgMatch?.group(1)?.trim() ?? '';
        final url = mdImgMatch?.group(2)?.trim() ?? tagImgMatch!.group(1)!.trim();
        widgets.add(
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.grey.shade300),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    if (alt.isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.only(left: 12, top: 8, bottom: 4),
                        child: Text(
                          alt,
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: Colors.grey.shade700,
                          ),
                        ),
                      ),
                    Image.network(
                      _resolveMediaUrl(url),
                      fit: BoxFit.contain,
                      errorBuilder: (context, error, stackTrace) => const SizedBox.shrink(),
                    ),
                  ],
                ),
              ),
            ),
          ),
        );
        i++;
        continue;
      }

      // Check for Example block
      if (line.toLowerCase().startsWith('example:') || line.toLowerCase().startsWith('câu mẫu:')) {
        final exampleLines = <String>[line];
        i++;
        while (i < lines.length &&
            lines[i].trim().isNotEmpty &&
            !lines[i].trim().startsWith('![') &&
            !lines[i].trim().toLowerCase().startsWith('gợi ý')) {
          exampleLines.add(lines[i].trim());
          i++;
        }
        widgets.add(
          Container(
            width: double.infinity,
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.blue.shade50,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.blue.shade200),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.chat_bubble_outline_rounded, size: 20, color: Colors.blue.shade800),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    exampleLines.join('\n'),
                    style: TextStyle(
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      color: Colors.blue.shade900,
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
        continue;
      }

      // Check for Speaking Hints or Instructions block
      if (line.toLowerCase().startsWith('gợi ý') ||
          line.toLowerCase().startsWith('speaking hints') ||
          line.toLowerCase().startsWith('hướng dẫn:') ||
          line.toLowerCase().startsWith('luật chơi:')) {
        final hintLines = <String>[line];
        i++;
        while (i < lines.length &&
            lines[i].trim().isNotEmpty &&
            !lines[i].trim().startsWith('![') &&
            !lines[i].trim().toLowerCase().startsWith('example:') &&
            !lines[i].trim().toLowerCase().startsWith('câu mẫu:') &&
            !lines[i].trim().toLowerCase().startsWith('ví dụ')) {
          hintLines.add(lines[i].trim());
          i++;
        }
        widgets.add(
          Container(
            width: double.infinity,
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.amber.shade50,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.amber.shade200),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.lightbulb_outline_rounded, size: 18, color: Colors.amber.shade900),
                    const SizedBox(width: 6),
                    Text(
                      hintLines.first,
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.bold,
                        color: Colors.amber.shade900,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                for (final hl in hintLines.sublist(1))
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 2),
                    child: Text(
                      hl,
                      style: const TextStyle(
                        fontSize: 13,
                        color: Colors.black87,
                        height: 1.4,
                      ),
                    ),
                  ),
              ],
            ),
          ),
        );
        continue;
      }

      // General text line
      widgets.add(
        Padding(
          padding: const EdgeInsets.only(bottom: 6),
          child: Text(
            line,
            style: const TextStyle(fontSize: 14, height: 1.5, color: Colors.black87),
          ),
        ),
      );
      i++;
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: widgets,
    );
  }
}

String _resolveMediaUrl(String url) {
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url;
  }
  const defaultBase = String.fromEnvironment('API_BASE_URL', defaultValue: 'http://10.0.2.2:8000');
  final base = defaultBase.replaceAll(RegExp(r'/+$'), '');
  var path = url.startsWith('/') ? url : '/$url';
  if (path.startsWith('/images/')) {
    path = '/api/v1/media$path';
  }
  return '$base$path';
}

class _InteractiveExerciseWidget extends StatefulWidget {
  final LessonActivity activity;
  const _InteractiveExerciseWidget({required this.activity});

  @override
  State<_InteractiveExerciseWidget> createState() => _InteractiveExerciseWidgetState();
}

class _ParsedExerciseItem {
  final int number;
  final String prompt;
  final String? imageUrl;
  final String correctAnswer;
  final String? explanation;
  final bool isTrueFalse;
  final List<String>? options;

  _ParsedExerciseItem({
    required this.number,
    required this.prompt,
    this.imageUrl,
    required this.correctAnswer,
    this.explanation,
    required this.isTrueFalse,
    this.options,
  });
}

class _InteractiveExerciseWidgetState extends State<_InteractiveExerciseWidget> {
  final Map<int, String> _userAnswers = {};
  final Map<int, TextEditingController> _controllers = {};
  List<String> _wordBank = [];
  List<String> _options = [];
  List<_ParsedExerciseItem> _items = [];
  List<String> _contextLines = [];
  String? _headerImageUrl;

  @override
  void initState() {
    super.initState();
    _parseContent();
  }

  @override
  void didUpdateWidget(covariant _InteractiveExerciseWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.activity != widget.activity) {
      _parseContent();
    }
  }

  @override
  void dispose() {
    for (final c in _controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  void _parseContent() {
    final fullText = widget.activity.fragments.map((f) => f.text).join('\n');
    final lines = fullText.split('\n');
    _wordBank = [];
    _options = [];
    _items = [];
    _contextLines = [];
    _headerImageUrl = null;

    for (int i = 0; i < lines.length; i++) {
      final rawLine = lines[i];
      final line = rawLine.trim();
      if (line.isEmpty) {
        if (_items.isEmpty && _contextLines.isNotEmpty && _contextLines.last.isNotEmpty) {
          _contextLines.add('');
        }
        continue;
      }

      final headerImgMatch = RegExp(r'^!\[(.*?)\]\((.*?)\)$').firstMatch(line);
      if (headerImgMatch != null) {
        _headerImageUrl = headerImgMatch.group(2)?.trim();
        continue;
      }
      final headerTagMatch = RegExp(r'^\[(?:image|img):\s*(.+?)\]$', caseSensitive: false).firstMatch(line);
      if (headerTagMatch != null) {
        _headerImageUrl = headerTagMatch.group(1)?.trim();
        continue;
      }

      final lower = line.toLowerCase();
      if (lower.startsWith('options:') ||
          lower.startsWith('choices:') ||
          lower.startsWith('lựa chọn:') ||
          lower.startsWith('âm lựa chọn:')) {
        var optsPart = line.contains(':') ? line.split(':').sublist(1).join(':').trim() : '';
        optsPart = optsPart.replaceAll('[', '').replaceAll(']', '').trim();
        final parsedOpts = optsPart
            .split(RegExp(r'[,|]'))
            .map((w) => w.trim())
            .where((w) => w.isNotEmpty)
            .toList();
        _options = parsedOpts;
        if (_items.isNotEmpty) {
          final last = _items.removeLast();
          _items.add(_ParsedExerciseItem(
            number: last.number,
            prompt: last.prompt,
            imageUrl: last.imageUrl,
            correctAnswer: last.correctAnswer,
            explanation: last.explanation,
            isTrueFalse: last.isTrueFalse,
            options: parsedOpts,
          ));
        }
        continue;
      }

      if (lower.startsWith('word box:') ||
          lower.startsWith('word bank:') ||
          lower.startsWith('từ gợi ý:') ||
          lower.startsWith('từ vựng:') ||
          lower == 'word box' ||
          lower == 'word bank') {
        var wordsPart = line.contains(':') ? line.split(':').sublist(1).join(':').trim() : '';
        if (wordsPart.isEmpty && i + 1 < lines.length) {
          final nextLine = lines[i + 1].trim();
          if (!RegExp(r'^\d+\.').hasMatch(nextLine)) {
            wordsPart = nextLine;
            i++;
          }
        }
        if (wordsPart.contains('[') && wordsPart.contains(']')) {
          _wordBank = RegExp(r'\[(.*?)\]')
              .allMatches(wordsPart)
              .map((m) => m.group(1)!.trim())
              .where((w) => w.isNotEmpty)
              .toList();
        } else {
          _wordBank = wordsPart
              .split(',')
              .map((w) => w.trim())
              .where((w) => w.isNotEmpty)
              .toList();
        }
        continue;
      }

      final match = RegExp(r'^(\d+)\.\s*(.*?)\s*->\s*(.+?)(?:\s*\((.+)\))?$').firstMatch(line);
      if (match != null) {
        final num = int.tryParse(match.group(1)!) ?? (_items.length + 1);
        var prompt = match.group(2)!.trim();
        final answer = match.group(3)!.trim();
        final explanation = match.group(4)?.trim();

        String? imageUrl;
        final mdImgMatch = RegExp(r'!\[(.*?)\]\((.*?)\)').firstMatch(prompt);
        if (mdImgMatch != null) {
          imageUrl = mdImgMatch.group(2)?.trim();
          prompt = prompt.replaceAll(mdImgMatch.group(0)!, '').trim();
          if (prompt.isEmpty && mdImgMatch.group(1) != null && mdImgMatch.group(1)!.isNotEmpty) {
            prompt = mdImgMatch.group(1)!.trim();
          }
        } else {
          final tagMatch = RegExp(r'\[(?:image|img):\s*(.+?)\]', caseSensitive: false).firstMatch(prompt);
          if (tagMatch != null) {
            imageUrl = tagMatch.group(1)?.trim();
            prompt = prompt.replaceAll(tagMatch.group(0)!, '').trim();
          }
        }

        final lowerAns = answer.toLowerCase();
        final isTf = lowerAns == 'true' || lowerAns == 'false' || lowerAns == 't' || lowerAns == 'f';

        _items.add(_ParsedExerciseItem(
          number: num,
          prompt: prompt,
          imageUrl: imageUrl,
          correctAnswer: answer,
          explanation: explanation,
          isTrueFalse: isTf,
        ));
      } else {
        if (_items.isEmpty) {
          _contextLines.add(line);
        } else if (line.isNotEmpty) {
          final last = _items.removeLast();
          _items.add(_ParsedExerciseItem(
            number: last.number,
            prompt: '${last.prompt}\n$line',
            imageUrl: last.imageUrl,
            correctAnswer: last.correctAnswer,
            explanation: last.explanation,
            isTrueFalse: last.isTrueFalse,
          ));
        }
      }
    }
  }

  bool _isTfMatch(String selected, String correct) {
    final s = selected.toLowerCase().trim();
    final c = correct.toLowerCase().trim();
    if (s == 't' || s == 'true') {
      return c == 't' || c == 'true';
    }
    if (s == 'f' || s == 'false') {
      return c == 'f' || c == 'false';
    }
    return s == c;
  }

  String _normalizeSound(String s) {
    return s
        .trim()
        .toLowerCase()
        .replaceAll('/', '')
        .replaceAll('ː', ':')
        .replaceAll('3', 'ɜ')
        .replaceAll(RegExp(r'[.\s]+$'), '');
  }

  bool _isOptionMatch(String selected, String correct) {
    final s = selected.toLowerCase().trim();
    final c = correct.toLowerCase().trim();
    if (s == c) return true;
    if (_normalizeSound(s) == _normalizeSound(c)) return true;

    final optLetterMatch = RegExp(r'^([a-d])[\.\)]\s*(.*)$', caseSensitive: false).firstMatch(s);
    final corrLetterMatch = RegExp(r'^([a-d])[\.\)]\s*(.*)$', caseSensitive: false).firstMatch(c);
    if (optLetterMatch != null && corrLetterMatch != null) {
      if (optLetterMatch.group(1)!.toLowerCase() == corrLetterMatch.group(1)!.toLowerCase()) return true;
    }
    if (optLetterMatch != null) {
      final letter = optLetterMatch.group(1)!.toLowerCase();
      final text = optLetterMatch.group(2)!.toLowerCase().trim();
      if (letter == c || text == c || _normalizeSound(text) == _normalizeSound(c)) return true;
    }
    if (corrLetterMatch != null) {
      final letter = corrLetterMatch.group(1)!.toLowerCase();
      final text = corrLetterMatch.group(2)!.toLowerCase().trim();
      if (letter == s || text == s || _normalizeSound(text) == _normalizeSound(s)) return true;
    }
    return false;
  }

  bool _isCorrect(_ParsedExerciseItem item, String userAnswer) {
    if (item.isTrueFalse) {
      return _isTfMatch(userAnswer, item.correctAnswer);
    }
    final opts = item.options ?? _options;
    if (opts.isNotEmpty) {
      return _isOptionMatch(userAnswer, item.correctAnswer);
    }

    String norm(String s) => s
        .toLowerCase()
        .replaceAll('’', "'")
        .replaceAll('`', "'")
        .replaceAll(RegExp(r'[\s\-–—,._]+'), ' ')
        .trim();

    final normUser = norm(userAnswer);
    if (normUser.isEmpty) return false;
    if (item.correctAnswer.contains('*')) return true;

    final cleanUser = userAnswer.trim().toLowerCase().replaceAll(RegExp(r'[.\s]+$'), '');
    final cleanCorrect = item.correctAnswer.trim().toLowerCase().replaceAll(RegExp(r'[.\s]+$'), '');
    if (cleanUser == cleanCorrect || norm(cleanCorrect) == normUser) return true;
    if (_isOptionMatch(cleanUser, cleanCorrect)) return true;

    final options = item.correctAnswer
        .split(RegExp(r'[/|]'))
        .map((e) => e.trim())
        .where((e) => e.isNotEmpty);

    for (final opt in options) {
      final cleanOpt = opt.toLowerCase().replaceAll(RegExp(r'[.\s]+$'), '');
      if (cleanUser == cleanOpt || norm(opt) == normUser) return true;
    }
    return false;
  }

  void _reset() {
    setState(() {
      _userAnswers.clear();
      for (final c in _controllers.values) {
        c.clear();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_items.isEmpty) {
      final fullText = widget.activity.fragments.map((f) => f.text).join('\n\n');
      return Text(fullText, style: const TextStyle(fontSize: 15, height: 1.6));
    }

    final answeredCount = _userAnswers.length;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (_headerImageUrl != null && _headerImageUrl!.isNotEmpty) ...[
          Container(
            width: double.infinity,
            margin: const EdgeInsets.only(bottom: 16),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(10),
              child: Container(
                constraints: const BoxConstraints(maxHeight: 280),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.grey.shade300),
                ),
                child: Image.network(
                  _resolveImageUrl(_headerImageUrl!),
                  fit: BoxFit.contain,
                  errorBuilder: (context, error, stackTrace) => const SizedBox.shrink(),
                ),
              ),
            ),
          ),
        ],
        if (_contextLines.isNotEmpty) ...[
          _buildContextSection(context, _contextLines),
          const SizedBox(height: 16),
        ],
        if (_wordBank.isNotEmpty) ...[
          Container(
            width: double.infinity,
            margin: const EdgeInsets.only(bottom: 16),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.amber.shade50,
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: Colors.amber.shade300),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.lightbulb_outline, size: 18, color: Colors.amber.shade900),
                    const SizedBox(width: 6),
                    Text(
                      'Từ gợi ý trong khung (Word Bank):',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 13,
                        color: Colors.amber.shade900,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Wrap(
                  spacing: 8,
                  runSpacing: 6,
                  children: [
                    for (final word in _wordBank)
                      Chip(
                        label: Text(
                          word,
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: Colors.amber.shade900,
                          ),
                        ),
                        backgroundColor: Colors.white,
                        side: BorderSide(color: Colors.amber.shade400),
                      ),
                  ],
                ),
              ],
            ),
          ),
        ],
        for (var i = 0; i < _items.length; i++) ...[
          _buildQuestionItem(context, i, _items[i]),
          if (i < _items.length - 1) const SizedBox(height: 14),
        ],
        const SizedBox(height: 16),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              'Đã làm: $answeredCount/${_items.length} câu',
              style: TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 13,
                color: answeredCount == _items.length ? Colors.green.shade800 : Colors.grey.shade700,
              ),
            ),
            if (answeredCount > 0)
              OutlinedButton.icon(
                onPressed: _reset,
                icon: const Icon(Icons.refresh, size: 16),
                label: const Text('Làm lại', style: TextStyle(fontSize: 12)),
              ),
          ],
        ),
      ],
    );
  }

  String _resolveImageUrl(String url) {
    return _resolveMediaUrl(url);
  }

  Widget _buildQuestionItem(BuildContext context, int index, _ParsedExerciseItem item) {
    final userAnswer = _userAnswers[index];
    final hasAnswered = userAnswer != null && userAnswer.isNotEmpty;

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: hasAnswered
              ? (_isCorrect(item, userAnswer) ? Colors.green.shade400 : Colors.red.shade300)
              : Theme.of(context).colorScheme.outlineVariant,
          width: hasAnswered ? 1.5 : 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              CircleAvatar(
                radius: 12,
                backgroundColor: hasAnswered
                    ? (_isCorrect(item, userAnswer) ? Colors.green : Colors.red)
                    : Theme.of(context).colorScheme.primaryContainer,
                child: Text(
                  '${item.number}',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                    color: hasAnswered
                        ? Colors.white
                        : Theme.of(context).colorScheme.onPrimaryContainer,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              if (item.prompt.isNotEmpty)
                Expanded(
                  child: _buildPromptWidget(item.prompt),
                )
              else if (item.imageUrl != null)
                Expanded(
                  child: Text(
                    'Hình ${item.number}',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: Colors.grey.shade700,
                    ),
                  ),
                )
              else
                Expanded(
                  child: Text(
                    'Câu ${item.number}',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w600,
                      color: Colors.grey.shade700,
                    ),
                  ),
                ),
            ],
          ),
          if (item.imageUrl != null && item.imageUrl!.isNotEmpty) ...[
            const SizedBox(height: 10),
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Container(
                width: double.infinity,
                constraints: const BoxConstraints(maxHeight: 200),
                decoration: BoxDecoration(
                  color: Colors.grey.shade100,
                  border: Border.all(color: Colors.grey.shade300),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Image.network(
                  _resolveImageUrl(item.imageUrl!),
                  fit: BoxFit.contain,
                  loadingBuilder: (context, child, loadingProgress) {
                    if (loadingProgress == null) return child;
                    return Container(
                      height: 120,
                      alignment: Alignment.center,
                      child: const SizedBox(
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      ),
                    );
                  },
                  errorBuilder: (context, error, stackTrace) {
                    return Container(
                      height: 80,
                      alignment: Alignment.center,
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.image_outlined, color: Colors.grey.shade500),
                          const SizedBox(width: 8),
                          Text('Ảnh SGK Unit 1 - Hình ${item.number}',
                              style: TextStyle(color: Colors.grey.shade600, fontSize: 12)),
                        ],
                      ),
                    );
                  },
                ),
              ),
            ),
          ],
          const SizedBox(height: 10),
          if (item.isTrueFalse)
            _buildTrueFalseButtons(index, item, userAnswer)
          else if (item.options != null && item.options!.isNotEmpty)
            _buildChoiceButtons(index, item, item.options!, userAnswer)
          else if (_options.isNotEmpty)
            _buildChoiceButtons(index, item, _options, userAnswer)
          else
            _buildInputRow(index, item, userAnswer),
          if (hasAnswered) ...[
            const SizedBox(height: 10),
            _buildExplanationBox(context, item, userAnswer),
          ],
        ],
      ),
    );
  }

  Widget _buildPromptWidget(String prompt) {
    if (!prompt.contains('<u>')) {
      return Text(
        prompt,
        style: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w600,
          height: 1.4,
        ),
      );
    }
    final spans = <TextSpan>[];
    final regex = RegExp(r'<u>(.*?)</u>');
    int lastEnd = 0;
    for (final match in regex.allMatches(prompt)) {
      if (match.start > lastEnd) {
        spans.add(TextSpan(text: prompt.substring(lastEnd, match.start)));
      }
      spans.add(TextSpan(
        text: match.group(1),
        style: TextStyle(
          decoration: TextDecoration.underline,
          decorationColor: Colors.deepOrange.shade800,
          decorationThickness: 2,
          fontWeight: FontWeight.bold,
          color: Colors.deepOrange.shade800,
        ),
      ));
      lastEnd = match.end;
    }
    if (lastEnd < prompt.length) {
      spans.add(TextSpan(text: prompt.substring(lastEnd)));
    }
    return RichText(
      text: TextSpan(
        style: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w600,
          height: 1.4,
          color: Colors.black87,
        ),
        children: spans,
      ),
    );
  }

  Widget _buildChoiceButtons(int index, _ParsedExerciseItem item, List<String> options, String? userAnswer) {
    final hasAnswered = userAnswer != null && userAnswer.isNotEmpty;
    final bool useVertical = options.any((o) => o.length > 8) || options.length > 3;

    if (useVertical) {
      return Column(
        children: [
          for (int optIdx = 0; optIdx < options.length; optIdx++) ...[
            if (optIdx > 0) const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: _buildChoiceButton(index, item, options[optIdx], userAnswer, hasAnswered),
            ),
          ],
        ],
      );
    }

    return Row(
      children: [
        for (int optIdx = 0; optIdx < options.length; optIdx++) ...[
          if (optIdx > 0) const SizedBox(width: 12),
          Expanded(
            child: _buildChoiceButton(index, item, options[optIdx], userAnswer, hasAnswered),
          ),
        ],
      ],
    );
  }

  Widget _buildChoiceButton(int index, _ParsedExerciseItem item, String option, String? userAnswer, bool hasAnswered) {
    final isSelected = userAnswer != null && _isOptionMatch(userAnswer, option);
    final isCorrectOption = _isOptionMatch(option, item.correctAnswer);

    Color? bgColor;
    Color borderColor = Colors.grey.shade400;
    Color textColor = Colors.black87;
    double borderWidth = 1;

    if (isSelected) {
      borderWidth = 2;
      if (isCorrectOption) {
        bgColor = Colors.green.shade100;
        borderColor = Colors.green;
        textColor = Colors.green.shade900;
      } else {
        bgColor = Colors.red.shade100;
        borderColor = Colors.red;
        textColor = Colors.red.shade900;
      }
    } else if (hasAnswered && isCorrectOption) {
      bgColor = Colors.green.shade50;
      borderColor = Colors.green.shade400;
      textColor = Colors.green.shade800;
    }

    return OutlinedButton(
      style: OutlinedButton.styleFrom(
        backgroundColor: bgColor,
        side: BorderSide(color: borderColor, width: borderWidth),
        foregroundColor: textColor,
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
      onPressed: () => setState(() => _userAnswers[index] = option),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (isSelected) ...[
            Icon(
              isCorrectOption ? Icons.check_circle : Icons.cancel,
              size: 18,
              color: isCorrectOption ? Colors.green.shade800 : Colors.red.shade800,
            ),
            const SizedBox(width: 6),
          ] else if (hasAnswered && isCorrectOption) ...[
            Icon(Icons.check, size: 16, color: Colors.green.shade700),
            const SizedBox(width: 4),
          ],
          Flexible(
            child: Text(
              option,
              textAlign: TextAlign.center,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
            ),
          ),
        ],
      ),
    );
  }


  Widget _buildTrueFalseButtons(int index, _ParsedExerciseItem item, String? userAnswer) {
    final hasAnswered = userAnswer != null;
    final isTSelected = userAnswer == 'T';
    final isFSelected = userAnswer == 'F';

    final tCorrect = _isTfMatch('T', item.correctAnswer);
    final fCorrect = _isTfMatch('F', item.correctAnswer);

    return Row(
      children: [
        Expanded(
          child: OutlinedButton(
            style: OutlinedButton.styleFrom(
              backgroundColor: isTSelected
                  ? (tCorrect ? Colors.green.shade100 : Colors.red.shade100)
                  : (hasAnswered && tCorrect ? Colors.green.shade50 : null),
              side: BorderSide(
                color: isTSelected
                    ? (tCorrect ? Colors.green : Colors.red)
                    : (hasAnswered && tCorrect ? Colors.green.shade400 : Colors.grey.shade400),
                width: isTSelected ? 2 : 1,
              ),
              foregroundColor: isTSelected
                  ? (tCorrect ? Colors.green.shade900 : Colors.red.shade900)
                  : Colors.black87,
            ),
            onPressed: () => setState(() => _userAnswers[index] = 'T'),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (isTSelected)
                  Icon(
                    tCorrect ? Icons.check : Icons.close,
                    size: 16,
                    color: tCorrect ? Colors.green.shade800 : Colors.red.shade800,
                  ),
                if (isTSelected) const SizedBox(width: 4),
                const Text('T', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const SizedBox(width: 4),
                const Text('(Đúng)', style: TextStyle(fontSize: 12)),
              ],
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: OutlinedButton(
            style: OutlinedButton.styleFrom(
              backgroundColor: isFSelected
                  ? (fCorrect ? Colors.green.shade100 : Colors.red.shade100)
                  : (hasAnswered && fCorrect ? Colors.green.shade50 : null),
              side: BorderSide(
                color: isFSelected
                    ? (fCorrect ? Colors.green : Colors.red)
                    : (hasAnswered && fCorrect ? Colors.green.shade400 : Colors.grey.shade400),
                width: isFSelected ? 2 : 1,
              ),
              foregroundColor: isFSelected
                  ? (fCorrect ? Colors.green.shade900 : Colors.red.shade900)
                  : Colors.black87,
            ),
            onPressed: () => setState(() => _userAnswers[index] = 'F'),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (isFSelected)
                  Icon(
                    fCorrect ? Icons.check : Icons.close,
                    size: 16,
                    color: fCorrect ? Colors.green.shade800 : Colors.red.shade800,
                  ),
                if (isFSelected) const SizedBox(width: 4),
                const Text('F', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
                const SizedBox(width: 4),
                const Text('(Sai)', style: TextStyle(fontSize: 12)),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildInputRow(int index, _ParsedExerciseItem item, String? userAnswer) {
    if (!_controllers.containsKey(index)) {
      _controllers[index] = TextEditingController(text: userAnswer ?? '');
    }
    final controller = _controllers[index]!;

    return Row(
      children: [
        Expanded(
          child: TextField(
            controller: controller,
            decoration: InputDecoration(
              hintText: 'Nhập câu trả lời...',
              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
              isDense: true,
            ),
            onSubmitted: (val) => setState(() => _userAnswers[index] = val.trim()),
          ),
        ),
        const SizedBox(width: 8),
        FilledButton.tonal(
          onPressed: () => setState(() => _userAnswers[index] = controller.text.trim()),
          child: const Text('Kiểm tra'),
        ),
      ],
    );
  }


  Widget _buildExplanationBox(BuildContext context, _ParsedExerciseItem item, String userAnswer) {
    final correct = _isCorrect(item, userAnswer);

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: correct ? Colors.green.shade50 : Colors.red.shade50,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: correct ? Colors.green.shade300 : Colors.red.shade300,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                correct ? Icons.check_circle : Icons.error_outline,
                size: 16,
                color: correct ? Colors.green.shade700 : Colors.red.shade700,
              ),
              const SizedBox(width: 6),
              Text(
                correct ? 'Chính xác!' : 'Chưa chính xác.',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 13,
                  color: correct ? Colors.green.shade800 : Colors.red.shade800,
                ),
              ),
              if (!correct) ...[
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    'Đáp án đúng: ${item.correctAnswer}',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 13,
                      color: Colors.red.shade900,
                    ),
                  ),
                ),
              ],
            ],
          ),
          if (item.explanation != null && item.explanation!.isNotEmpty) ...[
            const SizedBox(height: 4),
            Text(
              '💡 Giải thích: ${item.explanation}',
              style: TextStyle(
                fontSize: 12,
                height: 1.4,
                color: correct ? Colors.green.shade900 : Colors.red.shade900,
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildContextSection(BuildContext context, List<String> rawLines) {
    final lines = List<String>.from(rawLines);
    while (lines.isNotEmpty && lines.last.trim().isEmpty) {
      lines.removeLast();
    }
    if (lines.isEmpty) return const SizedBox.shrink();

    final widgets = <Widget>[];
    final passageHeaderIdx = lines.indexWhere((l) =>
        l.toLowerCase().contains('đoạn văn') || l.toLowerCase().contains('reading passage'));
    final defHeaderIdx = lines.indexWhere((l) =>
        l.toLowerCase().contains('định nghĩa') ||
        l.toLowerCase().contains('lợi ích') ||
        l.toLowerCase().contains('column b'));

    if (passageHeaderIdx != -1) {
      final passageEnd = defHeaderIdx != -1 && defHeaderIdx > passageHeaderIdx
          ? defHeaderIdx
          : lines.length;
      final passageLines = lines.sublist(passageHeaderIdx, passageEnd);
      final title = passageLines.first;
      final body = passageLines.sublist(1).join('\n').trim();

      widgets.add(
        Container(
          width: double.infinity,
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.blue.shade50.withValues(alpha: 0.5),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: Colors.blue.shade200),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.menu_book_rounded, size: 18, color: Colors.blue.shade800),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      title,
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 13,
                        color: Colors.blue.shade900,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Text(
                body,
                style: TextStyle(
                  fontSize: 13.5,
                  height: 1.6,
                  color: Colors.grey.shade900,
                ),
              ),
            ],
          ),
        ),
      );
    }

    if (defHeaderIdx != -1) {
      final defLines = lines.sublist(defHeaderIdx);
      final title = defLines.first;
      final bodyLines = defLines.sublist(1).where((l) => l.trim().isNotEmpty).toList();

      widgets.add(
        Container(
          width: double.infinity,
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.amber.shade50.withValues(alpha: 0.7),
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: Colors.amber.shade300),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.format_list_bulleted_rounded, size: 18, color: Colors.amber.shade900),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      title,
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 13,
                        color: Colors.amber.shade900,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              for (final bl in bodyLines)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 3),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        bl.contains('.') ? '${bl.split('.').first}. ' : '• ',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 13,
                          color: Colors.amber.shade900,
                        ),
                      ),
                      Expanded(
                        child: Text(
                          bl.contains('.') ? bl.split('.').sublist(1).join('.').trim() : bl,
                          style: TextStyle(
                            fontSize: 13,
                            height: 1.4,
                            color: Colors.grey.shade900,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
        ),
      );
    }

    if (passageHeaderIdx == -1 && defHeaderIdx == -1 && lines.isNotEmpty) {
      widgets.add(
        Container(
          width: double.infinity,
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.grey.shade50,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: Colors.grey.shade300),
          ),
          child: Text(
            lines.join('\n').trim(),
            style: TextStyle(fontSize: 13, height: 1.5, color: Colors.grey.shade800),
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: widgets,
    );
  }
}

