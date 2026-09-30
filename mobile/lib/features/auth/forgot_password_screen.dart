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

  // 0: Nhập SĐT, 1: Xác thực OTP, 2: Thiết lập mật khẩu mới
  int _step = 0;
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
        _step = 1;
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
      await widget.api.validateOtp(formattedPhone, otp);
      if (!mounted) return;
      setState(() {
        _step = 2;
        _errorMessage = null;
      });
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e is ApiException ? e.message : 'Mã OTP không hợp lệ: $e';
        });
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  Future<void> _resetPassword() async {
    final otp = _otpController.text.trim();
    final newPassword = _newPasswordController.text;
    final confirmPassword = _confirmPasswordController.text;

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
          _errorMessage = e is ApiException ? e.message : 'Đặt lại mật khẩu thất bại: $e';
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
        title: const Text('Quên mật khẩu'),
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  _buildStepIndicator(theme),
                  const SizedBox(height: 24),
                  if (_step == 0) _buildPhoneInputView(theme),
                  if (_step == 1) _buildOtpView(theme),
                  if (_step == 2) _buildNewPasswordView(theme),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildStepIndicator(ThemeData theme) {
    final stepTitles = ['Số điện thoại', 'Xác thực OTP', 'Mật khẩu mới'];
    return Row(
      children: List.generate(3, (index) {
        final isActive = index == _step;
        final isCompleted = index < _step;
        return Expanded(
          child: Row(
            children: [
              Expanded(
                child: Column(
                  children: [
                    Container(
                      width: 28,
                      height: 28,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: isCompleted
                            ? Colors.green
                            : isActive
                                ? theme.colorScheme.primary
                                : Colors.grey[300],
                      ),
                      child: Center(
                        child: isCompleted
                            ? const Icon(Icons.check, size: 16, color: Colors.white)
                            : Text(
                                '${index + 1}',
                                style: TextStyle(
                                  color: isActive ? Colors.white : Colors.grey[700],
                                  fontWeight: FontWeight.bold,
                                  fontSize: 13,
                                ),
                              ),
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      stepTitles[index],
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: isActive ? FontWeight.bold : FontWeight.normal,
                        color: isActive ? theme.colorScheme.primary : Colors.grey[600],
                      ),
                      textAlign: TextAlign.center,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
              if (index < 2)
                Container(
                  width: 20,
                  height: 2,
                  color: isCompleted ? Colors.green : Colors.grey[300],
                  margin: const EdgeInsets.only(bottom: 16),
                ),
            ],
          ),
        );
      }),
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

  Widget _buildOtpView(ThemeData theme) {
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
          'Xác nhận mã OTP',
          textAlign: TextAlign.center,
          style: theme.textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        Text(
          'Mã OTP đã được gửi đến:\n$formattedPhone\nVui lòng nhập mã 6 số để tiếp tục.',
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
        if (_errorMessage != null) ...[
          const SizedBox(height: 12),
          Text(
            _errorMessage!,
            style: TextStyle(color: theme.colorScheme.error),
          ),
        ],
        const SizedBox(height: 24),
        FilledButton(
          key: const Key('verify-reset-otp-btn'),
          onPressed: _isLoading ? null : _verifyOtp,
          style: FilledButton.styleFrom(padding: const EdgeInsets.symmetric(vertical: 14)),
          child: _isLoading
              ? const SizedBox(
                  height: 20,
                  width: 20,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                )
              : const Text('Xác nhận mã OTP', style: TextStyle(fontSize: 16)),
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
                      _step = 0;
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

  Widget _buildNewPasswordView(ThemeData theme) {
    final formattedPhone = _formatPhoneNumber(_phoneController.text);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Icon(
          Icons.vpn_key_outlined,
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
          'Mã OTP đã được xác nhận cho số $formattedPhone.\nVui lòng đặt mật khẩu mới cho tài khoản.',
          textAlign: TextAlign.center,
          style: theme.textTheme.bodyMedium?.copyWith(color: Colors.grey[700]),
        ),
        const SizedBox(height: 24),
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
        Center(
          child: TextButton.icon(
            icon: const Icon(Icons.arrow_back, size: 16),
            label: const Text('Quay lại nhập mã OTP'),
            onPressed: _isLoading
                ? null
                : () {
                    setState(() {
                      _step = 1;
                      _errorMessage = null;
                    });
                  },
          ),
        ),
      ],
    );
  }
}
