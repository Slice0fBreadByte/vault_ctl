import argparse
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

# --- CONFIGURATION ---
REPO_ROOT = Path.home() / "obsidian-encrypted-stage"
RCLONE_REMOTE = "obsidian_crypt:"
DEFAULT_BRANCH = "main"
STATS_INTERVAL = "3s"
# ---------------------

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)

USAGE_EXAMPLES = """\
Usage Examples:
  1. Pull latest encrypted commits and decrypt to a folder:
     python vault_ctl.py pull --dest ~/vault_decrypt_test -v

  2. Encrypt plaintext vault, commit to staging repo, and push:
     python vault_ctl.py sync --source ~/ObsidianVault --message "notes update" -v

  3. Preview pull or sync actions without modifying files or pushing:
     python vault_ctl.py pull --dest ~/vault_decrypt_test --dry-run -v
     python vault_ctl.py sync --source ~/ObsidianVault --dry-run -v

  4. Show help or these examples:
     python vault_ctl.py
     python vault_ctl.py help
     python vault_ctl.py man
"""


def log(msg: str, stream=sys.stdout) -> None:
    print(msg, file=stream, flush=True)


def detect_os() -> tuple[str, str]:
    system = platform.system().lower()
    release = platform.release().lower()

    if system == "windows":
        return "windows", f"Windows ({platform.release()})"

    if system == "linux":
        if os.environ.get("TERMUX_VERSION") or "com.termux" in os.environ.get("PREFIX", ""):
            return "termux", f"Android / Termux ({platform.release()})"
        if "microsoft" in release or "wsl" in release or os.environ.get("WSL_DISTRO_NAME"):
            distro = os.environ.get("WSL_DISTRO_NAME", "Linux")
            return "wsl", f"WSL ({distro}, {platform.release()})"
        return "linux", f"Linux ({platform.release()})"

    return system or "unknown", f"{platform.system()} ({platform.release()})"


def print_manual(exit_code: int = 0) -> None:
    _, os_label = detect_os()
    log("vault_ctl.py - Obsidian Vault Sync (Encrypt + Push) & Pull (Fetch + Decrypt)\n")
    log(f"Detected OS: {os_label}\n")
    log("Commands:")
    log("  pull --dest <path> [--branch main] [-v] [--dry-run]")
    log("  sync --source <path> [--message <msg>] [--branch main] [-v] [--dry-run]")
    log("  help | man\n")
    log(USAGE_EXAMPLES)
    sys.exit(exit_code)


def require_tool(name: str) -> str:
    log(f"[CHECK] Locating '{name}' in PATH...")
    found = shutil.which(name)
    if not found:
        log(f"[ERROR] Missing required tool in PATH: {name}", sys.stderr)
        sys.exit(1)
    log(f"[OK] Found {name}: {found}")
    return found


def run_cmd(cmd: list[str], cwd: Path | None = None, dry_run: bool = False, label: str | None = None) -> None:
    start = time.monotonic()
    where = f" (cwd={cwd})" if cwd else ""
    if label:
        log(f"[STEP] {label}")
    log(f"[RUN]{where} {' '.join(cmd)}")
    if dry_run:
        log("[SKIP] Dry-run mode active; command not executed.")
        return

    result = subprocess.run(cmd, cwd=cwd)
    elapsed = time.monotonic() - start
    if result.returncode != 0:
        log(f"[ERROR] Command exited with status {result.returncode} after {elapsed:.1f}s", sys.stderr)
        sys.exit(result.returncode)
    log(f"[DONE] Finished in {elapsed:.1f}s")


def check_repo_and_remote(dry_run: bool = False) -> None:
    os_kind, os_label = detect_os()
    log(f"[INFO] Detected OS: {os_label}")
    log("[INFO] Running environment and configuration checks...")
    require_tool("git")
    require_tool("rclone")

    log(f"[CHECK] Verifying Git staging repository at {REPO_ROOT}...")
    if not (REPO_ROOT / ".git").is_dir():
        log(f"[ERROR] No Git repository found at {REPO_ROOT}", sys.stderr)
        if os_kind == "windows":
            log(f"[HINT] Clone with: git clone https://github.com/Slice0fBreadByte/obsidian-vault-crypt.git \"{REPO_ROOT}\"", sys.stderr)
        else:
            log(f"[HINT] Clone with: git clone https://github.com/Slice0fBreadByte/obsidian-vault-crypt.git \"{REPO_ROOT}\"", sys.stderr)
        sys.exit(1)
    log("[OK] Staging Git repository verified.")

    log("[CHECK] Reading Rclone remotes (enter rclone.conf master password if prompted)...")
    result = subprocess.run(["rclone", "listremotes"], stdout=subprocess.PIPE, stderr=None, text=True)
    if result.returncode != 0:
        log("[ERROR] Failed to read Rclone remotes (check master password or rclone.conf).", sys.stderr)
        sys.exit(1)

    remotes = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    if RCLONE_REMOTE not in remotes and not dry_run:
        log(
            f"[ERROR] Remote '{RCLONE_REMOTE}' not found. Available: {', '.join(sorted(remotes)) or 'none'}",
            sys.stderr,
        )
        sys.exit(1)
    log(f"[OK] Rclone remote '{RCLONE_REMOTE}' ready.")


