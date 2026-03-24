import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'providers/auth_provider.dart';
import 'providers/subscription_provider.dart';
import 'providers/theme_provider.dart';
import 'theme/app_theme.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => ThemeProvider()),
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => SubscriptionProvider()),
      ],
      child: const NeoSyncApp(),
    ),
  );
}

class NeoSyncApp extends StatefulWidget {
  const NeoSyncApp({super.key});
  @override
  State<NeoSyncApp> createState() => _NeoSyncAppState();
}

class _NeoSyncAppState extends State<NeoSyncApp> {
  bool _initialized = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _init());
  }

  Future<void> _init() async {
    await context.read<AuthProvider>().tryAutoLogin();
    if (mounted) setState(() => _initialized = true);
  }

  @override
  Widget build(BuildContext context) {
    final themeProvider = context.watch<ThemeProvider>();
    final auth = context.watch<AuthProvider>();

    if (!_initialized) {
      return MaterialApp(
        theme: AppTheme.dark(),
        home: const Scaffold(
          body: Center(child: CircularProgressIndicator(color: AppTheme.neonPurple)),
        ),
      );
    }

    return MaterialApp(
      title: 'NeoSync',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      themeMode: themeProvider.mode,
      home: auth.isAuthenticated ? const HomeScreen() : const LoginScreen(),
    );
  }
}
