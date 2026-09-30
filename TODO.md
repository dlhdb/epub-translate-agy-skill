# TODO / Future Enhancements

## 方案 A：Translator 內部雙階段自我批判與校正（Two-Pass Self-Reflection）

### 核心目標
將高品質審查與自我糾錯機制整合於 `epub-translator` Subagent 內部，在記憶體中執行「Pass 1 初譯 $\rightarrow$ Pass 2 嚴格編輯自我批判 $\rightarrow$ Pass 3 一次性落盤」。
簡化 Root Orchestrator 職責，消除外部多目錄搬移負擔，使多章節背景並行（`background: true`）安全可靠且零狀態競爭。

---

### 分期任務清單

#### Phase 1: 更新 Translator Subagent 角色規範
- [x] **`.opencode/agents/epub-translator.md`**：
  - 新增 `Two-Pass Self-Reflection Protocol` 核心指令。
  - 明確 4 大記憶體自檢要項：XML 屬性合法性（防 `class="center class="translated"` 錯誤）、標題階層保留（禁止 `h1`/`h2` 降級為 `p`）、目錄完整性（父層項必翻）、台灣術語與人稱全篇一致性。
  - 維持單次原子性 `write` 落盤規範至 `<work_dir>/_translated/<relative_path>`。

#### Phase 2: 更新 Skill 規範檔案
- [x] **`.agents/skills/awesome-epub-translator/SKILL.md`**：
  - 簡化 Step 6.1 與 6.1.5：將高品質模式定義為在 Translator 調度中強制注入 Two-Pass 自檢指令。
  - 維持單一乾淨的工作目錄結構（`<work_dir>/_translated/` 與 `<work_dir>/_staging/`）。
  - 確保支援安全背景並行（`background: true`）。
- [x] **`AGENTS.md` 與 `README.md`**：
  - 更新核心特色與設計決策，清楚標記 Two-Pass In-Memory Self-Reflection & Editorial QA 機制。

#### Phase 3: 驗證與測試（Evals）
- [ ] 撰寫單元與整合測試，檢驗 Two-Pass 檢核標準（XML 屬性合法性、標籤階層、目錄父項完整性）。
- [ ] 執行端到端翻譯驗證。
