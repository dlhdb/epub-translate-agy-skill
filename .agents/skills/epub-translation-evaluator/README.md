# ePub Translation Evaluator (Antigravity Skill)

這是一個專為 Antigravity 環境打造的電子書翻譯品質驗證技能（Workspace Skill）。本技能透過多代理（Multi-Agent）架構與 Python 腳本，能夠自動比對舊版 (V1) 與新版 (V2) 翻譯的差異，並根據客觀標準產出評估報告。

---

## 🚀 使用方式 (Usage)

在使用本技能之前，您必須先準備好包含原文與翻譯結果的測試案例資料夾。

### 1. 準備測試案例資料夾

建議採用「抽樣」方式，僅保留 2~3 個具有代表性的 HTML/XHTML 章節（例如：包含對話、程式碼區塊、複雜表格的章節），以節省 Token 成本與等待時間。

資料夾結構必須符合以下格式：

```text
eval_workspace/
├── source/        (放置待測試章節的原文 html/xhtml 檔案)
├── v1/            (放置舊版 Skill 翻譯出來的章節，以及舊版的 style_profile.md)
└── v2/            (放置新版 Skill 翻譯出來的章節，以及新版的 style_profile.md)
```
*注意：`source/`、`v1/`、`v2/` 裡面的檔案名稱與相對路徑必須完全一致。*

### 2. 執行評估

在對話框中直接要求 Agent 進行評估：

- "請幫我評估 `eval_workspace/` 中的翻譯差異。"
- "Please evaluate the translation differences in the `eval_workspace/` directory."
- "請幫我評估 `eval_workspace/`，比較標準模式 (v1) 與 High-Quality 模式 (v2) 的翻譯品質差異。"

---

## ✨ 核心特色

1. **混合式驗證 (Hybrid Validation)**：
   - **結構快篩**：利用內建的 Python 腳本 (`html_validator.py`) 快速掃描 V1 與 V2 的檔案，抓出遺失閉合標籤等嚴重的 HTML 結構損毀，不浪費 LLM 算力。
   - **語意深度評估**：透過 Antigravity 的 `invoke_subagent` 呼叫多個子代理，進行原文與譯文的交叉比對。

2. **客觀評估標準 (Evaluation Rubric)**：
   子代理會嚴格遵循 `references/evaluation-rubric.md` 中定義的 1-5 分標準進行評分，避免 LLM 出現盲目給高分或幻覺。

3. **證據要求 (Chain of Thought)**：
   子代理在給出分數時，被強制要求必須引述原文與譯文的具體句子來佐證其評分，確保評估的準確度與參考價值。

4. **平行處理 (Parallel Subagents)**：
   自動將不同的章節分配給多個子代理同時進行評估，大幅提升整體處理速度。

---

## ⚠️ 注意事項

1. **Token 消耗警告**：
   此技能需要同時讀取原文、V1 譯文與 V2 譯文。**請絕對不要直接丟入整本完整的 ePub 書籍進行評估**，否則極易導致 Context Window 爆滿並產生高昂的 API 費用。請務必先手動刪減檔案，進行局部抽樣測試。
2. **檔案格式支援**：
   本系統支援 `.html` 與 `.xhtml` 檔案。如果在純瀏覽器中開啟這些檔案呈現全白畫面，屬於正常現象（通常是因為相對路徑的 CSS 或 SVG 渲染問題）。只要透過文字編輯器確認內部包含 HTML 標籤與文字，即可正常交由本技能評估。
