import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../api/api_client.dart';
import '../providers/subscription_provider.dart';
import '../theme/app_theme.dart';

class EmailImportScreen extends StatefulWidget {
  const EmailImportScreen({super.key});
  @override
  State<EmailImportScreen> createState() => _State();
}

class _State extends State<EmailImportScreen> {
  final _emailCtrl = TextEditingController();
  final _passCtrl = TextEditingController();
  String _provider = 'mailru';
  bool _loading = false;
  bool _obscure = true;
  String? _error;

  List<Map<String, dynamic>> _found = [];
  Set<int> _selected = {};
  bool _importing = false;
  bool _done = false;
  int _importedCount = 0;

  bool get _isStep2 => _found.isNotEmpty;
  final _providers = {'mailru': 'Mail.ru', 'yandex': 'Yandex'};

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_isStep2 ? 'Выберите подписки' : 'Импорт из почты'),
        leading: _isStep2
            ? IconButton(
                icon: const Icon(Icons.arrow_back_rounded),
                onPressed: () => setState(() {
                  _found = [];
                  _selected = {};
                  _error = null;
                }),
              )
            : null,
      ),
      body: _isStep2 ? _buildStep2() : _buildStep1(),
    );
  }

  Widget _buildStep1() {
    final scheme = Theme.of(context).colorScheme;
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppTheme.neonPurple.withValues(alpha: 0.1),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppTheme.neonPurple.withValues(alpha: 0.3)),
            ),
            child: Row(children: [
              const Icon(Icons.info_outline_rounded, color: AppTheme.neonPurple),
              const SizedBox(width: 12),
              Expanded(child: Text(
                'Приложение найдёт письма о подписках и покажет их вам. Вы сами выберете что добавить.',
                style: TextStyle(color: scheme.onSurface, fontSize: 13),
              )),
            ]),
          ),
          const SizedBox(height: 20),

          _label('ПОЧТОВЫЙ СЕРВИС'),
          const SizedBox(height: 8),
          Row(
            children: _providers.entries.map((e) {
              final sel = _provider == e.key;
              return Padding(
                padding: const EdgeInsets.only(right: 10),
                child: InkWell(
                  onTap: () => setState(() => _provider = e.key),
                  borderRadius: BorderRadius.circular(12),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                    decoration: BoxDecoration(
                      color: sel ? AppTheme.neonPurple : Colors.transparent,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: sel ? AppTheme.neonPurple : scheme.onSurface.withValues(alpha: 0.2),
                      ),
                    ),
                    child: Text(e.value,
                        style: TextStyle(
                            color: sel ? Colors.white : scheme.onSurface,
                            fontWeight: FontWeight.w700)),
                  ),
                ),
              );
            }).toList(),
          ),
          const SizedBox(height: 16),

          _label('EMAIL'),
          const SizedBox(height: 8),
          TextField(
            controller: _emailCtrl,
            keyboardType: TextInputType.emailAddress,
            decoration: InputDecoration(
              hintText: _provider == 'mailru' ? 'user@mail.ru' : 'user@yandex.ru',
            ),
          ),
          const SizedBox(height: 16),

          _label('ПАРОЛЬ ПРИЛОЖЕНИЯ'),
          const SizedBox(height: 8),
          TextField(
            controller: _passCtrl,
            obscureText: _obscure,
            decoration: InputDecoration(
              hintText: '••••••••••••••••',
              suffixIcon: IconButton(
                icon: Icon(_obscure ? Icons.visibility_off : Icons.visibility,
                    color: AppTheme.neonPurple),
                onPressed: () => setState(() => _obscure = !_obscure),
              ),
            ),
          ),
          const SizedBox(height: 16),

          // КНОПКА — теперь перед инструкцией
          if (_error != null) ...[
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: AppTheme.neonPink.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.neonPink.withValues(alpha: 0.4)),
              ),
              child: Row(children: [
                const Icon(Icons.error_rounded, color: AppTheme.neonPink, size: 18),
                const SizedBox(width: 8),
                Expanded(child: Text(_error!, style: TextStyle(color: scheme.onSurface, fontSize: 13))),
              ]),
            ),
            const SizedBox(height: 12),
          ],
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _loading ? null : _scan,
              icon: _loading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                  : const Icon(Icons.search_rounded),
              label: Text(_loading ? 'Сканирую почту (1-2 мин)...' : 'Найти подписки'),
            ),
          ),
          const SizedBox(height: 16),

          // ИНСТРУКЦИЯ — теперь после кнопки
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: scheme.onSurface.withValues(alpha: 0.04),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppTheme.neonPurple.withValues(alpha: 0.2)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(children: [
                  Icon(Icons.shield_rounded, color: AppTheme.neonPurple, size: 16),
                  SizedBox(width: 8),
                  Text('Как создать пароль приложения',
                      style: TextStyle(
                          color: AppTheme.neonPurple,
                          fontSize: 13,
                          fontWeight: FontWeight.w800)),
                ]),
                const SizedBox(height: 10),
                if (_provider == 'mailru') ...[
                  const _Step('1', 'Откройте mail.ru → Настройки аккаунта'),
                  const _Step('2', 'Перейдите в раздел "Безопасность"'),
                  const _Step('3', 'Найдите "Пароли для внешних приложений"'),
                  const _Step('4', 'Нажмите "Добавить" и введите название (например NeoSync)'),
                  const _Step('5', 'Скопируйте сгенерированный пароль и вставьте выше'),
                ] else ...[
                  const _Step('1', 'Откройте почту Яндекс → Настройки (шестерёнка вверху)'),
                  const _Step('2', 'Выберите "Все настройки" → "Почтовые программы"'),
                  const _Step('3', 'Включите "С сервера imap.yandex.ru" и сохраните'),
                  const _Step('4', 'Откройте id.yandex.ru → Безопасность → "Пароли приложений"'),
                  const _Step('5', 'Создайте пароль с типом "Почта", скопируйте и вставьте выше'),
                ],
                const SizedBox(height: 8),
                const Text(
                    '⚠ Сначала включите IMAP в настройках Яндекс почты, иначе подключение не работает',
                    style: TextStyle(
                        color: AppTheme.neonPink,
                        fontSize: 11,
                        fontWeight: FontWeight.w600)),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStep2() {
    final scheme = Theme.of(context).colorScheme;

    if (_done) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: const Color(0xFF10B981).withValues(alpha: 0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.check_circle_rounded,
                  color: Color(0xFF10B981), size: 64),
            ),
            const SizedBox(height: 20),
            Text('Готово!',
                style: TextStyle(
                    color: scheme.onSurface,
                    fontSize: 28,
                    fontWeight: FontWeight.w900)),
            const SizedBox(height: 8),
            Text('Добавлено подписок: $_importedCount',
                style: const TextStyle(
                    color: Color(0xFF10B981),
                    fontSize: 16,
                    fontWeight: FontWeight.w700)),
            const SizedBox(height: 32),
            ElevatedButton(
              onPressed: () =>
                  setState(() { _found = []; _selected = {}; _done = false; }),
              child: const Text('Импортировать ещё'),
            ),
          ],
        ),
      );
    }

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
          child: Row(
            children: [
              Text('Найдено: ${_found.length}',
                  style: TextStyle(
                      color: scheme.onSurface.withValues(alpha: 0.6),
                      fontSize: 13)),
              const Spacer(),
              TextButton(
                onPressed: () => setState(() =>
                    _selected = Set.from(List.generate(_found.length, (i) => i))),
                child: const Text('Выбрать все',
                    style: TextStyle(
                        color: AppTheme.neonPurple,
                        fontWeight: FontWeight.w700)),
              ),
              TextButton(
                onPressed: () => setState(() => _selected = {}),
                child: Text('Снять',
                    style: TextStyle(
                        color: scheme.onSurface.withValues(alpha: 0.5),
                        fontWeight: FontWeight.w700)),
              ),
            ],
          ),
        ),
        Expanded(
          child: ListView.builder(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            itemCount: _found.length,
            itemBuilder: (ctx, i) {
              final sub = _found[i];
              final selected = _selected.contains(i);
              return AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                margin: const EdgeInsets.only(bottom: 10),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(
                    color: selected
                        ? AppTheme.neonPurple
                        : scheme.onSurface.withValues(alpha: 0.1),
                    width: selected ? 2 : 1,
                  ),
                  color: selected
                      ? AppTheme.neonPurple.withValues(alpha: 0.08)
                      : scheme.surface,
                ),
                child: InkWell(
                  borderRadius: BorderRadius.circular(16),
                  onTap: () => setState(() {
                    if (selected) {
                      _selected.remove(i);
                    } else {
                      _selected.add(i);
                    }
                  }),
                  child: Padding(
                    padding: const EdgeInsets.all(14),
                    child: Row(
                      children: [
                        AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          width: 24,
                          height: 24,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: selected
                                ? AppTheme.neonPurple
                                : Colors.transparent,
                            border: Border.all(
                              color: selected
                                  ? AppTheme.neonPurple
                                  : scheme.onSurface.withValues(alpha: 0.3),
                              width: 2,
                            ),
                          ),
                          child: selected
                              ? const Icon(Icons.check_rounded,
                                  color: Colors.white, size: 14)
                              : null,
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(sub['name'] ?? '—',
                                  style: TextStyle(
                                      color: scheme.onSurface,
                                      fontSize: 15,
                                      fontWeight: FontWeight.w800)),
                              const SizedBox(height: 2),
                              Text(
                                '${sub['cost']} ${sub['currency'] ?? 'RUB'} · ${_periodLabel(sub['billing_period'])}',
                                style: TextStyle(
                                    color: scheme.onSurface.withValues(alpha: 0.5),
                                    fontSize: 12),
                              ),
                            ],
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: AppTheme.neonPurple.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(20),
                          ),
                          child: Text(sub['category'] ?? 'Other',
                              style: const TextStyle(
                                  color: AppTheme.neonPurple,
                                  fontSize: 10,
                                  fontWeight: FontWeight.w700)),
                        ),
                      ],
                    ),
                  ),
                ),
              );
            },
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: (_selected.isEmpty || _importing) ? null : _importSelected,
              icon: _importing
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                          color: Colors.white, strokeWidth: 2))
                  : const Icon(Icons.add_rounded),
              label: Text(_importing
                  ? 'Добавляю...'
                  : 'Добавить выбранные (${_selected.length})'),
            ),
          ),
        ),
      ],
    );
  }

  String _periodLabel(String? p) {
    switch (p) {
      case 'weekly':
        return 'Еженедельно';
      case 'monthly':
        return 'Ежемесячно';
      case 'quarterly':
        return 'Ежеквартально';
      case 'yearly':
        return 'Ежегодно';
      default:
        return p ?? 'Ежемесячно';
    }
  }

  Widget _label(String text) => Text(text,
      style: TextStyle(
          color: Theme.of(context).colorScheme.onSurface.withValues(alpha: 0.5),
          fontSize: 11,
          fontWeight: FontWeight.w800,
          letterSpacing: 1.5));

  Future<void> _scan() async {
    if (_emailCtrl.text.trim().isEmpty || _passCtrl.text.isEmpty) {
      setState(() => _error = 'Заполните email и пароль');
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    final res =
        await ApiClient.scanEmail(_provider, _emailCtrl.text.trim(), _passCtrl.text);
    if (!mounted) return;
    setState(() => _loading = false);
    if (res['status'] == 200) {
      final subs =
          List<Map<String, dynamic>>.from(res['data']['subscriptions'] ?? []);
      if (subs.isEmpty) {
        setState(() =>
            _error = 'Подписок не найдено. Попробуйте другой почтовый ящик.');
      } else {
        setState(() {
          _found = subs;
          _selected = Set.from(List.generate(subs.length, (i) => i));
        });
      }
    } else {
      setState(() => _error = res['data']['error'] ?? 'Ошибка сканирования');
    }
  }

  Future<void> _importSelected() async {
    if (_selected.isEmpty) return;
    setState(() => _importing = true);
    final toImport = _selected.map((i) => _found[i]).toList();
    final res = await ApiClient.importSubscriptions(toImport);
    setState(() => _importing = false);
    if (res['status'] == 200) {
      final count = res['data']['imported_count'] ?? 0;
      if (mounted) await context.read<SubscriptionProvider>().load();
      setState(() {
        _done = true;
        _importedCount = count;
      });
    } else {
      setState(() => _error = res['data']['error'] ?? 'Ошибка импорта');
    }
  }
}

class _Step extends StatelessWidget {
  final String number, text;
  const _Step(this.number, this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 20,
            height: 20,
            margin: const EdgeInsets.only(right: 8, top: 1),
            decoration: const BoxDecoration(
                color: AppTheme.neonPurple, shape: BoxShape.circle),
            child: Center(
              child: Text(number,
                  style: const TextStyle(
                      color: Colors.white,
                      fontSize: 11,
                      fontWeight: FontWeight.w900)),
            ),
          ),
          Expanded(
              child: Text(text,
                  style: TextStyle(
                      color: Theme.of(context).colorScheme.onSurface,
                      fontSize: 12))),
        ],
      ),
    );
  }
}
