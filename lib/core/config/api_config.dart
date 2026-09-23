import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ApiConfig {
  ApiConfig._();
  static final ApiConfig instance = ApiConfig._();

  static const _storageKey = 'api_base_url';

  /// URL de production Contabo (Coolify / Traefik).
  static const productionBaseUrl = 'https://merveille.raaga-bf.com/api';

  String _baseUrl = defaultBaseUrl;
  String get baseUrl => _baseUrl;

  static String get defaultBaseUrl {
    // Desktop / release : pointe vers Render par défaut
    if (!kIsWeb && (Platform.isWindows || Platform.isLinux || Platform.isMacOS)) {
      return productionBaseUrl;
    }
    if (kIsWeb) return productionBaseUrl;
    if (!kIsWeb && Platform.isAndroid) {
      // Émulateur Android → machine hôte ; téléphone réel → configurer Render ou IP
      return 'http://10.0.2.2:8080/api';
    }
    return productionBaseUrl;
  }

  Future<void> load() async {
    final prefs = await SharedPreferences.getInstance();
    _baseUrl = prefs.getString(_storageKey) ?? defaultBaseUrl;
  }

  /// Accepte une URL complète, une IP, ou host:port.
  /// Exemples valides :
  /// - https://merveille-pro-service.onrender.com/api
  /// - http://192.168.11.103:8080/api
  /// - 192.168.11.103
  Future<void> setBaseUrl(String url) async {
    _baseUrl = normalizeBaseUrl(url);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_storageKey, _baseUrl);
  }

  static String normalizeBaseUrl(String url) {
    var value = url.trim();
    if (value.isEmpty) return defaultBaseUrl;

    // IP seule ou host:port → préfixe http://
    if (!value.startsWith('http://') && !value.startsWith('https://')) {
      // Domaines cloud (Render, etc.) → https
      if (value.contains('onrender.com') || value.contains('.')) {
        final looksLikeIp = RegExp(r'^\d{1,3}(\.\d{1,3}){3}(:\d+)?(/.*)?$').hasMatch(value);
        value = looksLikeIp ? 'http://$value' : 'https://$value';
      } else {
        value = 'http://$value';
      }
    }

    final uri = Uri.tryParse(value);
    if (uri == null || uri.host.isEmpty) return defaultBaseUrl;

    final scheme = uri.scheme == 'https' ? 'https' : 'http';
    final hasExplicitPort = uri.hasPort;
    final isLocal = uri.host == 'localhost' ||
        uri.host == '127.0.0.1' ||
        uri.host == '10.0.2.2' ||
        RegExp(r'^\d{1,3}(\.\d{1,3}){3}$').hasMatch(uri.host);

    if (isLocal) {
      final port = hasExplicitPort ? uri.port : 8080;
      return '$scheme://${uri.host}:$port/api';
    }

    // Cloud / domaine : pas de port forcé (443 pour https)
    if (hasExplicitPort && uri.port != 80 && uri.port != 443) {
      return '$scheme://${uri.host}:${uri.port}/api';
    }
    return '$scheme://${uri.host}/api';
  }

  void reset() {
    _baseUrl = defaultBaseUrl;
  }
}
