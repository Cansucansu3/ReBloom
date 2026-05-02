import argparse

from services.embedding_service import (
    DEFAULT_EMBEDDINGS_PATH,
    DEFAULT_METADATA_PATH,
    DEFAULT_PRODUCTS_PATH,
    build_product_embeddings,
    load_embedding_index,
    load_products,
)
from services.outfit_recommendation import recommend_outfit
from services.similarity_service import find_similar_products, search_by_image


def print_search_results(results):
    if not results:
        print("No results found.")
        return

    for index, result in enumerate(results, start=1):
        product = result["product"]
        score = result["score"]
        print(f"{index}. {product.get('title')} ({score:.3f})")
        print(
            "   "
            f"{product.get('category')} | {product.get('color')} | "
            f"{product.get('brand')}"
        )


def run_outfit(product_id, top_k_per_category):
    embeddings, metadata = load_embedding_index()
    base_product = next(
        (
            product for product in metadata
            if str(product.get("product_id") or product.get("id")) == str(product_id)
        ),
        None,
    )

    if base_product is None:
        print(f"No product found with id {product_id}.")
        return

    results = recommend_outfit(
        base_product,
        metadata,
        embeddings=embeddings,
        metadata=metadata,
        top_k_per_category=top_k_per_category,
    )
    print(f"Outfit ideas for {base_product.get('title')}:")
    print_search_results(results)


def main():
    parser = argparse.ArgumentParser(description="ReBloom CLIP AI service.")
    parser.add_argument("--products", default=str(DEFAULT_PRODUCTS_PATH))
    parser.add_argument("--embeddings", default=str(DEFAULT_EMBEDDINGS_PATH))
    parser.add_argument("--metadata", default=str(DEFAULT_METADATA_PATH))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--build-embeddings", action="store_true")
    parser.add_argument("--search-image")
    parser.add_argument("--similar-product")
    parser.add_argument("--outfit")
    parser.add_argument("--top-k-per-category", type=int, default=1)
    args = parser.parse_args()

    if args.build_embeddings:
        result = build_product_embeddings(
            products_path=args.products,
            embeddings_path=args.embeddings,
            metadata_path=args.metadata,
        )
        print(f"Built embeddings: {result['count']}")
        if result["skipped"]:
            print("Skipped missing images:")
            for item in result["skipped"]:
                print(f"- {item}")
        return

    if args.search_image:
        results = search_by_image(
            args.search_image,
            embeddings_path=args.embeddings,
            metadata_path=args.metadata,
            top_k=args.top_k,
        )
        print_search_results(results)
        return

    if args.similar_product:
        results = find_similar_products(
            args.similar_product,
            embeddings_path=args.embeddings,
            metadata_path=args.metadata,
            top_k=args.top_k,
        )
        print_search_results(results)
        return

    if args.outfit:
        run_outfit(args.outfit, args.top_k_per_category)
        return

    products = load_products(args.products)
    print(f"Loaded {len(products)} products from {args.products}")
    parser.print_help()


if __name__ == "__main__":
    main()
