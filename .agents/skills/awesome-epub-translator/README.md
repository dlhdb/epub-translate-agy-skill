# Awesome ePub Translator (Antigravity Skill)

這是一個專為 Antigravity 環境打造的電子書自動翻譯技能（Workspace Skill）。本技能透過多代理（Multi-Agent）並行處理技術，能夠在保留原始排版、圖片與程式碼結構的前提下，將整本 ePub 電子書翻譯為您指定的目標語言。

---

## 🚀 使用方式 (Usage)

本技能已經整合至您的 Antigravity 環境中。您不需要輸入複雜的指令，只需在對話框中直接要求 Agent 進行翻譯即可。

### 基本範例
- "Translate `/path/to/my_book.epub` to Traditional Chinese."
- "請幫我把 `book.epub` 翻譯成繁體中文。"

### 進階參數範例
您可以透過自然語言指定更多細節：
- **雙語模式**："幫我翻譯 `book.epub` 成中文，請使用**雙語對照模式 (bilingual mode)**。"
- **指定風格**："將這本小說翻譯成日文，請使用**輕鬆幽默的語氣**。"
- **高品質 QA 模式**："翻譯 `book.epub` 到繁體中文，請**啟用高品質模式 (--high-quality)** 進行深度語意審查。"
- **指定子代理模型**："翻譯 `book.epub` 到繁體中文，翻譯模型請使用 `--translator-model google/gemini-flash-lite-latest`，QA 審查請使用 `--qa-model google/gemini-flash-latest`。"
- **自訂輸出路徑**："翻譯完成後，請將檔案另存到 `~/Desktop/translated_book.epub`。"

### 完整範例 (Full Example)
您可以將多項參數整合為一個完整指令，一次指定雙語對照、高品質審查以及自訂模型：
- **中文範例**：
  > "翻譯 `/path/to/book.epub` 到繁體中文，啟用高品質模式，使用雙語對照模式，翻譯模型指定為 `google/gemini-flash-lite-latest`，QA 審查模型指定為 `google/gemini-flash-latest`。"
- **英文範例**：
  > "Translate `/path/to/book.epub` to Traditional Chinese in bilingual mode with `--high-quality`, using `--translator-model google/gemini-flash-lite-latest` and `--qa-model google/gemini-flash-latest`."

---

## ✨ 核心特色

1. **風格畫像 (Style Profile)**：
   翻譯開始前，系統會先閱讀前幾個章節，自動提取書籍的文體、語氣與詞彙習慣（例如：學術嚴謹、或是輕鬆對話），並在後續的所有翻譯中保持這個風格。
2. **多代理並行加速 (Parallel Subagents)**：
   自動根據檔案大小進行智能分配，透過 Antigravity 的 `invoke_subagent` 呼叫最多 3 個子代理同時進行翻譯，大幅提升翻譯長篇書籍的速度。
3. **無縫雙語模式 (Bilingual Mode)**：
   除了純譯本外，支援產生中英（或原譯）對照的排版，並自動注入專屬的 CSS 樣式，方便語言學習者閱讀。
4. **高品質 Maker-Checker 語意審查 (High Quality QA)**：
   在 `--high-quality` 模式下，主協調者採用星狀架構調度獨立的 QA 審查員 (`epub-qa-reviewer`) 進行深度語意與標籤檢查；若發現漏翻或生硬句法即啟動自我糾錯迴圈，同時 100% 相容 OpenCode 與 Antigravity。
5. **自動斷點續傳 (Resumability)**：
   翻譯過程會建立 `_translation_work/` 暫存目錄並記錄審查狀態。如果遇到網路中斷或 Token 耗盡，重新要求翻譯同一個檔案時，系統會自動跳過已完成審查的章節。

---

## ⚠️ 其他重要資訊與系統需求

1. **系統依賴**：
   此技能依賴系統指令 `unzip` 來解壓縮 ePub，以及 `zip`（或 `python3` 作為備案）來將翻譯後的檔案重新打包成電子書。通常 macOS/Linux 環境皆已內建。
2. **Token 與時間消耗**：
   翻譯一整本書（特別是超過 20 章節的書籍）會消耗較大的 Token 量與時間。建議您可以先觀察第一回合（Round 1）的翻譯結果，技能會在每回合結束時向您報告進度。
3. **DRM 保護限制**：
   本工具無法翻譯帶有 DRM（數位版權管理）加密的電子書。若偵測到 DRM 加密，系統會自動停止翻譯並回報錯誤。
4. **格式限制**：
   對於固定版面（Fixed-layout）的 ePub 或是包含大量複雜巢狀 SVG 標籤的排版，翻譯後可能會有部分版面偏移。程式碼區塊（`<pre><code>`）預設會受到保護不被翻譯。
