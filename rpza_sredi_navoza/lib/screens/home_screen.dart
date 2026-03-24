import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/subscription_provider.dart';
import '../providers/theme_provider.dart';
import '../theme/app_theme.dart';
import '../models/subscription.dart';
import 'add_edit_subscription_screen.dart';
import 'subscription_detail_screen.dart';
import 'analytics_screen.dart';
import 'profile_screen.dart';
import 'email_import_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _tab = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<SubscriptionProvider>().load();
    });
  }

  @override
  Widget build(BuildContext context) {
    final isDark = context.watch<ThemeProvider>().isDark;

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              width: 30, height: 30,
              decoration: BoxDecoration(
                color: AppTheme.neonPurple.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.bolt, color: AppTheme.neonPurple, size: 18),
            ),
            const SizedBox(width: 10),
            const Text('NEOSYNC'),
          ],
        ),
        actions: [
          // Переключатель темы
          SizedBox(
            width: 52, height: 52,
            child: IconButton(
              iconSize: 28,
              icon: Icon(
                isDark ? Icons.light_mode_rounded : Icons.dark_mode_rounded,
                color: AppTheme.neonPurple,
              ),
              onPressed: () => context.read<ThemeProvider>().toggle(),
            ),
          ),
          // Профиль — крупнее
          SizedBox(
            width: 52, height: 52,
            child: IconButton(
              iconSize: 28,
              icon: const Icon(Icons.person_rounded),
              onPressed: () => Navigator.push(context,
                  MaterialPageRoute(builder: (_) => const ProfileScreen())),
            ),
          ),
        ],
      ),
      body: IndexedStack(
        index: _tab,
        children: const [
          _SubscriptionsTab(),
          AnalyticsScreen(),
          EmailImportScreen(),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _tab,
        onTap: (i) => setState(() => _tab = i),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.credit_card_rounded), label: 'Подписки'),
          BottomNavigationBarItem(icon: Icon(Icons.bar_chart_rounded), label: 'Аналитика'),
          BottomNavigationBarItem(icon: Icon(Icons.mail_rounded), label: 'Импорт'),
        ],
      ),
      floatingActionButton: _tab == 0
          ? FloatingActionButton(
              backgroundColor: AppTheme.neonPink,
              shape: const CircleBorder(),
              onPressed: () => Navigator.push(context,
                  MaterialPageRoute(builder: (_) => const AddEditSubscriptionScreen())),
              child: const Icon(Icons.add, color: Colors.white, size: 28),
            )
          : null,
    );
  }
}

class _SubscriptionsTab extends StatelessWidget {
  const _SubscriptionsTab();

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<SubscriptionProvider>();

    if (provider.loading) {
      return const Center(child: CircularProgressIndicator(color: AppTheme.neonPurple));
    }

    if (provider.subscriptions.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: AppTheme.neonPurple.withValues(alpha: 0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.inbox_rounded, size: 48, color: AppTheme.neonPurple),
            ),
            const SizedBox(height: 16),
            Text('Подписок пока нет',
                style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w900)),
            const SizedBox(height: 8),
            Text('Нажмите + чтобы добавить',
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(color: Colors.grey)),
          ],
        ),
      );
    }

    return RefreshIndicator(
      color: AppTheme.neonPurple,
      onRefresh: () => provider.load(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: provider.subscriptions.length,
        itemBuilder: (ctx, i) => _SubscriptionCard(sub: provider.subscriptions[i]),
      ),
    );
  }
}

class _SubscriptionCard extends StatelessWidget {
  final Subscription sub;
  const _SubscriptionCard({required this.sub});

  @override
  Widget build(BuildContext context) {
    final provider = context.read<SubscriptionProvider>();
    final textColor = Theme.of(context).colorScheme.onSurface;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: () => Navigator.push(context,
            MaterialPageRoute(builder: (_) => SubscriptionDetailScreen(sub: sub))),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(sub.name,
                        style: TextStyle(
                            color: textColor, fontSize: 17, fontWeight: FontWeight.w800)),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppTheme.neonPurple.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(sub.category,
                        style: const TextStyle(
                            color: AppTheme.neonPurple, fontSize: 11, fontWeight: FontWeight.w700)),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Text(
                    '${sub.cost.toStringAsFixed(sub.cost % 1 == 0 ? 0 : 2)}${sub.currencySymbol}',
                    style: const TextStyle(
                        color: AppTheme.neonPink, fontSize: 26, fontWeight: FontWeight.w900),
                  ),
                  const SizedBox(width: 6),
                  Padding(
                    padding: const EdgeInsets.only(bottom: 3),
                    child: Text('/ ${sub.periodLabel}',
                        style: TextStyle(color: textColor.withValues(alpha: 0.5), fontSize: 13)),
                  ),
                ],
              ),
              const SizedBox(height: 6),
              Row(
                children: [
                  Icon(Icons.calendar_today_rounded, size: 13, color: textColor.withValues(alpha: 0.4)),
                  const SizedBox(width: 4),
                  Text('Следующее: ',
                      style: TextStyle(color: textColor.withValues(alpha: 0.5), fontSize: 12)),
                  Text(sub.nextBillingDate,
                      style: TextStyle(
                          color: textColor, fontSize: 12, fontWeight: FontWeight.w700)),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  if (sub.paymentUrl != null && sub.paymentUrl!.isNotEmpty)
                    _Chip(
                      label: 'Оплатить',
                      icon: Icons.credit_card_rounded,
                      color: const Color(0xFF10B981),
                      onTap: () {},
                    ),
                  if (sub.paymentUrl != null && sub.paymentUrl!.isNotEmpty)
                    const SizedBox(width: 8),
                  _Chip(
                    label: 'Изменить',
                    icon: Icons.edit_rounded,
                    color: AppTheme.neonPurple,
                    onTap: () => Navigator.push(context,
                        MaterialPageRoute(builder: (_) => AddEditSubscriptionScreen(sub: sub))),
                  ),
                  const SizedBox(width: 8),
                  _Chip(
                    label: '',
                    icon: Icons.delete_rounded,
                    color: AppTheme.neonPink,
                    onTap: () async {
                      final ok = await showDialog<bool>(
                        context: context,
                        builder: (_) => AlertDialog(
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                          title: const Text('Удалить?'),
                          content: Text('${sub.name} будет удалена'),
                          actions: [
                            TextButton(
                                onPressed: () => Navigator.pop(context, false),
                                child: const Text('Отмена')),
                            TextButton(
                                onPressed: () => Navigator.pop(context, true),
                                child: const Text('Удалить',
                                    style: TextStyle(color: AppTheme.neonPink))),
                          ],
                        ),
                      );
                      if (ok == true) provider.delete(sub.id);
                    },
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  final String label;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;
  const _Chip({required this.label, required this.icon, required this.color, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(24),
      child: Container(
        padding: EdgeInsets.symmetric(horizontal: label.isEmpty ? 14 : 16, vertical: 10),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(24),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 18, color: color),
            if (label.isNotEmpty) ...[
              const SizedBox(width: 6),
              Text(label, style: TextStyle(color: color, fontSize: 13, fontWeight: FontWeight.w700)),
            ],
          ],
        ),
      ),
    );
  }
}
