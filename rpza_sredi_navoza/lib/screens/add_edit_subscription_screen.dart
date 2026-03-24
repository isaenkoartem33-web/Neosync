import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/subscription.dart';
import '../providers/subscription_provider.dart';
import '../theme/app_theme.dart';

class AddEditSubscriptionScreen extends StatefulWidget {
  final Subscription? sub;
  const AddEditSubscriptionScreen({super.key, this.sub});
  @override
  State<AddEditSubscriptionScreen> createState() => _State();
}

class _State extends State<AddEditSubscriptionScreen> {
  final _nameCtrl = TextEditingController();
  final _costCtrl = TextEditingController();
  final _notesCtrl = TextEditingController();
  final _payUrlCtrl = TextEditingController();
  String _currency = 'RUB';
  String _period = 'monthly';
  String _category = 'Other';
  DateTime _startDate = DateTime.now();
  bool _saving = false;
  String? _error;

  final _periods = {
    'weekly': 'Еженедельно',
    'monthly': 'Ежемесячно',
    'quarterly': 'Ежеквартально',
    'yearly': 'Ежегодно'
  };
  final _currencies = ['RUB', 'USD', 'EUR'];
  final _categories = ['Entertainment', 'Software', 'Education', 'Health', 'Finance', 'Other'];

  @override
  void initState() {
    super.initState();
    if (widget.sub != null) {
      final s = widget.sub!;
      _nameCtrl.text = s.name;
      _costCtrl.text = s.cost.toString();
      _notesCtrl.text = s.notes ?? '';
      _payUrlCtrl.text = s.paymentUrl ?? '';
      _currency = s.currency;
      _period = s.billingPeriod;
      _category = s.category;
      if (s.startDate.isNotEmpty) {
        try { _startDate = DateTime.parse(s.startDate); } catch (_) {}
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final isEdit = widget.sub != null;
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(title: Text(isEdit ? 'Редактировать' : 'Добавить подписку')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _Field(label: 'Название *', child: TextField(
              controller: _nameCtrl,
              decoration: const InputDecoration(hintText: 'Netflix, Spotify...'),
            )),
            const SizedBox(height: 14),

            Row(children: [
              Expanded(child: _Field(label: 'Стоимость *', child: TextField(
                controller: _costCtrl,
                keyboardType: TextInputType.number,
                decoration: const InputDecoration(hintText: '999'),
              ))),
              const SizedBox(width: 12),
              _Field(label: 'Валюта', child: SizedBox(
                width: 110,
                child: _Drop(
                  value: _currency,
                  items: _currencies,
                  onChanged: (v) => setState(() => _currency = v!),
                ),
              )),
            ]),
            const SizedBox(height: 14),

            _Field(label: 'Период', child: _Drop(
              value: _period,
              items: _periods.keys.toList(),
              labels: _periods,
              onChanged: (v) => setState(() => _period = v!),
            )),
            const SizedBox(height: 14),

            _Field(label: 'Категория', child: _Drop(
              value: _category,
              items: _categories,
              onChanged: (v) => setState(() => _category = v!),
            )),            const SizedBox(height: 14),

            _Field(label: 'Дата начала', child: InkWell(
              borderRadius: BorderRadius.circular(16),
              onTap: () async {
                final d = await showDatePicker(
                  context: context,
                  initialDate: _startDate,
                  firstDate: DateTime(2020),
                  lastDate: DateTime.now().add(const Duration(days: 365)),
                );
                if (d != null) setState(() => _startDate = d);
              },
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                decoration: BoxDecoration(
                  color: scheme.surface == Colors.white
                      ? const Color(0xFFF0F0F0)
                      : const Color(0xFF222222),
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(children: [
                  const Icon(Icons.calendar_today_rounded, size: 16, color: AppTheme.neonPurple),
                  const SizedBox(width: 8),
                  Text(
                    '${_startDate.year}-${_startDate.month.toString().padLeft(2, '0')}-${_startDate.day.toString().padLeft(2, '0')}',
                    style: TextStyle(color: scheme.onSurface),
                  ),
                ]),
              ),
            )),
            const SizedBox(height: 14),

            _Field(label: 'Ссылка на оплату', child: TextField(
              controller: _payUrlCtrl,
              decoration: const InputDecoration(hintText: 'https://...'),
            )),
            const SizedBox(height: 14),

            _Field(label: 'Заметки', child: TextField(
              controller: _notesCtrl,
              maxLines: 3,
              decoration: const InputDecoration(hintText: 'Дополнительная информация...'),
            )),

            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(top: 12),
                child: Text(_error!, style: const TextStyle(color: AppTheme.neonPink)),
              ),

            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _saving ? null : _save,
                child: _saving
                    ? const SizedBox(height: 20, width: 20,
                        child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : Text(isEdit ? 'Сохранить' : 'Добавить'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _save() async {
    if (_nameCtrl.text.trim().isEmpty || _costCtrl.text.trim().isEmpty) {
      setState(() => _error = 'Название и стоимость обязательны');
      return;
    }
    final cost = double.tryParse(_costCtrl.text.trim());
    if (cost == null || cost <= 0) {
      setState(() => _error = 'Неверная стоимость');
      return;
    }
    setState(() { _saving = true; _error = null; });

    final data = {
      'name': _nameCtrl.text.trim(),
      'cost': cost,
      'currency': _currency,
      'billing_period': _period,
      'category': _category,
      'start_date': '${_startDate.year}-${_startDate.month.toString().padLeft(2, '0')}-${_startDate.day.toString().padLeft(2, '0')}',
      'notes': _notesCtrl.text.trim(),
      'payment_url': _payUrlCtrl.text.trim().isEmpty ? null : _payUrlCtrl.text.trim(),
    };

    final provider = context.read<SubscriptionProvider>();
    final ok = widget.sub != null
        ? await provider.update(widget.sub!.id, data)
        : await provider.create(data);

    setState(() => _saving = false);
    if (ok && mounted) Navigator.pop(context);
    else setState(() => _error = 'Ошибка. Проверьте подключение к серверу.');
  }
}

class _Field extends StatelessWidget {
  final String label;
  final Widget child;
  const _Field({required this.label, required this.child});

  @override
  Widget build(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(label.toUpperCase(),
          style: TextStyle(
              color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
              fontSize: 11, fontWeight: FontWeight.w800, letterSpacing: 1.5)),
      const SizedBox(height: 6),
      child,
    ],
  );
}

class _Drop extends StatelessWidget {
  final String value;
  final List<String> items;
  final Map<String, String>? labels;
  final ValueChanged<String?> onChanged;
  const _Drop({required this.value, required this.items, this.labels, required this.onChanged});

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF222222) : const Color(0xFFF0F0F0),
        borderRadius: BorderRadius.circular(16),
      ),
      child: DropdownButton<String>(
        value: value,
        underline: const SizedBox(),
        dropdownColor: isDark ? const Color(0xFF222222) : Colors.white,
        style: TextStyle(
            color: Theme.of(context).colorScheme.onSurface,
            fontWeight: FontWeight.w600),
        items: items
            .map((e) => DropdownMenuItem(value: e, child: Text(labels?[e] ?? e)))
            .toList(),
        onChanged: onChanged,
      ),
    );
  }
}
