import 'dart:async';
import 'package:flutter/material.dart';

import '../../api/api_error.dart';
import '../../app/student_api.dart';

class ForgotPasswordScreen extends StatefulWidget {
  final StudentApi api;
  final String? initialPhone;

  const ForgotPasswordScreen({super.key, required this.api, this.initialPhone});

  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _phoneController = TextEditingController();
  final _otpController = TextEditingController();
  final _newPasswordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  bool _isCodeSent = false;
  bool _isLoading = false;
  String? _errorMessage;
  String _lastChannel = 'sms';

  Timer? _timer;
  int _secondsRemaining = 60;

  @override
  void initState() {
    super.initState();
    if (widget.initialPhone != null && widget.initialPhone!.isNotEmpty) {
      _phoneController.text = widget.initialPhone!;
    }
  }

  @override
  void dispose() {
    _phoneController.dispose();
    _otpController.dispose();
    _newPasswordController.dispose();
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
    if (cleaned.contains('@')) {
      return cleaned.toLowerCase();
    }
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
      setState(() => _errorMessage = 'Vui lòng nhập số điện thoại');
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
        purpose: 'reset_password',
      );
      if (!mounted) return;
      setState(() {
        _lastChannel = channel;
        _isCodeSent = true;
        _isLoading = false;
        _errorMessage = null;
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
        setState(() {
          _isLoading = false;
          _errorMessage = e is ApiException ? e.message : 'Lỗi gửi OTP: $e';
        });
      }
    }
  }

  Future<void> _resetPassword() async {
    final otp = _otpController.text.trim();
    final newPassword = _newPasswordController.text;
    final confirmPassword = _confirmPasswordController.text;

    if (otp.length != 6) {
      setState(() => _errorMessage = 'Vui lòng nhập đủ 6 chữ số OTP');
      return;
    }
    if (newPassword.length < 8) {
      setState(() => _errorMessage = 'Mật khẩu mới phải có ít nhất 8 ký tự');
      return;
    }
    if (newPassword != confirmPassword) {
      setState(() => _errorMessage = 'Mật khẩu xác nhận không khớp');
      return;
    }

    final formattedPhone = _formatPhoneNumber(_phoneController.text);

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      await widget.api.resetPassword(
        phone: formattedPhone,
        otp: otp,
        newPassword: newPassword,
        confirmPassword: confirmPassword,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Đặt lại mật khẩu thành công! Vui lòng đăng nhập bằng mật khẩu mới.'),
          backgroundColor: Colors.green,
        ),
      );
      Navigator.of(context).pop();
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _errorMessage = e is ApiException ? e.message : 'Đặt lại mật khẩu thất bại: $e';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Quên mật khẩu'),
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: _isCodeSent ? _buildResetForm(theme) : _buildPhoneInputView(theme),
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
          Icons.lock_reset_outlined,
          size: 64,
          color: theme.colorScheme.primary,
        ),
        const SizedBox(height: 16),
        Text(
          'Lấy lại mật khẩu',
          textAlign: TextAlign.center,
          style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        Text(
          'Nhập số điện thoại hoặc email đã đăng ký để nhận mã xác minh OTP đặt lại mật khẩu mới.',
          textAlign: TextAlign.center,
          style: theme.textTheme.bodyMedium?.copyWith(color: Colors.grey[700]),
        ),
        const SizedBox(height: 24),
        TextField(
          key: const Key('forgot-phone-input'),
          controller: _phoneController,
          keyboardType: TextInputType.emailAddress,
          decoration: const InputDecoration(
            labelText: 'Số điện thoại hoặc Email đã đăng ký',
            hintText: '0374423251 hoặc email@english7.edu.vn',
            prefixIcon: Icon(Icons.account_circle_outlined),
            border: OutlineInputBorder(),
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
        FilledButton.icon(
          key: const Key('forgot-send-otp-btn'),
          onPressed: _isLoading ? null : () => _sendOtp(channel: 'sms'),
          icon: const Icon(Icons.sms_outlined),
          label: const Text('Gửi mã OTP qua SMS', style: TextStyle(fontSize: 16)),
          style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
        ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          key: const Key('forgot-send-voice-btn'),
          onPressed: _isLoading ? null : () => _sendOtp(channel: 'voice'),
          icon: const Icon(Icons.phone_in_talk_outlined),
          label: const Text('Nhận mã qua cuộc gọi', style: TextStyle(fontSize: 15)),
          style: OutlinedButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
        ),
        if (_isLoading) ...[
          const SizedBox(height: 16),
          const Center(child: CircularProgressIndicator()),
        ],
      ],
    );
  }

  Widget _buildResetForm(ThemeData theme) {
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
          'Thiết lập mật khẩu mới',
          textAlign: TextAlign.center,
          style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        Text(
          'Mã OTP đã được gửi đến số $formattedPhone. Vui lòng nhập mã và mật khẩu mới.',
          textAlign: TextAlign.center,
          style: theme.textTheme.bodyMedium?.copyWith(color: Colors.grey[700]),
        ),
        const SizedBox(height: 24),
        TextField(
          key: const Key('reset-otp-input'),
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
          key: const Key('reset-new-password-input'),
          controller: _newPasswordController,
          obscureText: true,
          decoration: const InputDecoration(
            labelText: 'Mật khẩu mới (tối thiểu 8 ký tự)',
            border: OutlineInputBorder(),
            prefixIcon: Icon(Icons.lock_outline),
          ),
        ),
        const SizedBox(height: 16),
        TextField(
          key: const Key('reset-confirm-password-input'),
          controller: _confirmPasswordController,
          obscureText: true,
          decoration: const InputDecoration(
            labelText: 'Xác nhận mật khẩu mới',
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
          key: const Key('submit-reset-password-btn'),
          onPressed: _isLoading ? null : _resetPassword,
          style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
          child: _isLoading
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                )
              : const Text('Đặt lại mật khẩu', style: TextStyle(fontSize: 16)),
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
