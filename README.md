# Awesome ePub Translator (OpenCode Workspace)

這是一個專為 OpenCode 多代理（Multi-Agent）架構設計的電子書翻譯專案。

本專案的核心是一個**完全獨立且可攜帶 (Portable)** 的技能 (Skill)：`awesome-epub-translator`，搭配 OpenCode 子代理人 (`epub-translator` 與 `epub-qa-reviewer`)。它能夠在保留原始排版的前提下，將整本 ePub 電子書翻譯為指定的目標語言。

## 📦 如何在你的專案中使用這個技能（安裝方式）

這個翻譯技能被設計為模組化架構。如果你想在自己的 OpenCode 專案或全域環境中使用這個翻譯功能：

1. 複製本專案中的 `.agents/skills/awesome-epub-translator/` 資料夾到目標專案的 `.agents/skills/` 目錄。
2. 複製本專案中的 `.opencode/agents/` 資料夾到目標專案的 `.opencode/agents/` 目錄。
3. 關於該技能的詳細特色、使用範例與系統需求，請直接參閱該技能內建文檔：
   👉 [**Skill README**](.agents/skills/awesome-epub-translator/README.md)

## 🚀 在本專案直接體驗 (Quick Start)

如果你想測試翻譯效果，你可以直接在 OpenCode 中開啟此專案工作區進行翻譯：

1. 將你要翻譯的 `.epub` 檔案放入這個專案的目錄中。
2. 開啟 OpenCode 進入此目錄。
3. 直接向 Agent 下達指令，例如：
   > "請幫我把 `book.epub` 翻譯成繁體中文，請使用雙語對照模式。"

   > 💡 **更詳細的 Prompt 範例與進階用法**（如：指定翻譯風格、自訂儲存路徑、高品質 QA 模式等），請參閱 👉 [Skill 完整使用說明](.agents/skills/awesome-epub-translator/README.md#🚀-使用方式-usage)

## 📂 專案核心結構

- [`.agents/skills/awesome-epub-translator/`](.agents/skills/awesome-epub-translator/)：翻譯技能的核心模組，包含完整工作流指示、提示詞與文檔。
- [`.opencode/agents/`](.opencode/agents/)：OpenCode 子代理人設定檔（`epub-translator` 與 `epub-qa-reviewer`）。
- [`AGENTS.md`](AGENTS.md)：提供給 OpenCode Agent 閱讀的專案級別守則（Repository Rules），幫助 Agent 了解這個工作區的架構與設計決策。
- `README.md`：您現在正在閱讀的專案說明。

---

## 📚 參考專案 (Reference Project)

本技能的核心邏輯與提示詞架構移植自開源專案 [awesome-epub-translator-skill](https://github.com/ludengz/awesome-epub-translator-skill)。
- **原始作者**：ludengz
- **適配說明**：本版本已對核心底層進行深度改寫，轉換為 OpenCode 原生的 `read`、`write`、`subagent` 工具呼叫，並結合 Two-Pass 記憶體自我批判（Two-Pass Self-Reflection）與星狀 QA 審查架構實現高品質並行翻譯與審查。
