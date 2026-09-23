import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

/// Polices système — évite les appels réseau Google Fonts.
class AppFonts {
  AppFonts._();

  static String get family {
    if (kIsWeb) return 'Segoe UI';
    switch (defaultTargetPlatform) {
      case TargetPlatform.windows:
        return 'Segoe UI';
      case TargetPlatform.iOS:
      case TargetPlatform.macOS:
        return '.AppleSystemUIFont';
      default:
        return 'Roboto';
    }
  }

  static TextStyle style({
    double? fontSize,
    FontWeight? fontWeight,
    Color? color,
    double? letterSpacing,
    double? height,
    FontStyle? fontStyle,
    TextDecoration? decoration,
  }) {
    return TextStyle(
      fontFamily: family,
      fontSize: fontSize,
      fontWeight: fontWeight,
      color: color,
      letterSpacing: letterSpacing,
      height: height,
      fontStyle: fontStyle,
      decoration: decoration,
    );
  }

  static TextTheme textTheme([TextTheme? base]) {
    final theme =
        base ?? Typography.material2021(platform: TargetPlatform.windows).black;
    return theme.apply(fontFamily: family);
  }
}
