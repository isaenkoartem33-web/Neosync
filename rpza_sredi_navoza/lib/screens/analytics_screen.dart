import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:fl_chart/fl_chart.dart';
import '../providers/subscription_provider.dart';
import '../theme/app_theme.dart';
import '../models/subscription.dart';

class AnalyticsScreen extends StatelessWidget {
  const AnalyticsScreen({super.key});

  static const _rates = {'RUB': 1.0, 'USD': 90.0, 'EUR': 100.0};
  static const _chartColors = [
    AppTheme.neonPurple,
    AppTheme.neonPink,
    Color(0xFF00D4FF),
    Color(0xFF10B981),
    Color(0xFFFFB800),
    Color(0xFFFF6B35),
  ];

  double _monthlyRub(Subscription s) {
    final rate = _rates[s.currency] ?? 1.0;
    switch (s.billingPeriod) {
      case 'weekly': return s.cost * 52 / 12 * rate;
      case 'monthly': return s.cost * rate;
      case 'quarterly': return s.cost / 3 * rate;
      case 'yearly': return s.cost / 12 * rate;
      default: return s.cost * rate;
    }
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<SubscriptionProvider>();
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final textColor = isDark ? Colors.white : const Color(0xFF1A1A1A);
    final analytics = provider.analytics;
    final activeSubs = provider.subscriptions.where((s) => s.isActive).toList();

    // Группируем по категориям
    final Map<String, double> byCategory = {};
    for (final s in activeSubs) {
      byCategory[s.category] = (byCategory[s.category] ?? 0) + _monthlyRub(s);
    }
    final categories = byCategory.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));

    // Топ по расходам
    final sorted = List<Subscription>.from(activeSubs)
      ..sort((a, b) => _monthlyRub(b).compareTo(_monthlyRub(a)));

    return RefreshIndicator(
      color: AppTheme.neonPurple,
      onRefresh: () => provider.loadAnalytics(),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Заголовок
          Text('АНАЛИТИКА',
              style: TextStyle(
                  color: textColor, fontSize: 22, fontWeight: FontWeight.w900, letterSpacing: 2)),
          Container(
              height: 3, width: 50, color: AppTheme.neonPurple,
              margin: const EdgeInsets.only(top: 4, bottom: 16)),

          // Карточки статистики
          if (analytics != null) ...[
            GridView.count(
              crossAxisCount: 2,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              crossAxisSpacing: 10,
              mainAxisSpacing: 10,
              childAspectRatio: 1.7,
              children: [
                _StatCard('В МЕСЯЦ',
                    '${analytics['total_monthly']?.toStringAsFixed(0) ?? 0} ₽',
                    AppTheme.neonPurple, textColor),
                _StatCard('В ГОД',
                    '${analytics['total_yearly']?.toStringAsFixed(0) ?? 0} ₽',
                    AppTheme.neonPink, textColor),
                _StatCard('ПОДПИСОК',
                    '${analytics['subscription_count'] ?? 0}',
                    AppTheme.neonPurple, textColor),
                _StatCard('СРЕДНЕЕ',
                    '${analytics['average_monthly']?.toStringAsFixed(0) ?? 0} ₽',
                    AppTheme.neonPink, textColor),
              ],
            ),
            const SizedBox(height: 20),
          ],

          // Круговая диаграмма по категориям
          if (categories.isNotEmpty) ...[
            _SectionTitle('РАСХОДЫ ПО КАТЕГОРИЯМ', textColor),
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    SizedBox(
                      height: 200,
                      child: PieChart(
                        PieChartData(
                          sections: categories.asMap().entries.map((e) {
                            final color = _chartColors[e.key % _chartColors.length];
                            final total = categories.fold(0.0, (s, c) => s + c.value);
                            final pct = total > 0 ? e.value.value / total * 100 : 0;
                            return PieChartSectionData(
                              color: color,
                              value: e.value.value,
                              title: '${pct.toStringAsFixed(0)}%',
                              radius: 70,
                              titleStyle: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 12,
                                  fontWeight: FontWeight.w800),
                            );
                          }).toList(),
                          sectionsSpace: 2,
                          centerSpaceRadius: 40,
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                    // Легенда
                    Wrap(
                      spacing: 12,
                      runSpacing: 8,
                      children: categories.asMap().entries.map((e) {
                        final color = _chartColors[e.key % _chartColors.length];
                        return Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Container(
                                width: 10, height: 10,
                                decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
                            const SizedBox(width: 4),
                            Text(e.value.key,
                                style: TextStyle(
                                    color: textColor, fontSize: 12, fontWeight: FontWeight.w600)),
                            const SizedBox(width: 4),
                            Text('${e.value.value.toStringAsFixed(0)} ₽',
                                style: TextStyle(
                                    color: textColor.withValues(alpha: 0.5), fontSize: 11)),
                          ],
                        );
                      }).toList(),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 20),
          ],

          // Столбчатая диаграмма — топ подписок
          if (sorted.isNotEmpty) ...[
            _SectionTitle('ТОП ПОДПИСОК ПО РАСХОДАМ', textColor),
            const SizedBox(height: 12),
            Card(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(8, 16, 16, 8),
                child: SizedBox(
                  height: 200,
                  child: BarChart(
                    BarChartData(
                      alignment: BarChartAlignment.spaceAround,
                      maxY: _monthlyRub(sorted.first) * 1.2,
                      barTouchData: BarTouchData(
                        touchTooltipData: BarTouchTooltipData(
                          getTooltipItem: (group, groupIndex, rod, rodIndex) {
                            final sub = sorted[groupIndex];
                            return BarTooltipItem(
                              '${sub.name}\n${rod.toY.toStringAsFixed(0)} ₽',
                              const TextStyle(color: Colors.white, fontSize: 11),
                            );
                          },
                        ),
                      ),
                      titlesData: FlTitlesData(
                        bottomTitles: AxisTitles(
                          sideTitles: SideTitles(
                            showTitles: true,
                            getTitlesWidget: (value, meta) {
                              final i = value.toInt();
                              if (i >= sorted.length) return const SizedBox();
                              final name = sorted[i].name;
                              return Padding(
                                padding: const EdgeInsets.only(top: 4),
                                child: Text(
                                  name.length > 6 ? '${name.substring(0, 6)}..' : name,
                                  style: TextStyle(
                                      color: textColor.withValues(alpha: 0.6),
                                      fontSize: 10),
                                ),
                              );
                            },
                          ),
                        ),
                        leftTitles: AxisTitles(
                          sideTitles: SideTitles(
                            showTitles: true,
                            reservedSize: 40,
                            getTitlesWidget: (value, meta) => Text(
                              '${value.toInt()}',
                              style: TextStyle(
                                  color: textColor.withValues(alpha: 0.4), fontSize: 9),
                            ),
                          ),
                        ),
                        topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                        rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
                      ),
                      gridData: FlGridData(
                        getDrawingHorizontalLine: (value) => FlLine(
                          color: textColor.withValues(alpha: 0.08),
                          strokeWidth: 1,
                        ),
                      ),
                      borderData: FlBorderData(show: false),
                      barGroups: sorted.take(6).toList().asMap().entries.map((e) {
                        final color = _chartColors[e.key % _chartColors.length];
                        return BarChartGroupData(
                          x: e.key,
                          barRods: [
                            BarChartRodData(
                              toY: _monthlyRub(e.value),
                              color: color,
                              width: 20,
                              borderRadius: const BorderRadius.vertical(top: Radius.circular(6)),
                            ),
                          ],
                        );
                      }).toList(),
                    ),
                  ),
                ),
              ),
            ),
            const SizedBox(height: 20),
          ],

          // Список топ расходов
          _SectionTitle('ТОП РАСХОДОВ', textColor),
          const SizedBox(height: 10),
          ...sorted.take(10).toList().asMap().entries.map(
            (e) => _TopItem(rank: e.key + 1, sub: e.value, textColor: textColor,
                monthlyRub: _monthlyRub(e.value)),
          ),

          if (activeSubs.isEmpty)
            Center(
              child: Padding(
                padding: const EdgeInsets.all(32),
                child: Text('Нет данных',
                    style: TextStyle(color: textColor.withValues(alpha: 0.4))),
              ),
            ),
        ],
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String text;
  final Color color;
  const _SectionTitle(this.text, this.color);
  @override
  Widget build(BuildContext context) => Text(text,
      style: TextStyle(
          color: color.withValues(alpha: 0.6),
          fontSize: 11, fontWeight: FontWeight.w900, letterSpacing: 2));
}

