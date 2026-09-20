import 'package:flutter/material.dart';

import '../../app/student_api.dart';

class ProfileScreen extends StatefulWidget {
  final StudentApi api;
  final Future<void> Function() onLogout;

  const ProfileScreen({super.key, required this.api, required this.onLogout});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  bool _loading = true;
  String? _loadError;
  StudentProfile? _profile;

  bool _isEditing = false;
  bool _savingProfile = false;
  String? _profileError;

  bool _changingPassword = false;
  String? _passwordError;

  late final TextEditingController _fullNameController;
  late final TextEditingController _schoolNameController;
  late final TextEditingController _classNameController;
  late final TextEditingController _currentPasswordController;
  late final TextEditingController _newPasswordController;
  late final TextEditingController _confirmPasswordController;

  DateTime? _selectedDob;
  ProfileGender? _selectedGender;

  @override
  void initState() {
    super.initState();
    _fullNameController = TextEditingController();
    _schoolNameController = TextEditingController();
    _classNameController = TextEditingController();
    _currentPasswordController = TextEditingController();
    _newPasswordController = TextEditingController();
    _confirmPasswordController = TextEditingController();
    _loadProfile();
  }

  @override
  void dispose() {
    _fullNameController.dispose();
    _schoolNameController.dispose();
    _classNameController.dispose();
    _currentPasswordController.dispose();
    _newPasswordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _loadProfile() async {
    setState(() {
      _loading = true;
      _loadError = null;
    });

    try {
      final profile = await widget.api.loadProfile();
      if (!mounted) return;
      setState(() {
        _profile = profile;
        _fullNameController.text = profile.fullName ?? '';
        _schoolNameController.text = profile.schoolName ?? '';
        _classNameController.text = profile.className ?? '';
        _selectedDob = profile.dateOfBirth;
        _selectedGender = profile.gender;
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _loadError = 'Không thể tải thông tin hồ sơ';
        _loading = false;
      });
    }
  }

  void _populateControllers(StudentProfile profile) {
    _fullNameController.text = profile.fullName ?? '';
    _schoolNameController.text = profile.schoolName ?? '';
    _classNameController.text = profile.className ?? '';
    _selectedDob = profile.dateOfBirth;
    _selectedGender = profile.gender;
  }

  Future<void> _saveProfile() async {
    setState(() {
      _savingProfile = true;
      _profileError = null;
    });

    try {
      final update = ProfileUpdate(
        fullName: _fullNameController.text.trim().isEmpty
            ? null
            : _fullNameController.text.trim(),
        dateOfBirth: _selectedDob,
        gender: _selectedGender,
        schoolName: _schoolNameController.text.trim().isEmpty
            ? null
            : _schoolNameController.text.trim(),
        className: _classNameController.text.trim().isEmpty
            ? null
            : _classNameController.text.trim(),
      );

      final updated = await widget.api.updateProfile(update);
      if (!mounted) return;

      setState(() {
        _profile = updated;
        _populateControllers(updated);
        _isEditing = false;
        _savingProfile = false;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Cập nhật hồ sơ thành công')),
      );
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _profileError = 'Cập nhật hồ sơ thất bại';
        _savingProfile = false;
      });
    }
  }

