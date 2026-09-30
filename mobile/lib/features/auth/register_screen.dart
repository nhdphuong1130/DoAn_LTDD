import 'dart:async';
import 'package:flutter/material.dart';

import '../../api/api_error.dart';
import '../../app/student_api.dart';
import 'forgot_password_screen.dart';

class RegisterScreen extends StatefulWidget {
  final StudentApi api;
  final VoidCallback onAuthenticated;

  const RegisterScreen({
    super.key,
    required this.api,
    required this.onAuthenticated,
  });

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _phoneController = TextEditingController();
  final _otpController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  bool _isCodeSent = false;
  bool _isLoading = false;
  String? _errorMessage;
  bool _isPhoneAlreadyRegistered = false;
  String _lastChannel = 'sms';

  Timer? _timer;
  int _secondsRemaining = 60;

  @override
  void dispose() {
    _phoneController.dispose();
    _otpController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _timer?.cancel();
    super.dispose();
  }

  void _startCountdown() {
    _timer?.cancel();
    setState(() => _secondsRemaining = 60);
    _timer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_secondsRemaining > 0) {
        setState(() => _secondsRemaining--);
      } else {
        timer.cancel();
      }
    });
  }

  String _formatPhoneNumber(String input) {
    final cleaned = input.replaceAll(RegExp(r'\s+'), '').trim();
    if (cleaned.startsWith('0')) {
      return '+84${cleaned.substring(1)}';
    }
    if (!cleaned.startsWith('+')) {
      return '+84$cleaned';
    }
    return cleaned;
  }

  Future<void> _sendOtp({String channel = 'sms'}) async {
    final rawPhone = _phoneController.text.trim();
    if (rawPhone.isEmpty) {
      setState(() {
        _errorMessage = 'Vui lòng nhập số điện thoại';
        _isPhoneAlreadyRegistered = false;
      });
      return;
    }

    final formattedPhone = _formatPhoneNumber(rawPhone);

    setState(() {
      _isLoading = true;
      _errorMessage = null;
      _isPhoneAlreadyRegistered = false;
    });

    try {
      await widget.api.sendOtp(
        formattedPhone,
        channel: channel,
        purpose: 'register',
      );
      if (!mounted) return;
      setState(() {
        _lastChannel = channel;
        _isCodeSent = true;
        _isLoading = false;
        _errorMessage = null;
        _isPhoneAlreadyRegistered = false;
      });
      _startCountdown();
      final msg = channel == 'voice'
          ? 'Đang gọi điện đến $formattedPhone để đọc mã OTP'
          : 'Đã gửi mã OTP đến $formattedPhone qua tin nhắn SMS';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(msg),
          backgroundColor: channel == 'voice' ? Colors.blue[700] : Colors.green[700],
        ),
      );
    } catch (e) {
      if (mounted) {
        final isConflict = e is ApiException && (e.statusCode == 409 || e.code == 'phone_already_registered');
        setState(() {
          _isLoading = false;
          _isPhoneAlreadyRegistered = isConflict;
          _errorMessage = e is ApiException ? e.message : 'Lỗi gửi OTP: $e';
        });
      }
    }
  }

  Future<void> _register() async {
    final otp = _otpController.text.trim();
    final password = _passwordController.text;
    final confirm = _confirmPasswordController.text;

    if (otp.length != 6) {
      setState(() => _errorMessage = 'Vui lòng nhập đủ 6 chữ số OTP');
      return;
    }
    if (password.length < 8) {
      setState(() => _errorMessage = 'Mật khẩu phải có ít nhất 8 ký tự');
      return;
    }
    if (password != confirm) {
      setState(() => _errorMessage = 'Mật khẩu xác nhận không khớp');
      return;
    }

    final formattedPhone = _formatPhoneNumber(_phoneController.text);

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      await widget.api.registerPhone(
        phone: formattedPhone,
        otp: otp,
        password: password,
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Đăng ký tài khoản thành công!'),
            backgroundColor: Colors.green,
          ),
        );
        widget.onAuthenticated();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _errorMessage = e is ApiException ? e.message : 'Đăng ký thất bại: $e';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Đăng ký tài khoản mới'),
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: _isCodeSent ? _buildRegisterForm(theme) : _buildPhoneInputView(theme),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildPhoneInputView(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Icon(
          Icons.person_add_alt_1_outlined,
          size: 64,
          color: theme.colorScheme.primary,
        ),
        const SizedBox(height: 16),
        Text(
          'Tạo tài khoản học sinh',
          textAlign: TextAlign.center,
          style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        Text(
          'Nhập số điện thoại để nhận mã xác minh OTP tạo tài khoản mới.',
          textAlign: TextAlign.center,
          style: theme.textTheme.bodyMedium?.copyWith(color: Colors.grey[700]),
        ),
        const SizedBox(height: 24),
        TextField(
          key: const Key('register-phone-input'),
          controller: _phoneController,
          keyboardType: TextInputType.phone,
          decoration: const InputDecoration(
            labelText: 'Số điện thoại',
            hintText: '0912 345 678',
            prefixIcon: Padding(
              padding: EdgeInsets.symmetric(horizontal: 12),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text('🇻🇳 +84', style: TextStyle(fontWeight: FontWeight.bold)),
                  SizedBox(width: 8),
                ],
              ),
            ),
            border: OutlineInputBorder(),
          ),
        ),
        if (_errorMessage != null) ...[
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: theme.colorScheme.errorContainer.withValues(alpha: 0.5),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: theme.colorScheme.error),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Icon(Icons.error_outline, color: theme.colorScheme.error, size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        _errorMessage!,
                        style: TextStyle(
                          color: theme.colorScheme.error,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
                if (_isPhoneAlreadyRegistered) ...[
                  const SizedBox(height: 12),
                  Wrap(
                    alignment: WrapAlignment.end,
                    spacing: 8,
                    runSpacing: 4,
                    children: [
                      TextButton(
                        onPressed: () => Navigator.of(context).pop(),
                        child: const Text('Đăng nhập lại'),
                      ),
                      FilledButton.tonal(
                        onPressed: () {
                          Navigator.of(context).pushReplacement(
                            MaterialPageRoute(
                              builder: (_) => ForgotPasswordScreen(
                                api: widget.api,
                                initialPhone: _phoneController.text,
                              ),
                            ),
                          );
                        },
                        child: const Text('Quên mật khẩu?'),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
        ],
        const SizedBox(height: 24),
        FilledButton.icon(
          key: const Key('register-send-otp-btn'),
          onPressed: _isLoading ? null : () => _sendOtp(channel: 'sms'),
          icon: const Icon(Icons.sms_outlined),
          label: const Text('Gửi mã OTP qua SMS', style: TextStyle(fontSize: 16)),
          style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
        ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          key: const Key('register-send-voice-btn'),
          onPressed: _isLoading ? null : () => _sendOtp(channel: 'voice'),
          icon: const Icon(Icons.phone_in_talk_outlined),
          label: const Text('Nhận mã qua cuộc gọi', style: TextStyle(fontSize: 15)),
          style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
        ),
        if (_isLoading) ...[
          const SizedBox(height: 16),
          const Center(child: CircularProgressIndicator()),
        ],
        const SizedBox(height: 24),
        Wrap(
          alignment: WrapAlignment.center,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            const Text('Đã có tài khoản?'),
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Đăng nhập ngay'),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildRegisterForm(ThemeData theme) {
    final formattedPhone = _formatPhoneNumber(_phoneController.text);
    final isVoice = _lastChannel == 'voice';

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Icon(
          isVoice ? Icons.phone_callback_rounded : Icons.mark_email_read_outlined,
          size: 64,
          color: theme.colorScheme.primary,
        ),
        const SizedBox(height: 16),
        Text(
          'Xác nhận mã & Thiết lập mật khẩu',
          textAlign: TextAlign.center,
          style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        Text(
          'Mã xác nhận 6 số đã được gửi đến:\n$formattedPhone',
          textAlign: TextAlign.center,
          style: theme.textTheme.bodyMedium?.copyWith(color: Colors.grey[700]),
        ),
        const SizedBox(height: 24),
        TextField(
          key: const Key('register-otp-input'),
          controller: _otpController,
          keyboardType: TextInputType.number,
          maxLength: 6,
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 26, letterSpacing: 8, fontWeight: FontWeight.bold),
          decoration: const InputDecoration(
            counterText: '',
            labelText: 'Mã OTP (6 chữ số)',
            hintText: '------',
            border: OutlineInputBorder(),
          ),
        ),
        const SizedBox(height: 16),
        TextField(
          key: const Key('register-password-input'),
          controller: _passwordController,
          obscureText: true,
          decoration: const InputDecoration(
            labelText: 'Mật khẩu (tối thiểu 8 ký tự)',
            border: OutlineInputBorder(),
            prefixIcon: Icon(Icons.lock_outline),
          ),
        ),
        const SizedBox(height: 16),
        TextField(
          key: const Key('register-confirm-password-input'),
          controller: _confirmPasswordController,
          obscureText: true,
          decoration: const InputDecoration(
            labelText: 'Xác nhận mật khẩu',
            border: OutlineInputBorder(),
            prefixIcon: Icon(Icons.lock_outline),
          ),
        ),
        if (_errorMessage != null) ...[
          const SizedBox(height: 12),
          Text(
            _errorMessage!,
            style: TextStyle(color: theme.colorScheme.error),
          ),
        ],
        const SizedBox(height: 24),
        FilledButton(
          key: const Key('submit-register-btn'),
          onPressed: _isLoading ? null : _register,
          style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
          child: _isLoading
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                )
              : const Text('Hoàn tất Đăng ký', style: TextStyle(fontSize: 16)),
        ),
        const SizedBox(height: 16),
        if (_secondsRemaining > 0)
          Center(
            child: Text(
              'Gửi lại mã sau ${_secondsRemaining}s',
              style: TextStyle(color: Colors.grey[600]),
            ),
          )
        else
          Wrap(
            alignment: WrapAlignment.center,
            spacing: 8,
            children: [
              TextButton.icon(
                icon: const Icon(Icons.sms_outlined, size: 16),
                label: const Text('Gửi lại SMS'),
                onPressed: _isLoading ? null : () => _sendOtp(channel: 'sms'),
              ),
              TextButton.icon(
                icon: const Icon(Icons.phone_in_talk_outlined, size: 16),
                label: const Text('Gọi lại đọc mã'),
                onPressed: _isLoading ? null : () => _sendOtp(channel: 'voice'),
              ),
            ],
          ),
        const SizedBox(height: 8),
        Center(
          child: TextButton(
            onPressed: _isLoading
                ? null
                : () {
                    setState(() {
                      _isCodeSent = false;
                      _errorMessage = null;
                      _otpController.clear();
                    });
                  },
            child: const Text('Đổi số điện thoại khác'),
          ),
        ),
      ],
    );
  }
}
