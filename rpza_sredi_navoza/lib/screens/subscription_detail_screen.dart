import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import '../models/subscription.dart';
import '../theme/app_theme.dart';
import 'add_edit_subscription_screen.dart';

class SubscriptionDetailScreen extends StatelessWidget {
  final Subscription sub;
  const SubscriptionDetailScreen({super.key, required this.sub});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = isDark ? Colors.white : const Color(0xFF1A1A1A);
    final mutedColor = textColor.withOpacity(0.5);

    return Scaffold(
      appBar: AppBar(
        title: Text(sub.name.toUpperCase()),
        actions: [
          IconButton(
            icon: const Icon(Icons.edit),
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => AddEditSubscriptionScreen(sub: sub))),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Цена
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(border: Border.all(color: AppTheme.neonPurple)),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(sub.name, style: TextStyle(color: textColor, fontSize: 22, fontWeight: FontWeight.w900)),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                        color: AppTheme.neonPurple,
                        child: Text(sub.category, style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w900)),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Text('${sub.cost.toStringAsFixed(sub.cost % 1 == 0 ? 0 : 2)}${sub.currencySymbol}',
                          style: const TextStyle(color: AppTheme.neonPink, fontSize: 40, fontWeight: FontWeight.w900)),
                      const SizedBox(width: 8),
                      Padding(
                        padding: const EdgeInsets.only(bottom: 6),
                        child: Text('/ ${sub.periodLabel}', style: TextStyle(color: mutedColor, fontSize: 14)),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),

            // Детали
            _DetailCard(children: [
              _Row('Дата начала', sub.startDate, textColor, mutedColor),
              _Divider(),
              _Row('Следующее списание', sub.nextBillingDate, textColor, mutedColor, valueColor: AppTheme.neonPurple),
              _Divider(),
              _Row('Статус', sub.isActive ? 'Активна' : 'Неактивна', textColor, mutedColor,
                  valueColor: sub.isActive ? const Color(0xFF10B981) : AppTheme.neonPink),
              _Divider(),
              _Row('Валюта', sub.currency, textColor, mutedColor),
            ]),
            const SizedBox(height: 12),

            if (sub.notes != null && sub.notes!.isNotEmpty) ...[
              _SectionTitle('ЗАМЕТКИ', textColor),
              const SizedBox(height: 8),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(border: Border.all(color: textColor.withOpacity(0.15))),
                child: Text(sub.notes!, style: TextStyle(color: textColor, fontSize: 14)),
              ),
              const SizedBox(height: 12),
            ],

            // Кнопки
            if (sub.paymentUrl != null && sub.paymentUrl!.isNotEmpty)
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF10B981)),
                  icon: const Icon(Icons.credit_card),
                  label: const Text('ОПЛАТИТЬ'),
                  onPressed: () async {
                    final uri = Uri.parse(sub.paymentUrl!);
                    if (await canLaunchUrl(uri)) launchUrl(uri, mode: LaunchMode.externalApplication);
                  },
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _DetailCard extends StatelessWidget {
  final List<Widget> children;
  const _DetailCard({required this.children});
  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      decoration: BoxDecoration(border: Border.all(color: isDark ? Colors.white12 : Colors.black12)),
      child: Column(children: children),
    );
  }
}

class _Row extends StatelessWidget {
  final String label, value;
  final Color textColor, mutedColor;
  final Color? valueColor;
  const _Row(this.label, this.value, this.textColor, this.mutedColor, {this.valueColor});
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
    child: Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(label, style: TextStyle(color: mutedColor, fontSize: 12, fontWeight: FontWeight.w700, letterSpacing: 1)),
        Text(value, style: TextStyle(color: valueColor ?? textColor, fontSize: 14, fontWeight: FontWeight.w900)),
      ],
    ),
  );
}

class _Divider extends StatelessWidget {
  @override
  Widget build(BuildContext context) => Divider(height: 1, color: Theme.of(context).brightness == Brightness.dark ? Colors.white10 : const Color(0x1A000000));
}

class _SectionTitle extends StatelessWidget {
  final String text;
  final Color color;
  const _SectionTitle(this.text, this.color);
  @override
  Widget build(BuildContext context) => Text(text, style: TextStyle(color: color.withOpacity(0.6), fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: 2));
}
