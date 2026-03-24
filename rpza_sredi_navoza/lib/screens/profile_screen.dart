import 'dart:typed_data';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../providers/auth_provider.dart';
import '../providers/subscription_provider.dart';
import '../theme/app_theme.dart';
import 'login_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});
  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  Uint8List? _avatarBytes;
  static const _avatarKey = 'user_avatar';

  @override
  void initState() {
    super.initState();
    _loadAvatar();
  }

  Future<void> _loadAvatar() async {
    final prefs = await SharedPreferences.getInstance();
    final b64 = prefs.getString(_avatarKey);
    if (b64 != null && b64.isNotEmpty) {
      setState(() => _avatarBytes = base64Decode(b64));
    }
  }

  void _pickAvatar() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(source: ImageSource.gallery, imageQuality: 80);
    if (picked == null) return;
    final bytes = await picked.readAsBytes();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_avatarKey, base64Encode(bytes));
    setState(() => _avatarBytes = bytes);
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final subs = context.watch<SubscriptionProvider>();
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = isDark ? Colors.white : const Color(0xFF1A1A1A);
    final user = auth.user;
    final initial = (user?.name.isNotEmpty == true ? user!.name[0] : '?').toUpperCase();

    return Scaffold(
      appBar: AppBar(title: const Text('ПРОФИЛЬ')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  children: [
                    // Аватар — нажать чтобы сменить
                    GestureDetector(
                      onTap: _pickAvatar,
                      child: Stack(
                        children: [
                          Container(
                            width: 96, height: 96,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              gradient: _avatarBytes == null
                                  ? const LinearGradient(
                                      colors: [AppTheme.neonPurple, AppTheme.neonPink],
                                      begin: Alignment.topLeft,
                                      end: Alignment.bottomRight,
                                    )
                                  : null,
                              image: _avatarBytes != null
                                  ? DecorationImage(
                                      image: MemoryImage(_avatarBytes!),
                                      fit: BoxFit.cover,
                                    )
                                  : null,
                              boxShadow: [
                                BoxShadow(
                                  color: AppTheme.neonPurple.withValues(alpha: 0.35),
                                  blurRadius: 20,
                                  spreadRadius: 2,
                                ),
                              ],
                            ),
                            child: _avatarBytes == null
                                ? Center(
                                    child: Text(initial,
                                        style: const TextStyle(
                                            color: Colors.white,
                                            fontSize: 38,
                                            fontWeight: FontWeight.w900)),
                                  )
                                : null,
                          ),
                          Positioned(
                            bottom: 0, right: 0,
                            child: Container(
                              width: 30, height: 30,
                              decoration: const BoxDecoration(
                                color: AppTheme.neonPurple,
                                shape: BoxShape.circle,
                              ),
                              child: const Icon(Icons.camera_alt_rounded,
                                  color: Colors.white, size: 16),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),
                    Text(user?.name ?? '—',
                        style: TextStyle(
                            color: textColor, fontSize: 22, fontWeight: FontWeight.w900)),
                    const SizedBox(height: 4),
                    Text(user?.email ?? '—',
                        style: const TextStyle(
                            color: AppTheme.neonPurple,
                            fontSize: 13,
                            fontWeight: FontWeight.w700)),
                    const SizedBox(height: 20),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                      children: [
                        _Stat('${subs.subscriptions.length}', 'ПОДПИСОК',
                            AppTheme.neonPurple, textColor),
                        Container(
                            width: 1,
                            height: 40,
                            color: textColor.withValues(alpha: 0.1)),
                        _Stat(
                          '${subs.analytics?['total_monthly']?.toStringAsFixed(0) ?? 0} ₽',
                          'В МЕСЯЦ',
                          AppTheme.neonPink,
                          textColor,
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),

            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(children: [
                      Container(
                          width: 8,
                          height: 8,
                          decoration: const BoxDecoration(
                              color: AppTheme.neonPink, shape: BoxShape.circle)),
                      const SizedBox(width: 8),
                      const Text('СТАТУС АККАУНТА',
                          style: TextStyle(
                              color: AppTheme.neonPink,
                              fontSize: 11,
                              fontWeight: FontWeight.w900,
                              letterSpacing: 2)),
                    ]),
                    const SizedBox(height: 12),
                    _InfoRow(
                        'Подписок активно',
                        '${subs.subscriptions.where((s) => s.isActive).length}',
                        textColor),
                    const SizedBox(height: 8),
                    _InfoRow(
                        'Расходы в месяц',
                        '${subs.analytics?['total_monthly']?.toStringAsFixed(0) ?? 0} ₽',
                        textColor),
                    const SizedBox(height: 8),
                    _InfoRow(
                        'Расходы в год',
                        '${subs.analytics?['total_yearly']?.toStringAsFixed(0) ?? 0} ₽',
                        textColor),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                style: OutlinedButton.styleFrom(
                  foregroundColor: AppTheme.neonPink,
                  side: const BorderSide(color: AppTheme.neonPink),
                  shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16)),
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                icon: const Icon(Icons.logout_rounded, size: 22),
                label: const Text('ВЫЙТИ',
                    style: TextStyle(
                        fontWeight: FontWeight.w900,
                        letterSpacing: 2,
                        fontSize: 15)),
                onPressed: () async {
                  await auth.logout();
                  if (context.mounted) {
                    Navigator.pushAndRemoveUntil(
                        context,
                        MaterialPageRoute(builder: (_) => const LoginScreen()),
                        (_) => false);
                  }
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  final String value, label;
  final Color accentColor, textColor;
  const _Stat(this.value, this.label, this.accentColor, this.textColor);
  @override
  Widget build(BuildContext context) => Column(children: [
        Text(value,
            style: TextStyle(
                color: accentColor, fontSize: 22, fontWeight: FontWeight.w900)),
        const SizedBox(height: 2),
        Text(label,
            style: TextStyle(
                color: textColor.withValues(alpha: 0.5),
                fontSize: 10,
                fontWeight: FontWeight.w900,
                letterSpacing: 1)),
      ]);
}

class _InfoRow extends StatelessWidget {
  final String label, value;
  final Color textColor;
  const _InfoRow(this.label, this.value, this.textColor);
  @override
  Widget build(BuildContext context) => Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label,
              style: TextStyle(
                  color: textColor.withValues(alpha: 0.5), fontSize: 13)),
          Text(value,
              style: TextStyle(
                  color: textColor, fontSize: 13, fontWeight: FontWeight.w900)),
        ],
      );
}
