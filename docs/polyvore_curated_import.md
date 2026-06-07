# Polyvore Curated Product Import

This note describes the product import path used when ReBloom needs cleaner
marketplace demo items from a curated Polyvore-style subset.

## Expected ZIP Format

Place the ZIP under:

```text
local_datasets/polyvore_curated_subset.zip
```

The ZIP should contain:

```text
products.csv
images/
  item_001.jpg
  item_002.jpg
  ...
```

`products.csv` supports these columns:

```text
title,image_file,category,subcategory,brand,color,size,gender,condition,material,weight_kg,price,seller_name,description
```

Minimum useful columns:

```text
title,image_file,category,brand,color,gender
```

The importer fills missing fields conservatively:

- `seller_name`: assigned from demo sellers
- `size`: inferred from category/gender
- `material`: inferred from category/title
- `weight_kg`: default backend category weight
- `water_saved_liters`: calculated with the backend water impact algorithm
- `source_platform`: `polyvore-curated-subset`

## Preview

```powershell
python scripts/import_curated_products.py --dry-run
```

## Import

```powershell
python scripts/import_curated_products.py --replace
```

## Import and Hide Older Generated Dataset Items

```powershell
python scripts/import_curated_products.py `
  --replace `
  --deactivate-source outfit-items-subset
```

This keeps old order history intact because products are marked inactive instead
of being removed from the database.
