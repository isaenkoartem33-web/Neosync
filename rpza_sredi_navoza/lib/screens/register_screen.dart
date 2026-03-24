import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/auth_provider.dart';
import '../theme/app_theme.dart';
import 'verify_email_screen.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});
  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _nameCtrl = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  bool _obscure = true;

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = isDark ? Colors.white : const Color(0xFF1A1A1A);

    return Scaffold(
      appBar: AppBar(title: const Text('РЕГИСТРАЦИЯ')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('СОЗДАТЬ АККАУНТ', style: TextStyle(
                color: textColor, fontSize: 28, fontWeight: FontWeight.w900, letterSpacing: 2,
              )),
              Container(height: 3, width: 60, color: AppTheme.neonPink, margin: const EdgeInsets.only(top: 8, bottom: 32)),

              _label('ИМЯ', textColor),
              const SizedBox(height: 6),
              TextField(controller: _nameCtrl, style: TextStyle(color: textColor), decoration: const InputDecoration(hintText: 'Ваше имя')),
              const SizedBox(height: 16),

              _label('EMAIL', textColor),
              const SizedBox(height: 6),
              TextField(controller: _emailCtrl, keyboardType: TextInputType.emailAddress, style: TextStyle(color: textColor), decoration: const InputDecoration(hintText: 'user@example.com')),
              const SizedBox(height: 16),

              _label('ПАРОЛЬ', textColor),
              const SizedBox(height: 6),
              TextField(
                controller: _passCtrl,
                obscureText: _obscure,
                style: TextStyle(color: textColor),
                decoration: InputDecoration(
                  hintText: '••••••••',
                  suffixIcon: IconButton(
                    icon: Icon(_obscure ? Icons.visibility_off : Icons.visibility, color: AppTheme.neonPurple),
                    onPressed: () => setState(() => _obscure = !_obscure),
                  ),
                ),
              ),

              if (auth.error != null)
                Padding(
                  padding: const EdgeInsets.only(top: 12),
                  child: Text(auth.error!, style: const TextStyle(color: AppTheme.neonPink, fontSize: 13)),
                ),

              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: auth.loading ? null : () async {
                    final ok = await auth.register(_emailCtrl.text.trim(), _passCtrl.text, _nameCtrl.text.trim());
                    if (ok && context.mounted) {
                      Navigator.pushReplacement(
                        context,
                        MaterialPageRoute(builder: (_) => VerifyEmailScreen(email: _emailCtrl.text.trim())),
                      );
                    }
                  },
                  child: auth.loading
                      ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                      : const Text('ЗАРЕГИСТРИРОВАТЬСЯ'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _label(String text, Color color) => Text(text, style: TextStyle(color: color.withOpacity(0.6), fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: 2));
}
