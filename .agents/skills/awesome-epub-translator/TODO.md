# TODO / Future Enhancements

## 1. 導入 QA Subagent (Maker-Checker 架構)

**概念描述**：
目前的翻譯驗收（如檢查檔案截斷、確認 `</html>` 標籤等輕量防呆檢查）是由 Main Agent 兼任執行。未來可考慮引入獨立的 `QA Subagent` (品質保證代理) 來專職負責驗收工作。

**預期優勢**：
* **職責分離 (Separation of Concerns)**：讓 Main Agent 專心扮演 Orchestrator（狀態管理與任務分發），避免其 Context Window 被驗收過程中的大量 HTML 片段污染，維持大腦清醒。
* **深度語意審查 (Deep Semantic Review)**：QA Subagent 可讀取「原文」與「譯文」進行逐段比對，針對「翻譯品質」、「語氣是否符合 Style Profile」、「是否漏翻」或「生硬的雙關語」進行深度審查，而不僅僅是結構防呆。
* **自我修正迴圈 (Self-Correction Loop)**：建立 `Translator` -> `QA Reviewer` 的內部工作流。若 QA 發現問題，可直接提供具體修改建議並要求 Translator 重新修正，直到驗收通過後再回報給 Main Agent。

**實作考量點**：
* 建議將此功能設計為可選的進階模式（例如 `--high-quality` 參數）。因為每份檔案都額外喚醒 QA Subagent 會增加整體的 Token 成本與等待時間，讓使用者能依據需求在「速度/成本」與「極致品質」間做選擇。
