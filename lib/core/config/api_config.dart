import 'package:shared_preferences/shared_preferences.dart';

/// Configuration API — URL serveur fixe (jamais affichée à l'utilisateur).
class ApiConfig {
  ApiConfig._();
  static final ApiConfig instance = ApiConfig._();

  /// Backend Contabo (Coolify).
  static const productionBaseUrl = 'https://merveille.raaga-bf.com/api';

  String get baseUrl => productionBaseUrl;

  /// Conservé pour compatibilité ; force toujours la prod.
  static String get defaultBaseUrl => productionBaseUrl;

  Future<void> load() async {
    // Purge d'éventuelles anciennes URL locales sauvegardées.
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove('api_base_url');
    } catch (_) {}
  }

  /// Ignoré : l'URL reste celle de production.
  Future<void> setBaseUrl(String url) async {}

  static String normalizeBaseUrl(String url) => productionBaseUrl;

  void reset() {}
}
