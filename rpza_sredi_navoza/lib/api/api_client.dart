import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiClient {
  static const String baseUrl = 'http://localhost:5000';
  static const String _tokenKey = 'jwt_token';
  static const _timeout = Duration(seconds: 30);
  static const _emailTimeout = Duration(seconds: 120); // сканирование почты может занять до 2 мин

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_tokenKey);
  }

  static Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
  }

  static Future<void> deleteToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
  }

  static Future<Map<String, String>> _headers() async {
    final token = await getToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  static Future<http.Response> get(String path) async {
    final headers = await _headers();
    return http.get(Uri.parse('$baseUrl$path'), headers: headers).timeout(_timeout);
  }

  static Future<http.Response> post(String path, Map<String, dynamic> body) async {
    final headers = await _headers();
    return http.post(Uri.parse('$baseUrl$path'), headers: headers, body: jsonEncode(body)).timeout(_timeout);
  }

  static Future<http.Response> put(String path, Map<String, dynamic> body) async {
    final headers = await _headers();
    return http.put(Uri.parse('$baseUrl$path'), headers: headers, body: jsonEncode(body)).timeout(_timeout);
  }

  static Future<http.Response> delete(String path) async {
    final headers = await _headers();
    return http.delete(Uri.parse('$baseUrl$path'), headers: headers).timeout(_timeout);
  }

  // Auth
  static Future<Map<String, dynamic>> login(String email, String password) async {
    try {
      final res = await post('/mobile/auth/login', {'email': email, 'password': password});
      final data = jsonDecode(res.body);
      if (res.statusCode == 200) await saveToken(data['token']);
      return {'status': res.statusCode, 'data': data};
    } catch (e) {
      return {'status': 0, 'data': {'error': 'Нет соединения с сервером. Убедитесь что Flask запущен.'}};
    }
  }

  static Future<Map<String, dynamic>> register(String email, String password, String name) async {
    try {
      final res = await post('/mobile/auth/register', {'email': email, 'password': password, 'name': name});
      final data = jsonDecode(utf8.decode(res.bodyBytes));
      return {'status': res.statusCode, 'data': data};
    } catch (e) {
      print('[ApiClient] register exception: $e');
      return {'status': 0, 'data': {'error': 'Нет соединения с сервером. Убедитесь что Flask запущен.'}};
    }
  }

  static Future<Map<String, dynamic>> verifyEmail(String email, String code) async {
    try {
      print('[ApiClient] verifyEmail email=$email code=$code');
      final res = await post('/mobile/auth/verify-email', {'email': email, 'code': code});
      final data = jsonDecode(utf8.decode(res.bodyBytes));
      print('[ApiClient] verifyEmail status=${res.statusCode} data=$data');
      if (res.statusCode == 201) await saveToken(data['token']);
      return {'status': res.statusCode, 'data': data};
    } catch (e) {
      print('[ApiClient] verifyEmail exception: $e');
      return {'status': 0, 'data': {'error': 'Нет соединения с сервером.'}};
    }
  }

  static Future<Map<String, dynamic>?> getMe() async {
    try {
      final res = await get('/mobile/auth/me');
      if (res.statusCode == 200) return jsonDecode(res.body);
    } catch (_) {}
    return null;
  }

  // Subscriptions
  static Future<List<dynamic>> getSubscriptions() async {
    try {
      final res = await get('/mobile/subscriptions');
      if (res.statusCode == 200) return jsonDecode(res.body);
    } catch (_) {}
    return [];
  }

  static Future<Map<String, dynamic>?> createSubscription(Map<String, dynamic> data) async {
    try {
      final res = await post('/mobile/subscriptions', data);
      if (res.statusCode == 201) return jsonDecode(res.body);
    } catch (_) {}
    return null;
  }

  static Future<Map<String, dynamic>?> updateSubscription(String id, Map<String, dynamic> data) async {
    try {
      final res = await put('/mobile/subscriptions/$id', data);
      if (res.statusCode == 200) return jsonDecode(res.body);
    } catch (_) {}
    return null;
  }

  static Future<bool> deleteSubscription(String id) async {
    try {
      final res = await delete('/mobile/subscriptions/$id');
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  // Email import
  static Future<Map<String, dynamic>> scanEmail(String provider, String email, String password) async {
    final url = '$baseUrl/mobile/email/scan';
    print('[ApiClient] scanEmail → POST $url');
    try {
      final headers = await _headers();
      final res = await http.post(
        Uri.parse(url),
        headers: headers,
        body: jsonEncode({'provider': provider, 'email': email, 'password': password}),
      ).timeout(_emailTimeout);
      print('[ApiClient] scan status=${res.statusCode}');
      print('[ApiClient] scan body=${res.body}');
      // jsonDecode может упасть на спецсимволах — ловим отдельно
      try {
        final decoded = jsonDecode(utf8.decode(res.bodyBytes));
        return {'status': res.statusCode, 'data': decoded};
      } catch (decodeErr) {
        print('[ApiClient] JSON decode error: $decodeErr');
        return {'status': 0, 'data': {'error': 'Ошибка разбора ответа сервера: $decodeErr'}};
      }
    } catch (e, stack) {
      print('[ApiClient] EXCEPTION: $e');
      print('[ApiClient] STACK: $stack');
      return {'status': 0, 'data': {'error': 'Нет соединения с сервером'}};
    }
  }

  static Future<Map<String, dynamic>> importSubscriptions(List<Map<String, dynamic>> subscriptions) async {
    try {
      final res = await post('/mobile/email/import', {'subscriptions': subscriptions});
      return {'status': res.statusCode, 'data': jsonDecode(res.body)};
    } catch (e) {
      return {'status': 0, 'data': {'error': 'Нет соединения с сервером'}};
    }
  }

  static Future<Map<String, dynamic>> importFromEmail(String provider, String email, String password) async {
    try {
      final res = await post('/mobile/email/import', {'provider': provider, 'email': email, 'password': password});
      return {'status': res.statusCode, 'data': jsonDecode(res.body)};
    } catch (e) {
      return {'status': 0, 'data': {'error': 'Нет соединения с сервером'}};
    }
  }

  // Analytics
  static Future<Map<String, dynamic>?> getAnalyticsSummary() async {    try {
      final res = await get('/mobile/analytics/summary');
      if (res.statusCode == 200) return jsonDecode(res.body);
    } catch (_) {}
    return null;
  }

  static Future<Map<String, dynamic>?> getAnalyticsByCategory() async {
    try {
      final res = await get('/mobile/analytics/by-category');
      if (res.statusCode == 200) return jsonDecode(res.body);
    } catch (_) {}
    return null;
  }
}
