import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:pdf/pdf.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:printing/printing.dart';

import '../../../core/utils/formatters.dart';
import '../../settings/models/company_settings_model.dart';

class InvoiceExportResult {
  const InvoiceExportResult({this.path, this.cancelled = false});

  final String? path;
  final bool cancelled;

  bool get success => path != null;
}

class InvoiceService {
  static const _accent = PdfColor.fromInt(0xFF6366F1);
  static const _violet = PdfColor.fromInt(0xFF8B5CF6);
  static const _primary = PdfColor.fromInt(0xFF0F172A);
  static const _muted = PdfColor.fromInt(0xFF64748B);
  static const _surface = PdfColor.fromInt(0xFFF1F5F9);
  static const _white = PdfColors.white;

  static bool get _isDesktop {
    if (kIsWeb) return false;
    return defaultTargetPlatform == TargetPlatform.windows ||
        defaultTargetPlatform == TargetPlatform.linux ||
        defaultTargetPlatform == TargetPlatform.macOS;
  }

  static Future<void> previewAndPrint(Map<String, dynamic> invoice, {CompanySettingsModel? branding}) async {
    final pdf = await _buildPdf(invoice, branding: branding);
    await Printing.layoutPdf(onLayout: (_) async => pdf.save());
  }

  static Future<InvoiceExportResult> exportPdf(Map<String, dynamic> invoice, {CompanySettingsModel? branding}) async {
    final pdf = await _buildPdf(invoice, branding: branding);
    final bytes = await pdf.save();
    final filename = 'facture_${invoice['sale_id']}.pdf';

    if (_isDesktop) {
      final path = await FilePicker.saveFile(
        dialogTitle: 'Enregistrer la facture',
        fileName: filename,
        type: FileType.custom,
        allowedExtensions: ['pdf'],
        bytes: bytes,
      );
      if (path == null) return const InvoiceExportResult(cancelled: true);
      return InvoiceExportResult(path: path);
    }

    await Printing.sharePdf(bytes: bytes, filename: filename);
    return InvoiceExportResult(path: filename);
  }

  static Future<({pw.Font regular, pw.Font bold, pw.Font semiBold})> _loadFonts() async {
    try {
      return (
        regular: await PdfGoogleFonts.plusJakartaSansRegular(),
        bold: await PdfGoogleFonts.plusJakartaSansBold(),
        semiBold: await PdfGoogleFonts.plusJakartaSansSemiBold(),
      );
    } catch (_) {
      return (
        regular: await PdfGoogleFonts.nunitoSansRegular(),
        bold: await PdfGoogleFonts.nunitoSansBold(),
        semiBold: await PdfGoogleFonts.nunitoSansSemiBold(),
      );
    }
  }