class _StatCard extends StatelessWidget {
  final String label, value;
  final Color accentColor, textColor;
  const _StatCard(this.label, this.value, this.accentColor, this.textColor);

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: accentColor.withValues(alpha: 0.4)),
        color: isDark ? AppTheme.cardDark : AppTheme.cardLight,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label,
              style: TextStyle(
                  color: textColor.withValues(alpha: 0.5),
                  fontSize: 10, fontWeight: FontWeight.w900, letterSpacing: 1.5)),
          Text(value,
              style: TextStyle(
                  color: accentColor, fontSize: 20, fontWeight: FontWeight.w900)),
        ],
      ),
    );
  }
}

class _TopItem extends StatelessWidget {
  final int rank;
  final Subscription sub;
  final Color textColor;
  final double monthlyRub;
  const _TopItem(
      {required this.rank, required this.sub, required this.textColor, required this.monthlyRub});

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: textColor.withValues(alpha: 0.1)),
      ),
      child: Row(
        children: [
          Text('$rank',
              style: const TextStyle(
                  color: AppTheme.neonPurple, fontSize: 18, fontWeight: FontWeight.w900)),
          const SizedBox(width: 12),
          Expanded(
              child: Text(sub.name,
                  style: TextStyle(color: textColor, fontWeight: FontWeight.w700))),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text('${monthlyRub.toStringAsFixed(0)} ₽/мес',
                  style: const TextStyle(
                      color: AppTheme.neonPink, fontWeight: FontWeight.w900, fontSize: 13)),
              Text(sub.periodLabel,
                  style: TextStyle(color: textColor.withValues(alpha: 0.4), fontSize: 11)),
            ],
          ),
        ],
      ),
    );
  }
}
