# TODO / Future Enhancements

- [x] **重構高品質模式（Maker-Checker QA）調度架構以相容 OpenCode 與 Antigravity**
  - **背景與問題**：
    - **Antigravity (AGY)** 支援巢狀階層式代理人委派（Hierarchical Delegation），允許 `epub-translator` 子代理人在執行階段直接呼叫 `epub-qa-reviewer` 子代理人進行多輪自我糾錯迴圈（Self-correction Loop）。
    - **OpenCode** 採用嚴格的扁平/星狀調度架構（Flat Orchestrator Pattern），Child Session 內不具備 `subagent` 工具，禁止子代理人遞迴生成下一層子代理人。
    - 現行 `SKILL.md` 指示由 Translator 代理人自行呼叫 QA 代理人，導致在 OpenCode 環境中高品質模式（`--high-quality`）無法實際啟動獨立的 `epub-qa-reviewer`，退化為 Translator 內部自我檢查。
  - **實施成果與架構調整 (Completed)**：
    1. **修改 `SKILL.md` 調度職責（星狀架構）**：將 QA Reviewer 的調度權責全數移交給 Root Agent（主協調者）。
    2. **實作星狀 Maker-Checker 與自我糾錯閉環**：
       - **Phase 1 (Maker)**：主代理人派發 `epub-translator` 並行翻譯章節草稿。
       - **Phase 2 (Checker)**：章節產出後，主代理人並行調用 `epub-qa-reviewer` 進行深度語意與標籤驗證，並儲存 Markdown 審查報告至 `_translated/qa_reports/`。
       - **Phase 3 (Self-Correction Loop)**：若審查判定 `NEEDS_REVISION`，主代理人以自包含 Payload 重新派發 `epub-translator` 修訂並複查；設置上限 2 次修訂的 Circuit Breaker 與 `APPROVED_WITH_WARNING` 降級機制避免死循環。
    3. **狀態追蹤與斷點續傳防護**：引進 `.qa_status.json` 管理章節審查狀態，確保任務暫停重啟時不會誤判未審查草稿為完成。
    4. **更新設定與技術文件**：
       - 補齊 `.opencode/agents/epub-translator.md` 的修訂反饋指引。
       - 更新 `TECHNICAL_DETAILS.md` 架構圖與 Sequence 循序圖為星狀拓樸。
       - 更新 `README.md` 中的高品質審查特色介紹。
