import 'dart:convert';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import '../../../core/theme/app_fonts.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/constants/commerce_constants.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/utils/formatters.dart';
import '../../../widgets/animations.dart';
import '../../../widgets/data_list.dart';
import '../../../widgets/page_layout.dart';
import '../../auth/providers/auth_provider.dart';
import '../../shops/providers/shop_provider.dart';
import '../models/product_model.dart';
import '../providers/product_provider.dart';
import '../widgets/product_form_dialog.dart';

class ProductsScreen extends ConsumerStatefulWidget {
  const ProductsScreen({super.key});

  @override
  ConsumerState<ProductsScreen> createState() => _ProductsScreenState();
}

class _ProductsScreenState extends ConsumerState<ProductsScreen> {
  String _query = '';
  bool _importing = false;

  Future<void> _importCsv() async {
    final shopId = ref.read(effectiveShopIdProvider);
    if (shopId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Sélectionnez une boutique avant d\'importer')),
      );
      return;
    }

    final result = await FilePicker.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['csv'],
      withData: true,
    );
    if (result == null || result.files.isEmpty) return;
    final file = result.files.first;

    String csvContent;
    if (file.bytes != null) {
      csvContent = utf8.decode(file.bytes!, allowMalformed: true);
    } else {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Impossible de lire le fichier CSV')),
        );
      }
      return;
    }

    // Nettoyer BOM éventuel
    if (csvContent.startsWith('\uFEFF')) {
      csvContent = csvContent.substring(1);
    }

    if (!mounted) return;
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Importer le CSV ?', style: AppFonts.style(fontWeight: FontWeight.w800)),
        content: Text(
          'Fichier : ${file.name}\n'
          'Boutique sélectionnée.\n\n'
          'Les produits existants (même nom) seront mis à jour.',
          style: AppFonts.style(fontSize: 13),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Annuler')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Importer')),
        ],
      ),
    );
    if (confirm != true || !mounted) return;

    setState(() => _importing = true);
    try {
      final summary = await ref.read(productRepositoryProvider).importCsv(
            shopId: shopId,
            csvContent: csvContent,
          );
      ref.invalidate(productsProvider(_query.isEmpty ? null : _query));
      ref.invalidate(productsProvider(null));
      ref.invalidate(categoriesProvider);
      ref.invalidate(posProductsProvider(null));
      if (!mounted) return;

      final created = summary['created'] ?? 0;
      final updated = summary['updated'] ?? 0;
      final skipped = summary['skipped'] ?? 0;
      final errors = (summary['errors'] as List?) ?? const [];

      await showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: Text('Import terminé', style: AppFonts.style(fontWeight: FontWeight.w800)),
          content: SizedBox(
            width: 420,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Créés : $created', style: AppFonts.style(fontWeight: FontWeight.w600)),
                Text('Mis à jour : $updated', style: AppFonts.style(fontWeight: FontWeight.w600)),
                Text('Ignorés : $skipped', style: AppFonts.style()),
                if (errors.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  Text('Erreurs (${errors.length}) :', style: AppFonts.style(color: AppTheme.danger, fontWeight: FontWeight.w700)),
                  const SizedBox(height: 6),
                  ConstrainedBox(
                    constraints: const BoxConstraints(maxHeight: 160),
                    child: SingleChildScrollView(
                      child: Text(
                        errors.take(20).join('\n'),
                        style: AppFonts.style(fontSize: 12, color: AppTheme.primary.withValues(alpha: 0.7)),
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
          actions: [
            FilledButton(onPressed: () => Navigator.pop(ctx), child: const Text('OK')),
          ],
        ),
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
      }
    } finally {
      if (mounted) setState(() => _importing = false);
    }
  }

  Future<void> _showCategoryDialog() async {
    final nameCtrl = TextEditingController();

    await showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Catégories', style: AppFonts.style(fontWeight: FontWeight.w800)),
        content: SizedBox(
          width: 400,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: nameCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Nouvelle catégorie',
                        hintText: 'Ex : Soins visage, Cahiers…',
                      ),
                      onSubmitted: (_) => _createCategory(ctx, nameCtrl),
                    ),
                  ),
                  const SizedBox(width: 8),
                  FilledButton(
                    onPressed: () => _createCategory(ctx, nameCtrl),
                    child: const Icon(Icons.add_rounded),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Consumer(
                builder: (context, ref, _) {
                  final categories = ref.watch(categoriesProvider);
                  return categories.when(
                    loading: () => const Padding(
                      padding: EdgeInsets.all(16),
                      child: CircularProgressIndicator(),
                    ),
                    error: (e, _) => Text('Erreur : $e'),
                    data: (list) => ConstrainedBox(
                      constraints: const BoxConstraints(maxHeight: 280),
                      child: list.isEmpty
                          ? Text(
                              'Aucune catégorie',
                              style: AppFonts.style(color: AppTheme.primary.withValues(alpha: 0.5)),
                            )
                          : ListView.separated(
                              shrinkWrap: true,
                              itemCount: list.length,
                              separatorBuilder: (_, __) => const SizedBox(height: 6),
                              itemBuilder: (context, i) {
                                final cat = list[i];
                                return Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                                  decoration: BoxDecoration(
                                    color: AppTheme.surface,
                                    borderRadius: BorderRadius.circular(12),
                                  ),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        children: [
                                          Icon(Icons.category_rounded, size: 18, color: AppTheme.accent.withValues(alpha: 0.7)),
                                          const SizedBox(width: 10),
                                          Expanded(
                                            child: Text(cat.name, style: AppFonts.style(fontWeight: FontWeight.w700)),
                                          ),
                                          IconButton(
                                            icon: const Icon(Icons.delete_outline_rounded, size: 18, color: AppTheme.danger),
                                            tooltip: 'Supprimer',
                                            onPressed: () async {
                                              try {
                                                await ref.read(productRepositoryProvider).deleteCategory(cat.id);
                                                ref.invalidate(categoriesProvider);
                                              } catch (e) {
                                                if (ctx.mounted) {
                                                  ScaffoldMessenger.of(ctx).showSnackBar(SnackBar(content: Text('$e')));
                                                }
                                              }
                                            },
                                          ),
                                        ],
                                      ),
                                      if (cat.subcategories.isNotEmpty) ...[
                                        const SizedBox(height: 8),
                                        ...cat.subcategories.map(
                                          (sub) => Padding(
                                            padding: const EdgeInsets.only(left: 28, bottom: 4),
                                            child: Row(
                                              children: [
                                                Icon(Icons.subdirectory_arrow_right_rounded, size: 16, color: AppTheme.primary.withValues(alpha: 0.4)),
                                                const SizedBox(width: 6),
                                                Expanded(child: Text(sub.name, style: AppFonts.style(fontSize: 13))),
                                                IconButton(
                                                  icon: const Icon(Icons.close_rounded, size: 16, color: AppTheme.danger),
                                                  tooltip: 'Supprimer',
                                                  onPressed: () async {
                                                    try {
                                                      await ref.read(productRepositoryProvider).deleteSubCategory(sub.id);
                                                      ref.invalidate(categoriesProvider);
                                                    } catch (e) {
                                                      if (ctx.mounted) {
                                                        ScaffoldMessenger.of(ctx).showSnackBar(SnackBar(content: Text('$e')));
                                                      }
                                                    }
                                                  },
                                                ),
                                              ],
                                            ),
                                          ),
                                        ),
                                      ],
                                      Padding(
                                        padding: const EdgeInsets.only(left: 28, top: 4),
                                        child: TextButton.icon(
                                          onPressed: () => _createSubCategory(ctx, cat.id),
                                          icon: const Icon(Icons.add_rounded, size: 16),
                                          label: const Text('Sous-catégorie'),
                                        ),
                                      ),
                                    ],
                                  ),
                                );
                              },
                            ),
                    ),
                  );
                },
              ),
            ],
          ),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Fermer')),
        ],
      ),
    );
    nameCtrl.dispose();
  }

  Future<void> _createCategory(BuildContext ctx, TextEditingController nameCtrl) async {
    final name = nameCtrl.text.trim();
    if (name.isEmpty) return;
    try {
      await ref.read(productRepositoryProvider).createCategory(name);
      nameCtrl.clear();
      ref.invalidate(categoriesProvider);
      if (ctx.mounted) {
        ScaffoldMessenger.of(ctx).showSnackBar(
          SnackBar(content: Text('Catégorie « $name » créée')),
        );
      }
    } catch (e) {
      if (ctx.mounted) ScaffoldMessenger.of(ctx).showSnackBar(SnackBar(content: Text('$e')));
    }
  }

  Future<void> _createSubCategory(BuildContext ctx, int categoryId) async {
    final nameCtrl = TextEditingController();
    final name = await showDialog<String>(
      context: ctx,
      builder: (dCtx) => AlertDialog(
        title: const Text('Nouvelle sous-catégorie'),
        content: TextField(
          controller: nameCtrl,
          autofocus: true,
          decoration: const InputDecoration(
            labelText: 'Nom',
            hintText: 'Ex : Hydratation, Bille…',
          ),
          onSubmitted: (_) => Navigator.pop(dCtx, nameCtrl.text.trim()),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(dCtx), child: const Text('Annuler')),
          FilledButton(onPressed: () => Navigator.pop(dCtx, nameCtrl.text.trim()), child: const Text('Créer')),
        ],
      ),
    );
    nameCtrl.dispose();
    if (name == null || name.isEmpty) return;
    try {
      await ref.read(productRepositoryProvider).createSubCategory(categoryId: categoryId, name: name);
      ref.invalidate(categoriesProvider);
      if (ctx.mounted) {
        ScaffoldMessenger.of(ctx).showSnackBar(SnackBar(content: Text('Sous-catégorie « $name » créée')));
      }
    } catch (e) {
      if (ctx.mounted) ScaffoldMessenger.of(ctx).showSnackBar(SnackBar(content: Text('$e')));
    }
  }

  Future<void> _showProductDialog({ProductModel? product}) async {
    final shopId = ref.read(effectiveShopIdProvider);
    if (product == null && shopId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Sélectionnez une boutique avant d\'ajouter un produit')),
      );
      return;
    }

    final categories = await ref.read(categoriesProvider.future);
    if (!mounted) return;

    await showProductFormDialog(
      context: context,
      ref: ref,
      categories: categories,
      product: product,
      shopId: shopId,
    );
  }

  Future<void> _showPresetCategoriesDialog() async {
    final sector = await showDialog<String>(
      context: context,
      builder: (ctx) => SimpleDialog(
        title: Text('Modèle de catégories', style: AppFonts.style(fontWeight: FontWeight.w800)),
        children: [
          SimpleDialogOption(
            onPressed: () => Navigator.pop(ctx, 'librairie'),
            child: const ListTile(
              leading: Icon(Icons.menu_book_rounded),
              title: Text('Librairie & papeterie'),
            ),
          ),
          SimpleDialogOption(
            onPressed: () => Navigator.pop(ctx, 'cosmetiques'),
            child: const ListTile(
              leading: Icon(Icons.spa_rounded),
              title: Text('Cosmétiques & beauté'),
            ),
          ),
          SimpleDialogOption(
            onPressed: () => Navigator.pop(ctx, 'generique'),
            child: const ListTile(
              leading: Icon(Icons.storefront_rounded),
              title: Text('Commerce général'),
            ),
          ),
        ],
      ),
    );
    if (sector == null) return;

    final names = CommerceConstants.categoryPresets[sector] ?? [];
    final repo = ref.read(productRepositoryProvider);
    for (final name in names) {
      try {
        await repo.createCategory(name);
      } catch (_) {}
    }
    ref.invalidate(categoriesProvider);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('${names.length} catégories ajoutées')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final products = ref.watch(productsProvider(_query.isEmpty ? null : _query));
    final isAdmin = ref.watch(authProvider).user?.isAdmin ?? false;

    return PageLayout(
      title: 'Produits',
      subtitle: 'Librairie, cosmétiques, commerce général',
      actions: [
        SearchField(hint: 'Rechercher...', onChanged: (v) => setState(() => _query = v)),
        if (isAdmin) ...[
          const SizedBox(width: 12),
          ScaleTap(
            onTap: _importCsv,
            enabled: !_importing,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
              decoration: BoxDecoration(
                color: AppTheme.surface,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppTheme.primary.withValues(alpha: 0.08)),
              ),
              child: Row(
                children: [
                  if (_importing)
                    const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  else
                    Icon(Icons.upload_file_rounded, color: AppTheme.primary.withValues(alpha: 0.6), size: 20),
                  const SizedBox(width: 8),
                  Text(
                    _importing ? 'Import…' : 'Importer CSV',
                    style: AppFonts.style(fontWeight: FontWeight.w600, fontSize: 13),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(width: 12),
          ScaleTap(
            onTap: _showPresetCategoriesDialog,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
              decoration: BoxDecoration(
                color: AppTheme.surface,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppTheme.primary.withValues(alpha: 0.08)),
              ),
              child: Row(
                children: [
                  Icon(Icons.dashboard_customize_rounded, color: AppTheme.primary.withValues(alpha: 0.6), size: 20),
                  const SizedBox(width: 8),
                  Text('Modèles catégories', style: AppFonts.style(fontWeight: FontWeight.w600, fontSize: 13)),
                ],
              ),
            ),
          ),
          const SizedBox(width: 12),
          ScaleTap(
            onTap: _showCategoryDialog,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 14),
              decoration: BoxDecoration(
                color: AppTheme.accent.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: AppTheme.accent.withValues(alpha: 0.2)),
              ),
              child: Row(
                children: [
                  const Icon(Icons.category_rounded, color: AppTheme.accent, size: 20),
                  const SizedBox(width: 8),
                  Text('Catégories', style: AppFonts.style(color: AppTheme.accent, fontWeight: FontWeight.w600)),
                ],
              ),
            ),
          ),
          const SizedBox(width: 12),
          ScaleTap(
            onTap: () => _showProductDialog(),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
              decoration: BoxDecoration(
                gradient: const LinearGradient(colors: [AppTheme.accent, AppTheme.violet]),
                borderRadius: BorderRadius.circular(14),
                boxShadow: AppTheme.glowShadow,
              ),
              child: Row(
                children: [
                  const Icon(Icons.add_rounded, color: Colors.white, size: 20),
                  const SizedBox(width: 8),
                  Text('Ajouter', style: AppFonts.style(color: Colors.white, fontWeight: FontWeight.w600)),
                ],
              ),
            ),
          ),
        ],
      ],
      child: products.when(
        loading: () => const LoadingView(),
        error: (e, _) => EmptyView(icon: Icons.error_outline, message: '$e'),
        data: (list) => GlassCard(
          padding: EdgeInsets.zero,
          child: Column(
            children: [
              const DataListHeader(columns: ['Produit', 'Détails', 'Prix', 'Stock', 'Statut', 'Actions']),
              Expanded(
                child: ListView.builder(
                  itemCount: list.length,
                  itemBuilder: (context, i) {
                    final p = list[i];
                    return DataListRow(
                      index: i,
                      cells: [
                        Text(p.name, style: AppFonts.style(fontWeight: FontWeight.w600)),
                        Text(
                          p.displaySubtitle.isEmpty ? p.categoryName : p.displaySubtitle,
                          style: AppFonts.style(color: AppTheme.primary.withValues(alpha: 0.5), fontSize: 12),
                        ),
                        Text(
                          p.hasPackPricing ? '${formatCurrency(p.sellingPrice)} / u' : formatCurrency(p.sellingPrice),
                          style: AppFonts.style(fontWeight: FontWeight.w600, color: AppTheme.accent),
                        ),
                        Row(
                          children: [
                            Text('${p.stockQuantity}', style: AppFonts.style(fontWeight: FontWeight.w600)),
                            if (p.isLowStock) const Padding(padding: EdgeInsets.only(left: 6), child: Icon(Icons.warning_rounded, color: AppTheme.danger, size: 16)),
                          ],
                        ),
                        StatusBadge(label: p.isLowStock ? 'Stock faible' : 'OK', color: p.isLowStock ? AppTheme.danger : AppTheme.success),
                      ],
                      actions: isAdmin
                          ? [
                              IconButton(icon: const Icon(Icons.edit_rounded, size: 20), onPressed: () => _showProductDialog(product: p)),
                              IconButton(
                                icon: const Icon(Icons.delete_outline_rounded, size: 20, color: AppTheme.danger),
                                onPressed: () async {
                                  await ref.read(productRepositoryProvider).deleteProduct(p.id);
                                  ref.invalidate(productsProvider);
                                },
                              ),
                            ]
                          : null,
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
