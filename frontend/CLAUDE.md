@AGENTS.md

## Search Tooling

> **Use `rg` (ripgrep), never `grep`.** When shelling out to search files, run `rg` —
> it respects `.gitignore`, skips binaries, and is far faster than `grep`/`find -exec grep`.
> Reserve plain `grep` only for piping non-file streams.
