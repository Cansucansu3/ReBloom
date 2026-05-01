import argparse

from ai.extract_embeddings import build_embeddings, load_products, save_embeddings
from ai.llm_explainer import explain_match, explain_outfit
from ai.outfit_recommender import recommend_outfit
from ai.similarity import load_embeddings, search_similar_products


def ensure_embeddings():
    products = load_products()
    records = build_embeddings(products)
    save_embeddings(records)
    return products, records


def run_search(query):
    try:
        records = load_embeddings()
    except FileNotFoundError:
        _, records = ensure_embeddings()

    results = search_similar_products(query, records)

    for result in results:
        product = result["product"]
        print(f"- {product['title']} ({result['score']:.2f})")
        print(f"  {explain_match(query, result)}")


def run_outfit(product_id):
    products, _ = ensure_embeddings()
    seed_product = next(
        (product for product in products if product["product_id"] == str(product_id)),
        None,
    )

    if not seed_product:
        print(f"No product found with id {product_id}")
        return

    recommendations = recommend_outfit(seed_product, products)
    print(f"Outfit ideas for {seed_product['title']}:")

    for recommendation in recommendations:
        product = recommendation["product"]
        print(f"- {product['title']}")
        print(f"  {explain_outfit(seed_product, recommendation)}")


def main():
    parser = argparse.ArgumentParser(description="ReBloom AI service demo.")
    parser.add_argument("--build-embeddings", action="store_true")
    parser.add_argument("--search")
    parser.add_argument("--outfit", type=int)
    args = parser.parse_args()

    if args.build_embeddings:
        products, _ = ensure_embeddings()
        print(f"Built embeddings for {len(products)} products.")
    elif args.search:
        run_search(args.search)
    elif args.outfit:
        run_outfit(args.outfit)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
