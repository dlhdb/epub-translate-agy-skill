# 系統架構與技術細節 (Technical Details)

`epub-translation-evaluator` 採用了**混合式驗證 (Hybrid Validation)** 與 **多代理評審 (Multi-Agent Evaluation)** 架構。本文件詳細記錄了其背後的設計決策與實作細節。

## 1. 混合式驗證架構 (Hybrid Validation)

在評估由 LLM 產生的 HTML/XHTML 文件時，我們面臨兩個截然不同的檢查維度：
1. **語意品質**：翻譯是否通順、是否符合風格畫像 (Style Profile)。這需要強大的 LLM 進行語意理解。
2. **結構合法性**：標籤是否閉合、XML 是否合法。若交給 LLM 檢查，不僅容易產生幻覺（LLM 經常忽略遺失的 `</div>`），且極度浪費算力。

因此，本系統設計了兩階段過濾機制：
* **Phase 1 (Script Check)**：Main Agent 首先呼叫 `scripts/html_validator.py`。該腳本基於 Python 內建的 `html.parser` 實作了一個嚴格的 Stack 結構，掃描所有 `.xhtml` 與 `.html` 檔案。只要發現 `Mismatched tag` 或 `Unclosed tag`，腳本會立即回報錯誤。
* **Phase 2 (LLM Check)**：Main Agent 讀取腳本的 JSON 回報。對於結構已經嚴重損毀的檔案，直接判定為 1 分（災難級），**跳過**喚醒 Subagent 的流程。這能有效節省 API Token，將昂貴的 LLM 算力保留給結構正常的檔案進行深度語意審查。

## 2. 職責分離與 Context 管理

在 Multi-Agent 系統中，如果讓多個評審 Subagent 直接在主要對話框中印出評分報告，會導致 Main Agent 的 Context Window 遭到嚴重污染，進而引發幻覺（例如 Main Agent 搞混 V1 與 V2 的分數）。

為解決此問題，本系統實作了**硬碟暫存通訊機制**：
1. **Orchestrator (Main Agent)**：負責派發任務與最終數據統計。它只傳遞檔案「路徑」給 Subagent，而非檔案「內容」。
2. **Judge (Subagent)**：負責讀取原文、V1 與 V2，並在自己的獨立 Context 中進行深度交叉比對。
3. **JSON 落地機制**：Subagent 評估完成後，**禁止**直接回報文字。它們被強制要求將結果格式化為嚴格的 JSON，並使用 `write_to_file` 寫入 `_evaluation_work/` 目錄中。
4. **Data Aggregation**：Main Agent 最終只需讀取這些精簡的 JSON 檔案，即可輕鬆計算平均分並抓取證據，產出完美的 Markdown 報告。

## 3. 避免幻覺：Rubric 與 Chain of Thought

LLM 在擔任「裁判」時，常有「偏好長答案 (Verbosity Bias)」或「盲目給高分」的傾向。
本技能透過 `references/evaluation-rubric.md` 實作了雙重防護：

* **量化標準 (Rubric)**：將 1-5 分的定義具象化。例如明確定義「3 分 = 尚可，有明顯機翻感」。
* **強制舉證 (Chain of Thought, CoT)**：要求 Subagent 不能只給出數字，必須擷取原文、V1 與 V2 的具體字句來進行對比（例如：「*V1 未察覺這是片語，直譯導致語意錯誤*」）。這迫使模型在得出最終分數前，必須先進行邏輯推演，大幅提升了評分的客觀性與一致性。

## 4. 效能與成本考量 (Sampling Strategy)

由於 Subagent 每次都需要載入三份相同的章節文本（原文+V1+V2），Token 消耗量約為單純翻譯時的 3 倍以上。
因此，系統在設計上與 README 文件中皆強烈建議使用者採用**「局部抽樣 (Sampling)」**策略。與其讓 Agent 逐字掃描一本 50 個章節的電子書，不如精選 3 個具有代表性的章節（如對話密集區塊、程式碼區塊、表格區塊）進行驗證，以在「評估精準度」與「API 成本」之間取得最佳平衡。
