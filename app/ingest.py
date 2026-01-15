import argparse
import asyncio

from dotenv import load_dotenv

from app.services.ingest import (
    default_docs_dir,
    default_pairs_path,
    index_pairs,
    parse_documents,
)


load_dotenv()


async def run(args: argparse.Namespace) -> None:
    no_flags = not args.parse and not args.index
    do_parse = args.parse or no_flags
    do_index = args.index or no_flags
    do_reset = args.reset or no_flags

    if do_parse:
        await parse_documents(args.docs, args.pairs)
    if do_index:
        await index_pairs(args.pairs, reset=do_reset)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest FAQ documents.")
    parser.add_argument("--parse", action="store_true", help="Parse docs to Q/A.")
    parser.add_argument("--index", action="store_true", help="Index Q/A into Chroma.")
    parser.add_argument("--reset", action="store_true", help="Reset Chroma collection.")
    parser.add_argument("--docs", default=default_docs_dir(), help="Docs directory.")
    parser.add_argument(
        "--pairs", default=default_pairs_path(), help="Output pairs JSON."
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
