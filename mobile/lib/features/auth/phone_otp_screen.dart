import 'dart:async';
import 'package:flutter/material.dart';

import '../../api/api_error.dart';
import '../../app/student_api.dart';
import 'forgot_password_screen.dart';

class PhoneOtpScreen extends StatefulWidget {
  final StudentApi api;
  final VoidCallback onAuthenticated;

  const PhoneOtpScreen({
    super.key,
    required this.api,
    required this.onAuthenticated,
  });

  @override
  State<PhoneOtpScreen> createState() => _PhoneOtpScreenState();
}

class _PhoneOtpScreenState extends State<PhoneOtpScreen> {
  final _phoneController = TextEditingController();
  final _otpController = TextEditingController();

  bool _isCodeSent = false;
  bool _isLoading = false;
  String? _errorMessage;
  String _lastChannel = 'sms';

  Timer? _timer;
  int _secondsRemaining = 60;

  @override
  void dispose() {
    _phoneController.dispose();
    _otpController.dispose();
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
    String cleaned = input.replaceAll(RegExp(r'\s+'), '').trim();
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
      });
      return;
    }

    final formattedPhone = _formatPhoneNumber(rawPhone);

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      await widget.api.sendOtp(
        formattedPhone,
        channel: channel,
        purpose: 'any',
      );
      if (!mounted) return;
      setState(() {
        _lastChannel = channel;
        _isCodeSent = true;
        _isLoading = false;
        _errorMessage = null;
      });
      _startCountdown();
      final message = channel == 'voice'
          ? 'Đang gọi điện đến $formattedPhone để đọc mã OTP'
          : 'Đã gửi mã OTP đến $formattedPhone qua tin nhắn SMS';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: channel == 'voice' ? Colors.blue[700] : Colors.green[700],
        ),
      );
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _errorMessage = e is ApiException ? e.message : 'Lỗi gửi OTP: $e';
        });
      }
    }
  }

  Future<void> _verifyOtp() async {
    final otp = _otpController.text.trim();
    if (otp.length != 6) {
      setState(() => _errorMessage = 'Vui lòng nhập đủ 6 chữ số OTP');
      return;
    }

    final formattedPhone = _formatPhoneNumber(_phoneController.text);

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      await widget.api.verifyOtp(formattedPhone, otp);
      if (mounted) {
        if (Navigator.of(context).canPop()) {
          Navigator.of(context).pop();
        }
        widget.onAuthenticated();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e is ApiException ? e.message : 'Xác thực thất bại: $e';
        });
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(_isCodeSent ? 'Xác thực mã OTP' : 'Đăng nhập / Đăng ký bằng OTP'),
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: _isCodeSent ? _buildOtpInputView(theme) : _buildPhoneInputView(theme),
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
          Icons.phonelink_ring_outlined,
          size: 64,
          color: theme.colorScheme.primary,
        ),
        const SizedBox(height: 16),
        Text(
          'Đăng nhập / Đăng ký bằng số điện thoại',
          textAlign: TextAlign.center,
          style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        Text(
          'Nhập số điện thoại để nhận mã xác minh OTP 6 số. Hệ thống sẽ tự động đăng nhập hoặc tạo tài khoản mới nếu chưa có.',
          textAlign: TextAlign.center,
          style: theme.textTheme.bodyMedium?.copyWith(color: Colors.grey[700]),
        ),
        const SizedBox(height: 24),
        TextField(
          key: const Key('phone-input-field'),
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
            child: Row(
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
          ),
        ],
        const SizedBox(height: 24),
        FilledButton.icon(
          key: const Key('send-otp-btn'),
          onPressed: _isLoading ? null : () => _sendOtp(channel: 'sms'),
          icon: const Icon(Icons.sms_outlined),
          label: const Text('Gửi mã OTP qua SMS', style: TextStyle(fontSize: 16)),
          style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
        ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          key: const Key('send-otp-voice-btn'),
          onPressed: _isLoading ? null : () => _sendOtp(channel: 'voice'),
          icon: const Icon(Icons.phone_in_talk_outlined),
          label: const Text('Nhận mã qua cuộc gọi', style: TextStyle(fontSize: 15)),
          style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
        ),
        if (_isLoading) ...[
          const SizedBox(height: 16),
          const Center(child: CircularProgressIndicator()),
        ],
        const SizedBox(height: 16),
        Center(
          child: TextButton.icon(
            key: const Key('otp-forgot-password-btn'),
            icon: const Icon(Icons.lock_reset, size: 18),
            label: const Text('Quên mật khẩu? Đặt lại mật khẩu'),
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => ForgotPasswordScreen(
                    api: widget.api,
                    initialPhone: _phoneController.text,
                  ),
                ),
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildOtpInputView(ThemeData theme) {
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
          'Nhập mã OTP',
          textAlign: TextAlign.center,
          style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        Text(
          isVoice
              ? 'Hệ thống đang gọi điện đến số:\n$formattedPhone\nVui lòng nghe máy để nhận mã OTP 6 chữ số.'
              : 'Mã xác nhận 6 số đã được gửi đến số điện thoại:\n$formattedPhone',
          textAlign: TextAlign.center,
          style: theme.textTheme.bodyMedium?.copyWith(color: Colors.grey[700]),
        ),
        const SizedBox(height: 24),
        TextField(
          key: const Key('otp-input-field'),
          controller: _otpController,
          keyboardType: TextInputType.number,
          maxLength: 6,
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 28, letterSpacing: 10, fontWeight: FontWeight.bold),
          decoration: const InputDecoration(
            counterText: '',
            hintText: '------',
            border: OutlineInputBorder(),
          ),
          onChanged: (value) {
            if (value.length == 6) {
              _verifyOtp();
            }
          },
        ),
        if (_errorMessage != null) ...[
          const SizedBox(height: 12),
          Text(
            _errorMessage!,
            textAlign: TextAlign.center,
            style: TextStyle(color: theme.colorScheme.error),
          ),
        ],
        const SizedBox(height: 20),
        FilledButton(
          key: const Key('verify-otp-btn'),
          onPressed: _isLoading ? null : _verifyOtp,
          style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
          child: _isLoading
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                )
              : const Text('Xác nhận & Đăng nhập', style: TextStyle(fontSize: 16)),
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
            runSpacing: 4,
            children: [
              TextButton.icon(
                key: const Key('resend-sms-btn'),
                icon: const Icon(Icons.sms_outlined, size: 16),
                label: const Text('Gửi lại SMS'),
                onPressed: _isLoading ? null : () => _sendOtp(channel: 'sms'),
              ),
              TextButton.icon(
                key: const Key('resend-voice-btn'),
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
            child: const Text('Đổi số điện thoại'),
          ),
        ),
      ],
    );
  }
}
