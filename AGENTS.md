# AGENTS.md

This file provides guidance to Antigravity Agents when working with code and files in this repository.

## Project Overview

This is an experimental workspace for AI document and ePub translation. It leverages the Antigravity (AGY) multi-agent framework to translate ePub files between languages using the agent itself as the translation engine. The primary logic is expressed as natural-language instructions in Markdown files — specifically, within Antigravity Workspace Skills.

The translation workflow is triggered when users ask the agent to translate an ePub (e.g., "translate this ePub to Traditional Chinese", "翻譯這本書").

## Architecture

```text
/
└── .agents/
    └── skills/
        └── awesome-epub-translator/       # Antigravity Skill package
            ├── README.md                  # Skill introduction and documentation
            ├── SKILL.md                   # Main skill definition: frontmatter, workflow instructions, error handling
            └── references/
                ├── translation-prompt.md  # Translation prompt template with {STYLE_PROFILE}, {TARGET_LANGUAGE} placeholders
                └── epub-structure.md      # ePub format quick reference
```

- **.agents/skills/awesome-epub-translator/**: Contains the custom Antigravity skill that orchestrates the translation.
  - **SKILL.md** is the skill entry point. Its YAML frontmatter controls skill discovery and triggering. The body contains the step-by-step workflow the agent follows when translating.
  - **references/** files are read by the agent during execution to maintain rule adherence (e.g., `translation-prompt.md`).

## Key Design Decisions

- **Multi-Agent Parallelism**: Uses Antigravity's `invoke_subagent` tool to spawn subagents concurrently (up to 3), greatly speeding up the translation of large ePubs compared to sequential processing.
- **Zero External Tool Dependencies**: Only requires `unzip` (extraction) and `zip` or Python 3 (repackaging), which are available in standard macOS/Linux environments. The agent reads and writes files directly using native workspace tools.
- **Style Profile System**: Before translating the whole book, the agent reads early chapters to analyze the book's genre, tone, and voice, saving a profile to `style_profile.md`. This profile is passed to subagents to ensure consistent tone across all translated chapters.
- **Checkpoint-based Resumability**: Translated chapters are saved in a temporary directory. If the agent hits a context limit, network error, or simply pauses, re-running the skill will skip already-translated XHTML files.
- **Bilingual Mode**: An optional mode where the agent interleaves the original text and the translated text with specific CSS classes, ideal for language learners.

## Work Directory & Debugging

When a translation is in progress, a temporary `<filename>_translation_work/` directory is created alongside the source ePub. This is crucial for debugging if a translation fails:
- `_translated/`: Contains the generated `style_profile.md` and all successfully translated chapters. Check this folder to verify if translated XHTML files have valid, closed tags.
- `_staging/`: Used during the repackaging phase before the final zip is created.
Agents should always investigate this work directory if an ePub fails to repackage or render correctly.

## Limitations & Edge Cases

When handling user requests or modifying the workflow, keep these limitations in mind:
- **DRM Protection**: The skill does not support translating DRM-encrypted ePubs (detectable via `META-INF/encryption.xml`).
- **ePub Format Differences**: ePub 2 uses `toc.ncx` while ePub 3 uses `toc.xhtml`. The skill explicitly handles both.
- **Layout Constraints**: Fixed-layout ePubs may experience visual shifts post-translation. Embedded text within images or SVG tags is not translated.

## Working on This Project

Since the core skill is defined purely in Markdown, "development" means editing the instruction files:

- **Changing workflow behavior**: Edit `.agents/skills/awesome-epub-translator/SKILL.md`
- **Changing translation rules**: Edit `.agents/skills/awesome-epub-translator/references/translation-prompt.md`
- **Testing**: Ask the agent to translate a file and verify the behavior.

## Conventions

- **Tool Usage Constraints (CRITICAL)**: Never use the `replace_file_content` tool to translate or modify XHTML content blocks. The Edit/find-replace approach frequently fails on large files due to missing unique string matches and exhausts context limits. Always read the file into memory, translate it, and use `write_to_file` to write the complete XHTML file in one shot.
- The Antigravity skill instructions (`SKILL.md`, `references/*.md`) are primarily written in English or Traditional Chinese.
- Follow the multi-agent design pattern when extending the translation skill to avoid hitting context limits on a single agent.
- Output artifacts (reports, diagrams) should be created using Antigravity's artifact system.
