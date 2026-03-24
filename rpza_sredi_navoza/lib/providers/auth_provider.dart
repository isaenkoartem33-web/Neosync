import 'package:flutter/material.dart';
import '../api/api_client.dart';
import '../models/user.dart';

class AuthProvider extends ChangeNotifier {
  User? _user;
  bool _loading = false;
  String? _error;

  User? get user => _user;
  bool get loading => _loading;
  String? get error => _error;
  bool get isAuthenticated => _user != null;

  Future<void> tryAutoLogin() async {
    final token = await ApiClient.getToken();
    if (token == null) return;
    final data = await ApiClient.getMe();
    if (data != null) {
      _user = User.fromJson(data);
      notifyListeners();
    }
  }

  Future<bool> login(String email, String password) async {
    _loading = true;
    _error = null;
    notifyListeners();
    final result = await ApiClient.login(email, password);
    _loading = false;
    if (result['status'] == 200) {
      _user = User.fromJson(result['data']['user']);
      notifyListeners();
      return true;
    }
    _error = result['data']['error'] ?? 'Ошибка входа';
    notifyListeners();
    return false;
  }

  Future<bool> register(String email, String password, String name) async {
    _loading = true;
    _error = null;
    notifyListeners();
    final result = await ApiClient.register(email, password, name);
    _loading = false;
    if (result['status'] == 200) {
      // Регистрация успешна — нужно подтвердить email
      notifyListeners();
      return true;
    }
    _error = result['data']['error'] ?? 'Ошибка регистрации';
    notifyListeners();
    return false;
  }

  Future<bool> verifyEmail(String email, String code) async {
    _loading = true;
    _error = null;
    notifyListeners();
    final result = await ApiClient.verifyEmail(email, code);
    _loading = false;
    if (result['status'] == 201) {
      _user = User.fromJson(result['data']['user']);
      notifyListeners();
      return true;
    }
    _error = result['data']['error'] ?? 'Неверный код';
    notifyListeners();
    return false;
  }

  Future<void> logout() async {
    await ApiClient.deleteToken();
    _user = null;
    notifyListeners();
  }
}
