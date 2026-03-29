#!/usr/bin/env python3
"""Project management CLI with subcommands."""

import argparse
import json
import sys


def handle_init(args):
    """Initialize a new project."""
    result = {
        "action": "init",
        "project_name": args.name,
        "template": args.template,
    }
    print(json.dumps(result, separators=(",", ":")))


def handle_status(args):
    """Show project status."""
    result = {
        "action": "status",
        "verbose": args.verbose,
    }
    print(json.dumps(result, separators=(",", ":")))


def handle_deploy(args):
    """Deploy the project."""
    result = {
        "action": "deploy",
        "environment": args.env,
        "version": args.version,
        "dry_run": args.dry_run,
    }
    if args.env == "production" and not args.dry_run:
        result["confirmation_required"] = True
    print(json.dumps(result, separators=(",", ":")))


def main():
    parser = argparse.ArgumentParser(description="Project management CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init subcommand
    init_parser = subparsers.add_parser("init", help="Initialize a new project")
    init_parser.add_argument("--name", required=True, help="Project name")
    init_parser.add_argument("--template", default="basic", help="Project template")
    init_parser.set_defaults(func=handle_init)

    # status subcommand
    status_parser = subparsers.add_parser("status", help="Show project status")
    status_parser.add_argument("--verbose", action="store_true", help="Verbose output")
    status_parser.set_defaults(func=handle_status)

    # deploy subcommand
    deploy_parser = subparsers.add_parser("deploy", help="Deploy the project")
    deploy_parser.add_argument("--env", choices=["staging", "production"], required=True, help="Target environment")
    deploy_parser.add_argument("--version", required=True, help="Version to deploy")
    deploy_parser.add_argument("--dry-run", action="store_true", help="Simulate deployment without executing")
    deploy_parser.set_defaults(func=handle_deploy)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
