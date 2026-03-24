class Subscription {
  final String id;
  final String name;
  final double cost;
  final String currency;
  final String billingPeriod;
  final String startDate;
  final String nextBillingDate;
  final String category;
  final String? notes;
  final bool isActive;
  final String? paymentUrl;
  final bool manuallyAdded;

  Subscription({
    required this.id,
    required this.name,
    required this.cost,
    required this.currency,
    required this.billingPeriod,
    required this.startDate,
    required this.nextBillingDate,
    required this.category,
    this.notes,
    required this.isActive,
    this.paymentUrl,
    required this.manuallyAdded,
  });

  factory Subscription.fromJson(Map<String, dynamic> j) => Subscription(
        id: j['id'],
        name: j['name'],
        cost: (j['cost'] as num).toDouble(),
        currency: j['currency'] ?? 'RUB',
        billingPeriod: j['billing_period'],
        startDate: j['start_date'] ?? '',
        nextBillingDate: j['next_billing_date'] ?? '',
        category: j['category'] ?? 'Other',
        notes: j['notes'],
        isActive: j['is_active'] ?? true,
        paymentUrl: j['payment_url'],
        manuallyAdded: j['manually_added'] ?? false,
      );

  Map<String, dynamic> toJson() => {
        'name': name,
        'cost': cost,
        'currency': currency,
        'billing_period': billingPeriod,
        'start_date': startDate,
        'category': category,
        'notes': notes ?? '',
        'payment_url': paymentUrl,
        'is_active': isActive,
      };

  String get periodLabel {
    switch (billingPeriod) {
      case 'weekly': return 'Еженедельно';
      case 'monthly': return 'Ежемесячно';
      case 'quarterly': return 'Ежеквартально';
      case 'yearly': return 'Ежегодно';
      default: return billingPeriod;
    }
  }

  String get currencySymbol {
    switch (currency) {
      case 'RUB': return '₽';
      case 'USD': return '\$';
      case 'EUR': return '€';
      default: return currency;
    }
  }
}