  Future<void> _changePassword() async {
    final current = _currentPasswordController.text;
    final newPass = _newPasswordController.text;
    final confirm = _confirmPasswordController.text;

    if (current.isEmpty || newPass.isEmpty || confirm.isEmpty) {
      setState(
        () => _passwordError = 'Vui lòng điền đầy đủ các trường mật khẩu',
      );
      return;
    }

    if (newPass != confirm) {
      setState(() => _passwordError = 'Mật khẩu xác nhận không khớp');
      return;
    }

    setState(() {
      _changingPassword = true;
      _passwordError = null;
    });

    try {
      await widget.api.changePassword(current, newPass, confirm);
      if (!mounted) return;

      _currentPasswordController.clear();
      _newPasswordController.clear();
      _confirmPasswordController.clear();

      setState(() => _changingPassword = false);

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text('Đổi mật khẩu thành công')));
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _passwordError = 'Đổi mật khẩu thất bại';
        _changingPassword = false;
      });
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Đổi mật khẩu thất bại')));
    }
  }

  Future<void> _confirmLogout() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Đăng xuất'),
        content: const Text('Bạn có chắc muốn đăng xuất?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Đăng xuất'),
          ),
        ],
      ),
    );

    if (confirmed == true && mounted) {
      await widget.onLogout();
    }
  }

  String _genderLabel(ProfileGender? gender) => switch (gender) {
    ProfileGender.male => 'Nam',
    ProfileGender.female => 'Nữ',
    ProfileGender.other => 'Khác',
    ProfileGender.preferNotToSay => 'Không muốn nói',
    null => 'Chưa cập nhật',
  };

  String _formatDate(DateTime? date) {
    if (date == null) return 'Chưa cập nhật';
    final day = date.day.toString().padLeft(2, '0');
    final month = date.month.toString().padLeft(2, '0');
    return '$day/$month/${date.year}';
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _selectedDob ?? DateTime(now.year - 12, 1, 1),
      firstDate: DateTime(now.year - 25),
      lastDate: DateTime(now.year - 5),
    );
    if (picked != null && mounted) {
      setState(() => _selectedDob = picked);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_loadError != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(_loadError!),
            const SizedBox(height: 12),
            FilledButton(onPressed: _loadProfile, child: const Text('Thử lại')),
          ],
        ),
      );
    }

    final profile = _profile!;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        'Thông tin cá nhân',
                        style: Theme.of(context).textTheme.titleLarge,
                      ),
                      if (!_isEditing)
                        OutlinedButton.icon(
                          onPressed: () => setState(() => _isEditing = true),
                          icon: const Icon(Icons.edit, size: 16),
                          label: const Text('Chỉnh sửa hồ sơ'),
                        ),
                    ],
                  ),
                  const Divider(height: 24),
                  _buildReadOnlyRow('Email', profile.email),
                  const SizedBox(height: 8),
                  _buildReadOnlyRow(
                    'Vai trò',
                    profile.role == 'student' ? 'Học sinh' : profile.role,
                  ),
                  const SizedBox(height: 16),
                  if (!_isEditing) ...[
                    _buildInfoRow(
                      'Họ và tên',
                      profile.fullName ?? 'Chưa cập nhật',
                    ),
                    const SizedBox(height: 8),
                    _buildInfoRow(
                      'Ngày sinh',
                      _formatDate(profile.dateOfBirth),
                    ),
                    const SizedBox(height: 8),
                    _buildInfoRow('Giới tính', _genderLabel(profile.gender)),
                    const SizedBox(height: 8),
                    _buildInfoRow(
                      'Trường học',
                      profile.schoolName ?? 'Chưa cập nhật',
                    ),
                    const SizedBox(height: 8),
                    _buildInfoRow('Lớp', profile.className ?? 'Chưa cập nhật'),
                  ] else ...[
                    TextField(
                      key: const Key('profile-full-name'),
                      controller: _fullNameController,
                      decoration: const InputDecoration(labelText: 'Họ và tên'),
                    ),
                    const SizedBox(height: 12),
                    Row(
                      children: [
                        Expanded(
                          child: OutlinedButton.icon(
                            onPressed: _pickDate,
                            icon: const Icon(Icons.calendar_today, size: 16),
                            label: Text(
                              _selectedDob == null
                                  ? 'Chọn ngày sinh'
                                  : 'Ngày sinh: ${_formatDate(_selectedDob)}',
                            ),
                          ),
                        ),
                        if (_selectedDob != null)
                          IconButton(
                            onPressed: () =>
                                setState(() => _selectedDob = null),
                            icon: const Icon(Icons.clear),
                          ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    DropdownButtonFormField<ProfileGender?>(
                      initialValue: _selectedGender,
                      decoration: const InputDecoration(labelText: 'Giới tính'),
                      items: const [
                        DropdownMenuItem(
                          value: null,
                          child: Text('Chưa cập nhật'),
                        ),
                        DropdownMenuItem(
                          value: ProfileGender.male,
                          child: Text('Nam'),
                        ),
                        DropdownMenuItem(
                          value: ProfileGender.female,
                          child: Text('Nữ'),
                        ),
                        DropdownMenuItem(
                          value: ProfileGender.other,
                          child: Text('Khác'),
                        ),
                        DropdownMenuItem(
                          value: ProfileGender.preferNotToSay,
                          child: Text('Không muốn nói'),
                        ),
                      ],
                      onChanged: (val) => setState(() => _selectedGender = val),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      key: const Key('profile-school-name'),
                      controller: _schoolNameController,
                      decoration: const InputDecoration(
                        labelText: 'Trường học',
                      ),
                    ),
                    const SizedBox(height: 12),
                    TextField(
                      key: const Key('profile-class-name'),
                      controller: _classNameController,
                      decoration: const InputDecoration(labelText: 'Lớp'),
                    ),
                    if (_profileError != null) ...[
                      const SizedBox(height: 8),
                      Text(
                        _profileError!,
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.error,
                        ),
                      ),
                    ],
                    const SizedBox(height: 16),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        TextButton(
                          onPressed: _savingProfile
                              ? null
                              : () {
                                  setState(() {
                                    _populateControllers(profile);
                                    _profileError = null;
                                    _isEditing = false;
                                  });
                                },
                          child: const Text('Hủy'),
                        ),
                        const SizedBox(width: 8),
                        FilledButton(
                          onPressed: _savingProfile ? null : _saveProfile,
                          child: _savingProfile
                              ? const SizedBox(
                                  width: 16,
                                  height: 16,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Text('Lưu thay đổi'),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Đổi mật khẩu',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const Divider(height: 24),
                  TextField(
                    key: const Key('current-password-field'),
                    controller: _currentPasswordController,
                    obscureText: true,
                    decoration: const InputDecoration(
                      labelText: 'Mật khẩu hiện tại',
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    key: const Key('new-password-field'),
                    controller: _newPasswordController,
                    obscureText: true,
                    decoration: const InputDecoration(
                      labelText: 'Mật khẩu mới',
                    ),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    key: const Key('confirm-password-field'),
                    controller: _confirmPasswordController,
                    obscureText: true,
                    decoration: const InputDecoration(
                      labelText: 'Xác nhận mật khẩu mới',
                    ),
                  ),
                  if (_passwordError != null) ...[
                    const SizedBox(height: 8),
                    Text(
                      _passwordError!,
                      style: TextStyle(
                        color: Theme.of(context).colorScheme.error,
                      ),
                    ),
                  ],
                  const SizedBox(height: 16),
                  Align(
                    alignment: Alignment.centerRight,
                    child: FilledButton(
                      onPressed: _changingPassword ? null : _changePassword,
                      child: _changingPassword
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Text('Đổi mật khẩu'),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          OutlinedButton.icon(
            key: const Key('logout-button'),
            onPressed: _confirmLogout,
            icon: const Icon(Icons.logout, color: Colors.red),
            label: const Text('Đăng xuất', style: TextStyle(color: Colors.red)),
            style: OutlinedButton.styleFrom(
              side: const BorderSide(color: Colors.red),
              padding: const EdgeInsets.symmetric(vertical: 12),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildReadOnlyRow(String label, String value) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 100,
          child: Text(
            label,
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
        ),
        Expanded(child: Text(value)),
      ],
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        SizedBox(
          width: 100,
          child: Text(label, style: const TextStyle(color: Colors.grey)),
        ),
        Expanded(child: Text(value)),
      ],
    );
  }
}
