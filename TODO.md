# TODO / Future Enhancements

- [ ] **重構高品質模式（Maker-Checker QA）調度架構以相容 OpenCode 與 Antigravity**
  - **背景與問題**：
    - **Antigravity (AGY)** 支援巢狀階層式代理人委派（Hierarchical Delegation），允許 `epub-translator` 子代理人在執行階段直接呼叫 `epub-qa-reviewer` 子代理人進行多輪自我糾錯迴圈（Self-correction Loop）。
    - **OpenCode** 採用嚴格的扁平/星狀調度架構（Flat Orchestrator Pattern），Child Session 內不具備 `subagent` 工具，禁止子代理人遞迴生成下一層子代理人。
    - 現行 `SKILL.md` 指示由 Translator 代理人自行呼叫 QA 代理人，導致在 OpenCode 環境中高品質模式（`--high-quality`）無法實際啟動獨立的 `epub-qa-reviewer`，退化為 Translator 內部自我檢查。
  - **待辦工作 (Action Items)**：
    1. **修改 `SKILL.md` 的調度職責**：將 QA Reviewer 的調度權責移交給 Root Agent（主協調者）。
    2. **實作星狀 Maker-Checker 流程**：
       - 主代理人派發 `epub-translator` 產出翻譯章節。
       - 章節產出後，主代理人直接主動調用 `epub-qa-reviewer` 進行深度語意審查與格式驗證。
       - 若審查結果為 `NEEDS_REVISION`，主代理人將反饋帶回 `epub-translator` 進行修訂，直到通過 `APPROVED`。
    3. **雙環境相容性測試**：確保修改後的調度流程在 Antigravity 與 OpenCode 兩套 Agent Harness 下皆能穩定執行並完成閉環驗證。
