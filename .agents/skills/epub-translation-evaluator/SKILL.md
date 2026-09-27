---
name: epub-translation-evaluator
description: 評估並比較兩個 ePub 翻譯版本的品質差異 (A/B 測試驗證)
---

# 技能介紹
本技能用於評估 `awesome-epub-translator` 的翻譯品質。當使用者修改了 Prompt 或分配策略後，可透過此技能自動比對舊版 (V1) 與新版 (V2) 譯文的差異，進行客觀的 A/B 測試。

# 運作流程 (Orchestrator Workflow)

身為 Main Agent，當使用者要求執行「翻譯驗證」或「比較 V1 與 V2」時，請嚴格執行以下步驟：

## 1. 環境與參數確認
- 詢問或確認使用者提供的**測試案例目錄**。該目錄必須包含：
  - `source/`：原文 XHTML 或 HTML 檔案
  - `v1/`：舊版譯文檔案，以及舊版產生的 `style_profile.md`
  - `v2/`：新版譯文檔案，以及新版產生的 `style_profile.md`
- 在該目錄下建立 `_evaluation_work/` 暫存資料夾。

## 2. 結構快篩 (Structural Validation)
- 呼叫終端機工具 (`run_command`)，執行 `.agents/skills/epub-translation-evaluator/scripts/html_validator.py`。
- 分別傳入 `v1/` 與 `v2/` 的路徑進行檢查。
- 讀取腳本輸出的 JSON 報告。若有檔案回報 `valid: false` (如閉合標籤遺失)，請直接在你的筆記中將該版本的該檔案評為 1 分（災難性結構破壞）。

## 3. 語意深度評估 (Subagent Dispatch)
- 遍歷 `source/` 目錄中的所有 XHTML 或 HTML 章節檔案。
- 若該章節在 V1 或 V2 的結構檢查中已嚴重損毀，可選擇跳過語意評估。
- 針對結構正常的章節，使用 `invoke_subagent` 喚醒最多 3 個子代理並行處理。
- **派發給子代理的 Prompt 組合**：
  - 讀取 `references/subagent-prompt.md` 作為 System Prompt。
  - 讀取 `references/evaluation-rubric.md` 讓子代理了解標準。
  - 將原文內容，以及 V1 與 V2 各自對應的章節檔案與 `style_profile.md` 一併傳遞給子代理。
- 指示子代理嚴格按照 JSON 格式回報，並將結果寫入 `_evaluation_work/{chapter_name}.json`。

## 4. 數據匯總與最終報告
- 等待所有 Subagent 完成任務。
- 讀取 `_evaluation_work/` 中所有的 JSON 檔案。
- 計算 V1 與 V2 的平均總分。
- 彙整 Subagent 提出的具體「證據 (Evidence)」。
- 使用 `write_to_file` 將最終的總結報告寫入測試目錄下，命名為 `Evaluation_Report.md`。報告應包含：
  - 整體勝出者
  - 平均分數對比
  - 重大結構破壞記錄 (來自 Python 腳本)
  - 具體翻譯優劣對比 (來自 Subagent Evidence)
- 在對話框中通知使用者評估完成，並給出報告路徑。

# 使用限制
- 為了避免超出 Token 限制，本技能主要設計用於**微型測試案例** (單一章節或極短的書籍)。請勿直接傳入一本包含上百章節的完整 ePub。
