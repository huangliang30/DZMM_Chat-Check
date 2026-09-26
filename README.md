# Chat-Check
一个用于酒馆DZMM导出的聊天json文件查看器。

## 功能
- 纯 tkinter 轻量界面，浅色 / 深色双主题（自动记忆）
- 圆润设计：窗口圆角、药丸按钮 / 标签 / 搜索框
- 消息列表侧栏（单击定位、双击编辑），角色色标（user / char / 系统），日期分隔
- 搜索高亮（Ctrl+F，Enter / Shift+Enter 跳转匹配），角色筛选
- 编辑模式：Ctrl+Return 应用修改，Ctrl+S 保存回原 JSON（不会写入内部字段）
- “” 内话语高亮（工具栏「“”高亮」开关或 Ctrl+H，写入设置记忆）
- 正文一键导出为 TXT
- 字号调节 Ctrl+ / Ctrl-

## 运行
- 源码：`python chat_viewer.py [chat_export_xxx.json]`（Python 3.10+；可选依赖 tkinterdnd2 支持拖入文件）
- 打包版：`dist/AI_Chat_Viewer.exe`（重建：`python -m PyInstaller AI_Chat_Viewer.spec --noconfirm`）
- 最新打包版下载：[Releases 页](https://github.com/huangliang30/Chat-Check/releases)（`AI_Chat_Viewer.exe` 单文件绿色版）

## 快捷键
| 快捷键 | 功能 |
| --- | --- |
| Ctrl+O | 打开文件 |
| Ctrl+S | 保存修改 |
| Ctrl+E | 编辑模式 |
| Ctrl+F | 搜索内容 |
| Ctrl+H | “” 高亮开关 |
| Ctrl+C | 复制选中 / 当前消息 |
| Ctrl+ / Ctrl- | 字号放大 / 缩小 |
| Ctrl+Return | 应用修改（编辑面板内） |
| Esc | 退出编辑 / 清空搜索 |

## 设置
保存在 `%APPDATA%\AI_Chat_Viewer\settings.json`（主题、字号、侧栏、窗口大小、quote_highlight）。

## 备注
- `chat_viewer.py.bak` 为界面重构前的旧版备份。
