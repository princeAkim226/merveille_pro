import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'prefs_io.dart' if (dart.library.html) 'prefs_web.dart' as prefs_platform;

/// Charge SharedPreferences en récupérant un fichier local corrompu ou vide.
Future<SharedPreferences> loadSharedPreferences() async {
  await prefs_platform.sanitizePrefsFile();
  try {
    return await SharedPreferences.getInstance();
  } on FormatException {
    await prefs_platform.resetPrefsFile();
    return SharedPreferences.getInstance();
  } on PlatformException catch (e) {
    if (e.message?.contains('empty') ?? false) {
      await prefs_platform.resetPrefsFile();
      return SharedPreferences.getInstance();
    }
    rethrow;
  }
}
