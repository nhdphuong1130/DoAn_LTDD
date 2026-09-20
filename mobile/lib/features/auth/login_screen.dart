import 'package:flutter/material.dart';

import '../../app/student_api.dart';

class LoginScreen extends StatefulWidget {
  final StudentApi api;
  final VoidCallback onAuthenticated;
  const LoginScreen({
    super.key,
    required this.api,
    required this.onAuthenticated,
  });

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      await widget.api.login(_email.text, _password.text);
      widget.onAuthenticated();
    } catch (_) {
      if (mounted) setState(() => _error = 'Đăng nhập không thành công');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    body: SafeArea(
      child: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Icon(
                  Icons.school,
                  size: 72,
                  color: Theme.of(context).colorScheme.primary,
                ),
                const SizedBox(height: 16),
                Text(
                  'English 7',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                const SizedBox(height: 24),
                TextField(
                  key: const Key('email-field'),
                  controller: _email,
                  keyboardType: TextInputType.emailAddress,
                  decoration: const InputDecoration(labelText: 'Email'),
                ),
                const SizedBox(height: 12),
                TextField(
                  key: const Key('password-field'),
                  controller: _password,
                  obscureText: true,
                  decoration: const InputDecoration(labelText: 'Mật khẩu'),
                ),
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    _error!,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.error,
                    ),
                  ),
                ],
                FilledButton(
                  onPressed: _busy ? null : _login,
                  child: Text(_busy ? 'Đang đăng nhập…' : 'Đăng nhập'),
                ),
                const SizedBox(height: 12),
                TextButton.icon(
                  onPressed: () {
                    _email.text = 'student@english7.edu.vn';
                    _password.text = 'StudentPassword123!';
                  },
                  icon: const Icon(Icons.account_circle_outlined, size: 18),
                  label: const Text('Điền tài khoản mẫu (Học sinh)'),
                ),
              ],
            ),
          ),
        ),
      ),
    ),
  );
}
