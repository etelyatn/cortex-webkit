# cortex-webkit Tech Debt

## WEBKIT-TD-001 — Lock file not implemented in lifecycle manager

- **Priority:** Low
- **Effort:** Small
- **Status:** Open

**Description:** `EditorLifecycleManager._launch_editor_sync` does not write a `CortexRestarting.lock` file during restart. The MCP `do_restart_editor` in `composites.py` has this lock. Without the lock, external hooks could launch a second editor during the restart window.

**Fix approach:** Add lock file write/cleanup in `_launch_editor_sync` with try/finally pattern, same as `composites.py`.

---

## WEBKIT-TD-002 — Duplicated launch logic between lifecycle manager and MCP composites

- **Priority:** Low
- **Effort:** Medium
- **Status:** Open

**Description:** The editor launch algorithm is duplicated between `EditorLifecycleManager._launch_editor_sync` and MCP's `do_restart_editor` in `composites.py`. The design spec intended the lifecycle manager to import and call `do_restart_editor` directly, but the `tools/` directory is not a proper Python package importable from `cortex-webkit`.

**Fix approach:** Either (a) move `do_restart_editor` into a shared library that both `cortex-webkit` and `cortex-mcp` install as a dependency, or (b) install `cortex-mcp` as a formal dependency of `cortex-webkit` and expose the tools via proper package structure.
