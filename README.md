# Dataset Annotator

一個極簡 Flask「資料夾瀏覽＋文字標註」工具。  
適合巡覽大型圖像資料集，快速輸入/修改 `*.caption_txt`、`*.mask_txt`  
以及專屬的 `*.system_label_meta_txt` 類標籤檔。

> **特色**
> - 🔍 **自動掃描**：依檔名規則將「媒體檔」與「標註檔」分組，並支援遞迴搜尋子目錄
> - ⚡ **零延遲切換**：預先快取後續 5 張影像  
> - ⌨️ **鍵盤友善**：`← / →` 自動儲存並跳至上一／下一張  
> - ✏️ **一鍵標籤**：游標預設於快速標籤框，直接輸入即可生成或覆寫  
> - 📨 **純前端 Vanilla JS**，環境依賴最低

---

## 目錄結構

```

dataset-annotator/
├── app.py              # Flask 伺服器（主程式）
├── templates/
│   └── index.html      # Jinja2 樣板
├── static/
│   ├── main.js         # 前端互動邏輯
│   └── style.css       # 基本排版
├── README.md           # 使用說明（本檔）
└── .gitignore          # Git 忽略規則

````

> **檔名規則總覽**
>
> | 種類 | 範例 | 規則說明 |
> |------|------|----------|
> | **媒體檔** | `image1.jpg`, `video1.mp4`, `text1.txt` | 檔名 `A.B` 中 **B 不含底線 `_`**，且副檔名屬於<br>　`IMAGE / VIDEO / AUDIO / TEXT` 四大集合之一 |
> | **註解檔** | `image1.caption_txt`, `image1._txt`,<br>`image1.custom_mask_txt` | 檔名 `A.B` 中 **B 至少含一個 `_`**；<br>最右側副檔名需屬於文字格式（`.txt/.json/.yaml/.csv`） |
> | **快速標籤** | `image1.system_label_meta_txt` | 固定後綴 `.system_label_meta_txt`<br>顯示於右側專用輸入框 |

---

## 快速開始

```bash
# 1. 取得原始碼
git clone https://github.com/your-name/dataset-annotator.git
cd dataset-annotator

# 2. 建立隔離環境（可略）
python3 -m venv .venv
source .venv/bin/activate

# 3. 安裝依賴
pip install flask

# 4. 啟動（假設資料集位於 /data/images）
python app.py /data/images              # 一般檔案模式
python app.py /data/images --dir        # 以資料夾為單位標註
# 啟用除錯標籤
python app.py /data/images --debug
# 查看所有選項
python app.py -h
# 伺服器監聽 http://0.0.0.0:{port}
````

開啟瀏覽器輸入 `http://localhost:{port}/`

> 若在遠端伺服器啟動，請開放對應埠或以 SSH port forwarding 存取。

---

## 操作說明

| 操作   | 鍵盤／滑鼠           | 效果                                |
| ---- | --------------- | --------------------------------- |
| 下一張  | → (Right Arrow) | 自動儲存當前標註 → 載入下一張                  |
| 上一張  | ← (Left Arrow)  | 自動儲存 → 載入上一張                      |
| 快速標籤 | 直接輸入英數字後按 →     | 建立 / 覆寫 `*.system_label_meta_txt`<br>使用 `--dir` 時會寫入 `system_label_dir_meta_txt` |
| 換資料夾 | ↑ / ↓ (Arrow Up/Down) | `--dir` 模式下，切換上一／下一資料夾 |
| 編輯註解 | 右側 textarea     | 編輯完成後按 → 或 ← 立即儲存                 |
| 除錯標籤 | --debug           | 頁面右上會出現紅色 DEBUG 標示               |

---

## 客製化

* **快取張數**：`app.py` → `CACHE_SIZE`
* **支援格式**：於 `IMAGE_EXTS / VIDEO_EXTS / …` 中增刪副檔名
* **埠號**：啟動時改寫 `app.run(... port=49145)`

---



