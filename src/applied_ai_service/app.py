"""Example entrypoint for the applied-ai-service package."""

import argparse


def main(argv=None):
    parser = argparse.ArgumentParser(prog="applied-ai-service")
    parser.add_argument("--demo", action="store_true", help="Run demo output")
    args = parser.parse_args(argv)

    if args.demo:
        print("Applied AI Service — demo running")
    else:
        print("Applied AI Service — no action specified. Use --demo to run demo.")


if __name__ == "__main__":
    main()
