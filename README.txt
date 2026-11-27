================================================================================
OBSIDIAN VAULT CRYPT CONTROLLER (vault_ctl.py) - SETUP & USAGE GUIDE
Target OS : Windows (user-scoped) and Linux
Repo      : https://github.com/Slice0fBreadByte/obsidian-vault-crypt.git
Remote    : obsidian_crypt:
================================================================================

1. PREREQUISITES
--------------------------------------------------------------------------------
- Python 3 (standard library only; no third-party pip packages required)
- Git (configured with HTTPS/SSH access to Slice0fBreadByte/obsidian-vault-crypt)
- Rclone (configured with encrypted remote `obsidian_crypt:`)
- Secrets in LastPass:
    * rclone.conf master/config password
    * crypt password and password2 salt

--------------------------------------------------------------------------------
2. GIT CONFIGURATION (NEW MACHINE)
--------------------------------------------------------------------------------
[Windows - PowerShell]
# Set basic Git identity (if not already set globally)
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# Clone the encrypted staging repository
git clone https://github.com/Slice0fBreadByte/obsidian-vault-crypt.git "$env:USERPROFILE\obsidian-encrypted-stage"

# Enable long paths to avoid Windows MAX_PATH errors on deep encrypted paths
git -C "$env:USERPROFILE\obsidian-encrypted-stage" config core.longpaths true

# Verify remote and branch
git -C "$env:USERPROFILE\obsidian-encrypted-stage" remote -v
git -C "$env:USERPROFILE\obsidian-encrypted-stage" branch -a

[Linux - Bash/Zsh]
# Set basic Git identity (if not already set globally)
git config --global user.name "Your Name"
git config --global user.email "you@example.com"

# Clone the encrypted staging repository
git clone https://github.com/Slice0fBreadByte/obsidian-vault-crypt.git "$HOME/obsidian-encrypted-stage"

# Verify remote and branch
git -C "$HOME/obsidian-encrypted-stage" remote -v
git -C "$HOME/obsidian-encrypted-stage" branch -a

--------------------------------------------------------------------------------
3. RCLONE CONFIGURATION (NEW MACHINE)
--------------------------------------------------------------------------------
[Windows - PowerShell]
# Create Rclone config directory and restore rclone.conf
New-Item -ItemType Directory -Force -Path "$env:APPDATA\rclone"
# Copy your rclone.conf into: %APPDATA%\rclone\rclone.conf

# Test remote access (enter rclone.conf master password from LastPass)
rclone listremotes

[Linux - Bash/Zsh]
# Create Rclone config directory and restore rclone.conf
mkdir -p "$HOME/.config/rclone"
# Copy your rclone.conf into: ~/.config/rclone/rclone.conf

# Test remote access (enter rclone.conf master password from LastPass)
rclone listremotes

Note on `obsidian_crypt:` target:
- Ensure `obsidian_crypt:` points to `<REPO_ROOT>/vault` (for example,
  C:\Users\<user>\obsidian-encrypted-stage\vault on Windows or
  ~/obsidian-encrypted-stage/vault on Linux) with `standard` filename
  encryption and `directory` encryption enabled.

Optional session-only password (avoids re-entering per subcommand in one shell):
- Windows PowerShell : $env:RCLONE_CONFIG_PASS = "<your-config-password>"
- Linux Bash/Zsh   : export RCLONE_CONFIG_PASS="<your-config-password>"

--------------------------------------------------------------------------------
4. PLACE vault_ctl.py ON USER PATH
--------------------------------------------------------------------------------
- Windows: Save script at C:\Users\<user>\bin\vault_ctl.py (ensure bin is in
  user PATH). Confirm REPO_ROOT = Path.home() / "obsidian-encrypted-stage".
- Linux  : Save script at ~/bin/vault_ctl.py (ensure ~/bin is in PATH) and
  confirm REPO_ROOT = Path.home() / "obsidian-encrypted-stage".

--------------------------------------------------------------------------------
5. USAGE OF vault_ctl.py
--------------------------------------------------------------------------------
[Help & Examples]
# Windows
python "$env:USERPROFILE\bin\vault_ctl.py"
python "$env:USERPROFILE\bin\vault_ctl.py" help
python "$env:USERPROFILE\bin\vault_ctl.py" man

# Linux
python3 ~/bin/vault_ctl.py
python3 ~/bin/vault_ctl.py help
python3 ~/bin/vault_ctl.py man

[Pull & Decrypt (Git pull --rebase + rclone copy to destination)]
# Windows (test folder example)
python "$env:USERPROFILE\bin\vault_ctl.py" pull --dest "$env:USERPROFILE\vault_decrypt_test" -v

# Linux
python3 ~/bin/vault_ctl.py pull --dest ~/ObsidianVault -v

[Encrypt, Commit & Push (rclone sync to obsidian_crypt: + git add/commit/push)]
# Windows
python "$env:USERPROFILE\bin\vault_ctl.py" sync --source "D:\Documents\Obsidian Vault" --message "vault sync" -v

# Linux
python3 ~/bin/vault_ctl.py sync --source ~/ObsidianVault --message "vault sync" -v

[Dry-Run Preview (no file writes, no git commit, no git push)]
# Windows
python "$env:USERPROFILE\bin\vault_ctl.py" sync --source "D:\Documents\Obsidian Vault" --message "test" --dry-run -v
python "$env:USERPROFILE\bin\vault_ctl.py" pull --dest "$env:USERPROFILE\vault_decrypt_test" --dry-run -v

# Linux
python3 ~/bin/vault_ctl.py sync --source ~/ObsidianVault --message "test" --dry-run -v
python3 ~/bin/vault_ctl.py pull --dest ~/vault_decrypt_test --dry-run -v

[Optional Flags]
--branch <name>   Git branch to pull from or push to (default: main)
--message <text>  Commit message for `sync` (default: "vault sync")
-v, --verbose     Pass -v to Rclone for detailed per-file output
--dry-run         Preview actions without modifying files or pushing to GitHub
================================================================================
