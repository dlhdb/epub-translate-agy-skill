# Awesome ePub Translator (Antigravity Workspace)

這是一個基於 Antigravity (AGY) 多代理（Multi-Agent）框架的電子書翻譯實驗性專案。

本專案的核心是一個**完全獨立且可攜帶 (Portable)** 的 Antigravity 技能 (Workspace Skill)：`awesome-epub-translator`。它能夠在保留原始排版的前提下，將整本 ePub 電子書翻譯為指定的目標語言。

## 📦 如何在你的專案中使用這個技能（安裝方式）

這個翻譯技能被設計為完全自給自足的模組。如果你想在自己的專案或全域環境中使用這個翻譯功能，**只需複製貼上即可**：

1. 複製本專案中的 `.agents/skills/awesome-epub-translator/` 整個資料夾。
2. 將它貼到你目標專案的 `.agents/skills/` 目錄下（或是你的全域技能目錄中）。
3. 關於該技能的詳細特色、Prompt 使用範例與系統需求，請直接參閱該技能內建的文檔：
   👉 [**Skill README**](.agents/skills/awesome-epub-translator/README.md)

## 🚀 在本專案直接體驗 (Quick Start)

如果你只是想測試翻譯效果，你可以直接將這個 Repository 作為 Antigravity 的工作區來進行翻譯：

1. 將你要翻譯的 `.epub` 檔案放入這個專案的根目錄中。
2. 開啟 Antigravity IDE 或使用 AGY CLI 進入此目錄。
3. 直接向 Agent 下達指令，例如：
   > "請幫我把 `book.epub` 翻譯成繁體中文，請使用雙語對照模式。"

   > 💡 **更詳細的 Prompt 範例與進階用法**（如：指定翻譯風格、自訂儲存路徑等），請參閱 👉 [Skill 完整使用說明](.agents/skills/awesome-epub-translator/README.md#🚀-使用方式-usage)

## 📂 專案核心結構

- [`.agents/skills/awesome-epub-translator/`](.agents/skills/awesome-epub-translator/)：翻譯技能的核心模組，包含完整的提示詞、工作流指示與文檔。
- [`AGENTS.md`](AGENTS.md)：提供給 Antigravity Agent 閱讀的專案級別守則（Repository Rules），幫助 Agent 了解這個工作區的架構與設計決策。
- `README.md`：您現在正在閱讀的專案說明。

---

## 📚 參考專案 (Reference Project)

本技能的核心邏輯與提示詞架構移植自開源專案 [awesome-epub-translator-skill](https://github.com/ludengz/awesome-epub-translator-skill)。
- **原始作者**：ludengz
- **原始環境**：專為 Claude Code 打造的外掛（Plugin）。
- **適配說明**：本版本已對核心底層進行深度改寫，將原有的 Claude Code 工具呼叫轉換為 Antigravity 原生的 `view_file`、`write_to_file` 工具，並利用 `invoke_subagent` 實現並行處理。
