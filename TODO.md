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
- [x] 撰寫單元測試 (`tests/test_two_pass_rules.py`)，驗證 Two-Pass 4 大核心檢核標準（XML 屬性合法性、標題階層、目錄父項完整性、人稱一致性）。
- [x] 撰寫整合測試 (`tests/test_translated_output_qa.py`)，自動驗證現有產出全部通過 XML 解析與 Two-Pass 規範檢核。
- [x] 執行全套測試，7 項單元/整合測試全數通過（`Ran 7 tests in 0.005s, OK`）。

---

## 純粹單一子代理架構（Pure Single-Subagent Architecture）精簡

### 核心目標
徹底移除冗餘的 `epub-qa-reviewer.md`，使整個系統達到純粹極簡的 **1 個 Skill + 1 個 Subagent (`epub-translator`)**。
全面清除專案文件中的 `--qa-model` 歷史包袱，確立以 `epub-translator` 內部 Two-Pass 自審為唯一核心的高品質翻譯架構。

### 分期任務清單

#### Phase 4: 物理移除冗餘 Subagent 與淨化 Skill 規範
- [x] 刪除 `.opencode/agents/epub-qa-reviewer.md`。
- [x] 修改 `.agents/skills/awesome-epub-translator/SKILL.md`：
  - 參數表移除 `QA model` (`--qa-model`)。
  - Step 6.1 移除所有調度 QA reviewer 與 `--qa-model` 分支。
  - Step 6.1.5 完全確立為純粹的 Translator 內部雙階段自省完稿，無外部 QA 呼叫。

#### Phase 5: 全面更新專案文件與架構圖
- [x] 更新 `AGENTS.md`：架構樹移除 `epub-qa-reviewer.md`，更新設計決策為純粹 Single-Subagent。
- [x] 更新根目錄 `README.md` 與技能 `README.md`：移除 `--qa-model` 範例與多代理人描述。
- [x] 更新 `TECHNICAL_DETAILS.md`：Mermaid 架構圖改繪單代理內部 Pass 1 $\rightarrow$ Pass 2 流程。

#### Phase 6: 全套回歸測試驗證
- [x] 執行現有所有單元與整合測試，確保 100% 通過（`Ran 7 tests in 0.006s, OK`）。

---

## 機械化格式檢查與 LLM 統一針對性修復（Deterministic Linter + Targeted LLM Repair）

### 核心目標
確立「機械化負責格式檢查（0 Token、毫秒級）、語意統一由 LLM 判斷、修復統一由 LLM 執行（最多 2 次熔斷）」架構原則，避免整章報廢重翻造成的 Token 浪費，並防止腳本黑盒硬修改帶來的副作用。

### 分期任務清單
- [x] 實作機械格式檢查工具 `.agents/skills/awesome-epub-translator/scripts/format_linter.py`（XML 閉合、重複屬性、標題階層、檔案截斷比率）。
- [x] 撰寫獨立單元測試 `tests/test_format_linter.py`，驗證 5 大格式檢查與 JSON 輸出功能（全部通過）。
- [x] 更新 `SKILL.md` Step 6.2：整合 `format_linter.py` 驗收與 LLM 針對性修復流程（最多 2 次修訂後熔斷）。
- [x] 更新 `.opencode/agents/epub-translator.md` Directive 8：指導 Subagent 接收 linter 診斷資訊進行精準修復，保留有效譯文。
- [x] 更新 `AGENTS.md`、`TECHNICAL_DETAILS.md`、`README.md`：同步新架構時序圖與核心特色描述。
- [x] 全套測試回歸驗證（14 項測試全部通過）。

