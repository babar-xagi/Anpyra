# ⚙️ Project Configuration

Anpyra reads one `[app]` table from `anpyra.toml`. It does not use the repository's `pyproject.toml` as application configuration.

## 📝 Complete configuration

```toml
[app]
package = "dev.example.myapp"
label = "My App"
entry = "app.py"
version_code = 1
version_name = "0.1.0"
min_sdk = 24
target_sdk = 36
output_dir = "build"
```

## 📋 Setting reference

| Setting | Default | Meaning and validation |
| --- | --- | --- |
| `package` | `dev.anpyra.app` | Application ID; at least two lowercase segments, each starting with a letter and then letters/digits/underscores |
| `label` | `Anpyra` | Display label; nonempty string, Unicode accepted, no NUL |
| `entry` | `app.py` | Source path relative to project root |
| `version_code` | `1` | Positive signed 32-bit integer; booleans/strings rejected |
| `version_name` | `0.1.0` | Nonempty human-readable version string |
| `min_sdk` | `24` | Positive integer, at least 24 |
| `target_sdk` | `36` | Positive integer at least `min_sdk` |
| `output_dir` | `build` | Separate output directory relative to project root |

Omitted settings use defaults. Unknown keys and extra top-level tables are rejected, so `lable` is an error rather than an ignored typo. Integer fields must use unquoted TOML integers.

The target SDK default retains the experiments' API 36 value. It is not a promise that current store policies have been met. The minimum SDK reflects the [v2-only signing profile](https://source.android.com/docs/security/features/apksigning/v2); lowering it to 23 is rejected.

## 🗂️ Relative paths

This arrangement works:

```text
myapp/
├── anpyra.toml
├── application/
│   └── main.py
└── build/            # Generated
```

Set `entry = "application/main.py"` and `output_dir = "build"`. This changes the entry location only; multi-module imports are still unsupported.

Paths are resolved against the configuration file's directory, not your shell's current directory. Absolute paths, drive-qualified paths, paths escaping the project, output containing the entry, and overlap with `.anpyra/` are rejected. Resolved symlink targets must stay inside the project for project-managed paths.

## 🧭 Select a project

Both forms are accepted:

```powershell
anpyra build myapp
anpyra build myapp/anpyra.toml
```

After moving into the application directory:

```powershell
cd myapp
anpyra build
```

Running `anpyra build` in the framework checkout root fails unless you create an application configuration there. Prefer a separate app directory.

## 🔑 Package and signing identity

The package ID determines the generated Activity's namespace and the APK filename, such as `dev.example.myapp.apk`. The Activity class name comes from source, not a config setting.

The debug identity lives at `.anpyra/debug-key.pem` and `.anpyra/debug-cert.der`. There is no `signing`, release-mode, icon, permission or resources setting yet. The direct Python build API can select a `state_dir`; project builds use `.anpyra/`.

When updating an installed app, retain its package and identity. Changing only the label changes display metadata; changing the package gives a separate application ID.
