GATE: PASS

## Attempt 1

Verdict: PASS
Command: ./check.sh
Build: 33e7ed1b58ace4db
Exit: 0
Seconds: 191.3
Waited: 0.0
Tree: unchanged

Last 80 lines of its output:

    ........................................................................ [  9%]
    ........................................................................ [ 11%]
    ........................................................................ [ 13%]
    ........................................................................ [ 15%]
    ........................................................................ [ 17%]
    ........................................................................ [ 19%]
    ........................................................................ [ 21%]
    ........................................................................ [ 23%]
    ........................................................................ [ 25%]
    ........................................................................ [ 27%]
    ........................................................................ [ 29%]
    .................................................ss..................... [ 31%]
    ........................................................................ [ 33%]
    ........................................................................ [ 35%]
    ........................................................................ [ 37%]
    ........................................................................ [ 39%]
    ........................................................................ [ 41%]
    ........................................................................ [ 43%]
    ........................................................................ [ 45%]
    ........................................................................ [ 47%]
    ........................................................................ [ 49%]
    ........................................................................ [ 51%]
    ........................................................................ [ 53%]
    ........................................................................ [ 55%]
    ........................................................................ [ 57%]
    ........................................................................ [ 59%]
    ........................................................................ [ 61%]
    ........................................................................ [ 63%]
    ........................................................................ [ 65%]
    ........................................................................ [ 67%]
    ........................................................................ [ 69%]
    ........................................................................ [ 71%]
    ........................................................................ [ 73%]
    ........................................................................ [ 75%]
    ........................................................................ [ 77%]
    ........................................................................ [ 79%]
    ........................................................................ [ 81%]
    ........................................................................ [ 83%]
    ........................................................................ [ 85%]
    ........................................................................ [ 87%]
    ........................................................................ [ 89%]
    ........................................................................ [ 91%]
    ........................................................................ [ 93%]
    ..........................................s............................. [ 95%]
    ........................................................................ [ 97%]
    ........................................................................ [ 99%]
    ..............................                                           [100%]
    3601 passed, 29 skipped in 189.78s (0:03:09)
    Validating marketplace manifest: <path-to-clone>/.claude/worktrees/204-scorecard-reads-true/.claude-plugin/marketplace.json
    
    Plugin directory checks for <path-to-clone>/.claude/worktrees/204-scorecard-reads-true. The plugin directory is the catalog that plugins are submitted to; this is a subset of what it runs.
    
    ⚠ Found 1 plugin directory warning:
    
      ❯ .claude-plugin/plugin.json icon: No icon (ICON_MISSING). No icon found in the plugin. The validator looked for `icon` in plugin.json and for a file at .claude-plugin/icon.png or .svg, assets/icon.png or .svg, or a similar path.
        Fix: Add a square PNG to the plugin folder at .claude-plugin/icon.png, or set `icon` in plugin.json to the path of a square PNG or JPEG in the plugin: 512 to 2048 px on each side, under 2 MB. SVG and WebP are not accepted. That file may become the listing icon only once: the first time the plugin is saved or submitted in the developer portal. Adding or changing it later does not change the icon.
    
    About these checks:
    
      ❯ This folder also holds a marketplace manifest. The plugin directory treats such a folder as a plugin, so these checks cover only the plugin in this folder. To check another plugin that the marketplace lists, run validate on that plugin's folder.
    
    These plugin directory checks do not change the result below.
    
    The directory also runs a safety scan and a policy review that this command does not.
    
    ✔ Validation passed
    Validating plugin manifest: <path-to-clone>/.claude/worktrees/204-scorecard-reads-true/plugins/factory/.claude-plugin/plugin.json
    
    Plugin directory checks for <path-to-clone>/.claude/worktrees/204-scorecard-reads-true/plugins/factory. The plugin directory is the catalog that plugins are submitted to; this is a subset of what it runs.
    
    ⚠ Found 1 plugin directory warning:
    
      ❯ .claude-plugin/plugin.json icon: No icon (ICON_MISSING). No icon found in the plugin. The validator looked for `icon` in plugin.json and for a file at .claude-plugin/icon.png or .svg, assets/icon.png or .svg, or a similar path.
        Fix: Add a square PNG to the plugin folder at .claude-plugin/icon.png, or set `icon` in plugin.json to the path of a square PNG or JPEG in the plugin: 512 to 2048 px on each side, under 2 MB. SVG and WebP are not accepted. That file may become the listing icon only once: the first time the plugin is saved or submitted in the developer portal. Adding or changing it later does not change the icon.
    
    These plugin directory checks do not change the result below.
    
    The directory also runs a safety scan and a policy review that this command does not.
    
    ✔ Validation passed
