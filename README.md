# DZMM Chat-Check
一个用于酒馆DZMM导出的聊天json文件查看器。

## 功能
- 纯 tkinter 轻量界面，浅色 / 深色双主题（自动记忆）
- 2.5D 扁平图标按钮：全部按钮去文字化为简笔画矢量图标（PIL 超采样抗锯齿，无 PIL 自动降级），悬停显示功能提示（Tooltip）；纯平面反馈，无投影 / 描边 / 弹性动画
- 圆润设计：窗口圆角；按钮 / 搜索框静置时透明融入工具栏背景，悬停 / 按下 / 选中才浮现药丸底色（PIL 超采样抗锯齿，边缘平滑）
- 消息列表侧栏（单击定位、双击编辑），角色色标（user / char / 系统），日期分隔
- 搜索高亮（Ctrl+F，Enter / Shift+Enter 跳转匹配），角色筛选（全部 / user / char）
- 编辑模式：Ctrl+Return 应用修改，Ctrl+S 保存回原 JSON（不会写入内部字段）
- 引号话语高亮（支持 “”、「」、『』与直引号；仅改字体颜色；工具栏「高亮」开关或 Ctrl+H；旁边色块可改高亮颜色，右键色块恢复默认）
- 正文一键导出为 TXT（纯文字，不含角色与时间戳）
- 查找替换：Ctrl+R 替换条复用搜索词，支持替换当前匹配 / 全部替换（替换内容可为空 = 删除），结果走待保存机制，Ctrl+S 写回
- 视觉对齐 DZMM 网页：粉色主色、深色近黑底、琥珀色引号高亮、侧栏角色圆点；char / user 正文直接铺在页面背景上（无色块），阅读节奏与网页一致
- 对话分支：SillyTavern 分支导出在有分支的消息头部显示「分支 i/n」提示，点 ‹ › 逐个切换查看各分支（定位闪烁标记，有未保存修改时需先保存再切换）
- 文件夹选片：工具栏「文件夹」/ Ctrl+Shift+O / 空状态「选择文件夹」进入窗口内文件夹视图（非弹窗），按文件名中文标题列出聊天 JSON，支持标题过滤与重新扫描，双击或回车进入；打开后信息栏「‹ 返回文件夹」回列表重选（保留过滤并定位当前文件），Esc 返回
- 字号调节 Ctrl+ / Ctrl-
- 操作栏可收起：工具栏「收起」/ 信息栏「展开」/ Ctrl+T，偏好自动记忆

## 运行
- 源码：`python chat_viewer.py [chat_export_xxx.json]`（Python 3.10+；可选依赖 tkinterdnd2 支持拖入文件）
- 打包版：`dist/AI_Chat_Check.exe`（重建：`python -m PyInstaller AI_Chat_Viewer.spec --noconfirm`）
- 软件名 AI Chat Check；窗口 / 任务栏 / exe 图标为 `good.ico`（源图 `good.png`）
- 最新打包版下载：[Releases 页](https://github.com/huangliang30/DZMM_Chat-Check/releases)（`AI_Chat_Check.exe` 单文件绿色版）

## 快捷键
| 快捷键 | 功能 |
| --- | --- |
| Ctrl+O | 打开文件 |
| Ctrl+S | 保存修改 |
| Ctrl+E | 编辑模式 |
| Ctrl+F | 搜索内容 |
| Ctrl+H | 引号高亮开关 |
| Ctrl+C | 复制选中 / 当前消息 |
| Ctrl+ / Ctrl- | 字号放大 / 缩小 |
| Ctrl+Return | 应用修改（编辑面板内） |
| Ctrl+T | 操作栏收起 / 展开 |
| Ctrl+R | 替换条显示 / 隐藏 |
| Ctrl+Shift+O | 文件夹选片（窗口内文件夹列表，双击 / 回车打开，Esc 返回） |
| Esc | 退出编辑 / 清空搜索 |

## 设置
保存在 `%APPDATA%\AI_Chat_Viewer\settings.json`（主题、字号、侧栏、窗口大小、quote_highlight、quote_color、show_toolbar）。

## 发布
- 发新版只需打标签推送：`git tag v1.3 && git push origin v1.3` → GitHub Actions 自动在 Windows 环境打包，并在 Releases 页创建发行版、附上 `AI_Chat_Check.exe`
- Actions 页的「Build & Release」支持手动运行（仅验证构建，产物在构建件里）
- 本地打包：`python -m PyInstaller AI_Chat_Viewer.spec --noconfirm` 或运行 `build.bat`

## 备注
- 界面图标 / 按钮设计规范与图标对照表见 `UI_ICONS.md`