def cmd_pull(args: argparse.Namespace) -> None:
    _, os_label = detect_os()
    log(f"[START] OS: {os_label} | Mode: PULL | Branch: {args.branch} | Dest: {args.dest} | Dry-run: {args.dry_run}")
    check_repo_and_remote(dry_run=args.dry_run)

    dest_path = Path(args.dest).expanduser()
    log(f"[CHECK] Preparing destination folder: {dest_path}")
    if not args.dry_run:
        dest_path.mkdir(parents=True, exist_ok=True)
        log("[OK] Destination folder ready.")

    run_cmd(
        ["git", "pull", "--rebase", "origin", args.branch],
        cwd=REPO_ROOT,
        dry_run=args.dry_run,
        label="Fetching and rebasing latest encrypted commits from GitHub",
    )

    rclone_cmd = ["rclone", "copy", RCLONE_REMOTE, str(dest_path), "--stats", STATS_INTERVAL]
    if args.verbose:
        rclone_cmd.append("-v")
    if args.dry_run:
        rclone_cmd.append("--dry-run")

    run_cmd(
        rclone_cmd,
        dry_run=False,
        label="Decrypting staged vault into destination folder",
    )
    log(f"[OK] Pull + decrypt complete -> {dest_path}")


def cmd_sync(args: argparse.Namespace) -> None:
    _, os_label = detect_os()
    log(f"[START] OS: {os_label} | Mode: SYNC | Branch: {args.branch} | Source: {args.source} | Dry-run: {args.dry_run}")
    check_repo_and_remote(dry_run=args.dry_run)

    src_path = Path(args.source).expanduser()
    log(f"[CHECK] Verifying source vault folder: {src_path}")
    if not src_path.is_dir():
        log(f"[ERROR] Source vault folder not found: {src_path}", sys.stderr)
        sys.exit(1)
    log("[OK] Source vault folder verified.")

    rclone_cmd = ["rclone", "sync", str(src_path), RCLONE_REMOTE, "--stats", STATS_INTERVAL]
    if args.verbose:
        rclone_cmd.append("-v")
    if args.dry_run:
        rclone_cmd.append("--dry-run")

    run_cmd(
        rclone_cmd,
        dry_run=False,
        label="Encrypting and syncing vault into staging folder",
    )

    run_cmd(
        ["git", "add", "-A"],
        cwd=REPO_ROOT,
        dry_run=args.dry_run,
        label="Staging encrypted changes in Git",
    )

    if args.dry_run:
        log(f"[DRY-RUN] Would check git status, commit with message {args.message!r}, and push to origin/{args.branch}.")
        return

    log("[CHECK] Checking Git working tree for changes...")
    status = subprocess.run(["git", "status", "--porcelain"], cwd=REPO_ROOT, capture_output=True, text=True)
    if not status.stdout.strip():
        log("[OK] No encrypted changes to commit or push.")
        return

    changed_count = len([line for line in status.stdout.splitlines() if line.strip()])
    log(f"[INFO] Detected {changed_count} changed/new encrypted entry(ies).")

    run_cmd(
        ["git", "commit", "-m", args.message],
        cwd=REPO_ROOT,
        label="Committing encrypted changes locally",
    )
    run_cmd(
        ["git", "push", "origin", args.branch],
        cwd=REPO_ROOT,
        label=f"Pushing encrypted commit to origin/{args.branch}",
    )
    log(f"[OK] Encrypted sync + push complete -> origin/{args.branch}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vault_ctl.py",
        description="Unified Obsidian vault sync (encrypt + push) and pull (fetch + decrypt) controller.",
        epilog=USAGE_EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("help", help="Show usage commands and examples.")
    subparsers.add_parser("man", help="Show usage commands and examples.")

    pull_p = subparsers.add_parser(
        "pull",
        help="Pull latest encrypted commits and decrypt to destination.",
        epilog=USAGE_EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    pull_p.add_argument("--dest", required=True, help="Plaintext destination folder path.")
    pull_p.add_argument("--branch", default=DEFAULT_BRANCH, help="Git branch (default: main).")
    pull_p.add_argument("-v", "--verbose", action="store_true", help="Pass -v to rclone.")
    pull_p.add_argument("--dry-run", action="store_true", help="Preview commands without writing or pushing.")
    pull_p.set_defaults(func=cmd_pull)

    sync_p = subparsers.add_parser(
        "sync",
        help="Encrypt plaintext vault, commit to staging repo, and push.",
        epilog=USAGE_EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sync_p.add_argument("--source", required=True, help="Plaintext local Obsidian vault folder path.")
    sync_p.add_argument("--message", default="vault sync", help="Git commit message (default: 'vault sync').")
    sync_p.add_argument("--branch", default=DEFAULT_BRANCH, help="Git branch (default: main).")
    sync_p.add_argument("-v", "--verbose", action="store_true", help="Pass -v to rclone.")
    sync_p.add_argument("--dry-run", action="store_true", help="Preview commands without writing or pushing.")
    sync_p.set_defaults(func=cmd_sync)

    return parser


def main() -> None:
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1].lower() in {"help", "man"}):
        print_manual(0)

    parser = build_parser()
    args = parser.parse_args()
    if args.command in {"help", "man"}:
        print_manual(0)
    args.func(args)


if __name__ == "__main__":
    main()