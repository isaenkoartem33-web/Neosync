import 'package:flutter/material.dart';
import '../api/api_client.dart';
import '../models/subscription.dart';

class SubscriptionProvider extends ChangeNotifier {
  List<Subscription> _subscriptions = [];
  Map<String, dynamic>? _analytics;
  bool _loading = false;

  List<Subscription> get subscriptions => _subscriptions;
  Map<String, dynamic>? get analytics => _analytics;
  bool get loading => _loading;

  Future<void> load() async {
    _loading = true;
    notifyListeners();
    final data = await ApiClient.getSubscriptions();
    _subscriptions = data.map((j) => Subscription.fromJson(j)).toList();
    _loading = false;
    notifyListeners();
    loadAnalytics();
  }

  Future<void> loadAnalytics() async {
    _analytics = await ApiClient.getAnalyticsSummary();
    notifyListeners();
  }
  Future<bool> create(Map<String, dynamic> data) async {
    final result = await ApiClient.createSubscription(data);
    if (result != null) {
      _subscriptions.add(Subscription.fromJson(result));
      notifyListeners();
      loadAnalytics();
      return true;
    }
    return false;
  }

  Future<bool> update(String id, Map<String, dynamic> data) async {
    final result = await ApiClient.updateSubscription(id, data);
    if (result != null) {
      final idx = _subscriptions.indexWhere((s) => s.id == id);
      if (idx != -1) _subscriptions[idx] = Subscription.fromJson(result);
      notifyListeners();
      loadAnalytics();
      return true;
    }
    return false;
  }

  Future<bool> delete(String id) async {
    final ok = await ApiClient.deleteSubscription(id);
    if (ok) {
      _subscriptions.removeWhere((s) => s.id == id);
      notifyListeners();
      loadAnalytics();
    }
    return ok;
  }
}