  static Future<pw.Document> _buildPdf(Map<String, dynamic> invoice, {CompanySettingsModel? branding}) async {
    final fonts = await _loadFonts();
    final regular = fonts.regular;
    final bold = fonts.bold;
    final semiBold = fonts.semiBold;

    final companyName = branding?.companyName ?? 'Merveille Pro';
    final tagline = branding?.tagline ?? 'Gestion commerciale';
    final footer = branding?.invoiceFooter ?? 'Merci pour votre confiance !';
    final logoBytes = branding?.logoBytes;
    final contactParts = [
      if (branding?.phone.isNotEmpty == true) branding!.phone,
      if (branding?.email.isNotEmpty == true) branding!.email,
      if (branding?.address.isNotEmpty == true) branding!.address,
    ];

    final doc = pw.Document();
    final items = invoice['items'] as List;
    final date = DateTime.parse(invoice['date'] as String);
    final total = double.parse(invoice['total_amount'].toString());
    final shop = invoice['shop'] as String? ?? '';
    final notes = invoice['notes'] as String? ?? '';

    pw.TextStyle heading({double size = 24, PdfColor color = _white}) =>
        pw.TextStyle(font: bold, fontSize: size, color: color);

    doc.addPage(
      pw.Page(
        pageFormat: PdfPageFormat.a4,
        margin: const pw.EdgeInsets.all(32),
        build: (context) {
          return pw.Column(
            crossAxisAlignment: pw.CrossAxisAlignment.stretch,
            children: [
              // En-tête
              pw.Container(
                padding: const pw.EdgeInsets.all(24),
                decoration: const pw.BoxDecoration(
                  gradient: pw.LinearGradient(
                    begin: pw.Alignment.topLeft,
                    end: pw.Alignment.bottomRight,
                    colors: [_accent, _violet],
                  ),
                  borderRadius: pw.BorderRadius.all(pw.Radius.circular(16)),
                ),
                child: pw.Row(
                  mainAxisAlignment: pw.MainAxisAlignment.spaceBetween,
                  crossAxisAlignment: pw.CrossAxisAlignment.start,
                  children: [
                    pw.Row(
                      children: [
                        if (logoBytes != null)
                          pw.Container(
                            width: 48,
                            height: 48,
                            margin: const pw.EdgeInsets.only(right: 12),
                            child: pw.ClipRRect(
                              horizontalRadius: 8,
                              verticalRadius: 8,
                              child: pw.Image(pw.MemoryImage(logoBytes), fit: pw.BoxFit.cover),
                            ),
                          ),
                        pw.Column(
                          crossAxisAlignment: pw.CrossAxisAlignment.start,
                          children: [
                            pw.Text(companyName.toUpperCase(), style: heading(size: 18)),
                            if (tagline.isNotEmpty) ...[
                              pw.SizedBox(height: 4),
                              pw.Text(tagline, style: pw.TextStyle(font: regular, fontSize: 10, color: PdfColor.fromInt(0xCCFFFFFF))),
                            ],
                            if (contactParts.isNotEmpty) ...[
                              pw.SizedBox(height: 6),
                              pw.Text(contactParts.join(' • '), style: pw.TextStyle(font: regular, fontSize: 8, color: PdfColor.fromInt(0xB3FFFFFF))),
                            ],
                          ],
                        ),
                      ],
                    ),
                    pw.Column(
                      crossAxisAlignment: pw.CrossAxisAlignment.end,
                      children: [
                        pw.Text('FACTURE', style: pw.TextStyle(font: bold, fontSize: 10, color: PdfColor.fromInt(0xCCFFFFFF))),
                        pw.SizedBox(height: 6),
                        pw.Text('N° ${invoice['sale_id']}', style: heading(size: 18)),
                        pw.Text(formatDate(date), style: pw.TextStyle(font: regular, fontSize: 11, color: PdfColor.fromInt(0xE6FFFFFF))),
                      ],
                    ),
                  ],
                ),
              ),
              pw.SizedBox(height: 20),

              // Infos
              pw.Row(
                children: [
                  pw.Expanded(child: _infoCard('Date', formatDateTime(date), regular, semiBold)),
                  pw.SizedBox(width: 10),
                  pw.Expanded(child: _infoCard('Vendeur', invoice['user'] as String? ?? '', regular, semiBold)),
                  if (shop.isNotEmpty) ...[
                    pw.SizedBox(width: 10),
                    pw.Expanded(child: _infoCard('Boutique', shop, regular, semiBold)),
                  ],
                ],
              ),
              pw.SizedBox(height: 24),

              pw.Text('Détail des articles', style: pw.TextStyle(font: bold, fontSize: 12, color: _primary)),
              pw.SizedBox(height: 10),

              // Tableau (pw.Table évite les erreurs Flex)
              pw.Table(
                border: pw.TableBorder.all(color: PdfColor.fromInt(0xFFE2E8F0), width: 0.5),
                columnWidths: {
                  0: const pw.FlexColumnWidth(3),
                  1: const pw.FlexColumnWidth(1),
                  2: const pw.FlexColumnWidth(1.5),
                  3: const pw.FlexColumnWidth(1.5),
                },
                children: [
                  pw.TableRow(
                    decoration: const pw.BoxDecoration(color: _surface),
                    children: [
                      _cell('Produit', bold, isHeader: true),
                      _cell('Qté', bold, isHeader: true, align: pw.TextAlign.center),
                      _cell('Prix unit.', bold, isHeader: true, align: pw.TextAlign.right),
                      _cell('Sous-total', bold, isHeader: true, align: pw.TextAlign.right),
                    ],
                  ),
                  ...items.asMap().entries.map((entry) {
                    final item = entry.value as Map<String, dynamic>;
                    final price = double.parse(item['price'].toString());
                    final subtotal = double.parse(item['subtotal'].toString());
                    final bg = entry.key.isEven ? _white : _surface;
                    return pw.TableRow(
                      decoration: pw.BoxDecoration(color: bg),
                      children: [
                        _cell(item['product'] as String, semiBold),
                        _cell('${item['quantity']}', regular, align: pw.TextAlign.center),
                        _cell(_formatAmount(price), regular, align: pw.TextAlign.right, color: _muted),
                        _cell(_formatAmount(subtotal), semiBold, align: pw.TextAlign.right),
                      ],
                    );
                  }),
                ],
              ),
              pw.SizedBox(height: 20),

              // Total aligné à droite
              pw.Align(
                alignment: pw.Alignment.centerRight,
                child: pw.Container(
                  width: 200,
                  padding: const pw.EdgeInsets.all(16),
                  decoration: const pw.BoxDecoration(
                    gradient: pw.LinearGradient(colors: [_accent, _violet]),
                    borderRadius: pw.BorderRadius.all(pw.Radius.circular(12)),
                  ),
                  child: pw.Column(
                    crossAxisAlignment: pw.CrossAxisAlignment.start,
                    children: [
                      pw.Text('TOTAL TTC', style: pw.TextStyle(font: regular, fontSize: 9, color: PdfColor.fromInt(0xCCFFFFFF))),
                      pw.SizedBox(height: 4),
                      pw.Text(formatCurrency(total), style: pw.TextStyle(font: bold, fontSize: 20, color: _white)),
                      pw.Text(
                        '${items.length} article${items.length > 1 ? 's' : ''}',
                        style: pw.TextStyle(font: regular, fontSize: 8, color: PdfColor.fromInt(0xB3FFFFFF)),
                      ),
                    ],
                  ),
                ),
              ),

              if (notes.isNotEmpty) ...[
                pw.SizedBox(height: 16),
                pw.Container(
                  padding: const pw.EdgeInsets.all(12),
                  decoration: pw.BoxDecoration(
                    color: _surface,
                    borderRadius: const pw.BorderRadius.all(pw.Radius.circular(8)),
                  ),
                  child: pw.Column(
                    crossAxisAlignment: pw.CrossAxisAlignment.start,
                    children: [
                      pw.Text('Notes', style: pw.TextStyle(font: semiBold, fontSize: 9, color: _muted)),
                      pw.SizedBox(height: 4),
                      pw.Text(notes, style: pw.TextStyle(font: regular, fontSize: 10, color: _primary)),
                    ],
                  ),
                ),
              ],

              pw.SizedBox(height: 32),
              pw.Divider(color: PdfColor.fromInt(0xFFE2E8F0)),
              pw.SizedBox(height: 12),
              pw.Center(
                child: pw.Column(
                  children: [
                    pw.Text(footer, style: pw.TextStyle(font: semiBold, fontSize: 11, color: _accent)),
                    pw.SizedBox(height: 4),
                    pw.Text('Document généré par $companyName', style: pw.TextStyle(font: regular, fontSize: 8, color: _muted)),
                  ],
                ),
              ),
            ],
          );
        },
      ),
    );
    return doc;
  }

