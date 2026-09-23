import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';

File? prefsFile() {
  if (kIsWeb || !Platform.isWindows) return null;
  final appData = Platform.environment['APPDATA'];
  if (appData == null) return null;
  return File(
    '$appData${Platform.pathSeparator}com.example'
    '${Platform.pathSeparator}merveille_pro'
    '${Platform.pathSeparator}shared_preferences.json',
  );
}

Future<void> sanitizePrefsFile() async {
  final file = prefsFile();
  if (file == null || !await file.exists()) return;

  try {
    final content = (await file.readAsString()).trim();
    if (content.isEmpty) {
      await resetPrefsFile();
      return;
    }
    final decoded = jsonDecode(content);
    if (decoded is! Map) {
      await resetPrefsFile();
    }
  } catch (_) {
    await resetPrefsFile();
  }
}

Future<void> resetPrefsFile() async {
  final file = prefsFile();
  if (file == null) return;
  try {
    if (await file.exists()) {
      await file.delete();
    }
    await file.parent.create(recursive: true);
    await file.writeAsString('{}');
  } catch (_) {}
}
