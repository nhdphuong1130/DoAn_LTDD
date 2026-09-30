import 'package:flutter/material.dart';

import '../../app/learning_api.dart';

class ReviewScreen extends StatefulWidget {
  final LearningApi api;
  final FlashcardDeck deck;
  const ReviewScreen({super.key, required this.api, required this.deck});
  @override
  State<ReviewScreen> createState() => _ReviewScreenState();
}

class _ReviewScreenState extends State<ReviewScreen> {
  late Future<List<Flashcard>> _cards;
  final _answer = TextEditingController();
  int _index = 0;
  bool _revealed = false, _busy = false;
  String? _error, _requestId, _rating, _submittedAnswer;
  FlashcardReviewResult? _result;
  @override
  void initState() {
    super.initState();
    _cards = widget.api.loadReviewCards(widget.deck.id);
  }

  @override
  void dispose() {
    _answer.dispose();
    super.dispose();
  }

  Future<void> _rate(Flashcard card, String rating) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    _requestId ??= learningRequestId();
    _rating ??= rating;
    _submittedAnswer ??= _answer.text;
    try {
      final result = await widget.api.reviewCard(
        card.id,
        requestId: _requestId!,
        answer: _submittedAnswer!,
        rating: _rating!,
      );
      if (mounted) setState(() => _result = result);
    } catch (_) {
      if (mounted) {
        setState(() => _error = 'Chưa lưu được. Thử lại để lưu cùng kết quả.');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _next() {
    setState(() {
      _index++;
      _revealed = false;
      _result = null;
      _requestId = null;
      _rating = null;
      _submittedAnswer = null;
      _answer.clear();
    });
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Ôn từ')),
    body: FutureBuilder<List<Flashcard>>(
      future: _cards,
      builder: (context, snapshot) {
        if (snapshot.hasError) {
          return Center(
            child: TextButton(
              onPressed: () => setState(
                () => _cards = widget.api.loadReviewCards(widget.deck.id),
              ),
              child: const Text('Không tải được. Thử lại'),
            ),
          );
        }
        if (!snapshot.hasData) {
          return const Center(child: CircularProgressIndicator());
        }
        if (_index >= snapshot.data!.length) {
          return const Center(
            child: Text('Đã hết thẻ đến hạn và từ mới trong lượt này.'),
          );
        }
        final card = snapshot.data![_index];
        return ListView(
          padding: const EdgeInsets.all(24),
          children: [
            Text('Thẻ ${_index + 1}/${snapshot.data!.length}'),
            Text(
              card.meaning,
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const Text('Nhớ lại và nhập từ tiếng Anh trước khi xem đáp án.'),
            TextField(
              controller: _answer,
              enabled: !_revealed,
              decoration: const InputDecoration(labelText: 'Từ tiếng Anh'),
              autocorrect: false,
              enableSuggestions: false,
            ),
            if (!_revealed)
              FilledButton(
                onPressed: () {
                  setState(() => _revealed = true);
                },
                child: const Text('Xem đáp án'),
              ),
            if (_revealed) ...[
              Text(
                card.word,
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              Text('${card.ipa ?? ""} ${card.pos ?? ""}'),
              if (card.example.isNotEmpty) Text(card.example),
              Text(card.sourceLabel ?? 'Nội dung cá nhân'),
              const Text(
                'Tự đánh giá độ nhớ. Hệ thống kiểm tra câu trả lời bạn đã nhập để xếp lịch ôn.',
              ),
              if (_result == null)
                Wrap(
                  spacing: 8,
                  children: [
                    for (final item in const {
                      'again': 'Chưa nhớ',
                      'hard': 'Còn khó',
                      'good': 'Đã nhớ',
                    }.entries)
                      OutlinedButton(
                        onPressed:
                            _busy || (_rating != null && _rating != item.key)
                            ? null
                            : () => _rate(card, item.key),
                        child: Text(item.value),
                      ),
                  ],
                ),
            ],
            if (_busy) const LinearProgressIndicator(),
            if (_error != null) Text(_error!),
            if (_result != null) ...[
              Text(
                _result!.correct
                    ? 'Trả lời đúng. Đã lưu lịch ôn.'
                    : 'Chưa đúng. Từ này cần ôn lại sớm.',
              ),
              Text(
                'Ôn tiếp: ${_result!.dueAt.toLocal().toString().split(".").first}',
              ),
              FilledButton(
                onPressed: _next,
                child: const Text('Thẻ tiếp theo'),
              ),
            ],
          ],
        );
      },
    ),
  );
}