  static pw.Widget _cell(
    String text,
    pw.Font font, {
    bool isHeader = false,
    pw.TextAlign align = pw.TextAlign.left,
    PdfColor color = _primary,
  }) {
    return pw.Padding(
      padding: const pw.EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      child: pw.Text(
        text,
        style: pw.TextStyle(font: font, fontSize: isHeader ? 9 : 10, color: color),
        textAlign: align,
      ),
    );
  }

  static pw.Widget _infoCard(String label, String value, pw.Font regular, pw.Font semiBold) {
    return pw.Container(
      padding: const pw.EdgeInsets.all(12),
      decoration: pw.BoxDecoration(
        color: _surface,
        borderRadius: const pw.BorderRadius.all(pw.Radius.circular(8)),
        border: pw.Border.all(color: PdfColor.fromInt(0xFFE2E8F0)),
      ),
      child: pw.Column(
        crossAxisAlignment: pw.CrossAxisAlignment.start,
        children: [
          pw.Text(label.toUpperCase(), style: pw.TextStyle(font: regular, fontSize: 7, color: _muted)),
          pw.SizedBox(height: 4),
          pw.Text(value, style: pw.TextStyle(font: semiBold, fontSize: 10, color: _primary)),
        ],
      ),
    );
  }

  static String _formatAmount(double value) {
    final formatted = value.toStringAsFixed(0).replaceAllMapped(
          RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
          (m) => '${m[1]} ',
        );
    return '$formatted F';
  }
}
