# ColaManager v2.0.0

已实现：原生输出移除强制 iCloud Drive 路径；显式初始化、本地选择器、非覆盖快照、
独立读回、恢复预览和二次确认、v1迁移、今日状态和关于；保留原核心规则及入口。

限制：需用户选择最新文件及保存位置；无自动最新状态发现、事务锁或锁屏周报保证。
原Scriptable数值组件留存源码，不放入纯原生分发包；原生按钮不等价动态面板。
用户报告完整本地版在 iOS 26.1、关闭 iCloud Drive 后基础测试通过：初始化、
记录重读、漱口刷牙、重复操作、备份恢复、离线和重启。专项及异常场景仍待验收。

主程序安装后保留名称 ColaManager，保存到我的 iPhone。
许可证已由所有者确认使用 MIT。Mac 隔离规则测试 11/11、Python 测试 30/30 通过。
用户已确认公开发布；本次按上述有限验证范围分发，不代表专项及异常场景全部通过。
真实 iPhone 截图待补。
[RoutineHub](https://routinehub.co/shortcut/26832/) ·
[Apple 安装链接](https://www.icloud.com/shortcuts/58dce0926d154d95a3c3698637ad4a06)。
分享副本名为 ColaManager-v2.0.0；使用中文子入口前，应备份/改名旧版并将新主程序改名为 ColaManager。

## 安装

下载 `ColaManager-v2.0.0.shortcut` 到 iPhone 并打开添加。已有旧版时先备份旧快捷指令和数据。
主入口名称保持 ColaManager；完整 ZIP 的 dist/ 包含其他可选中文入口。
首次使用保存至“我的 iPhone”并重新选择文件校验，以后总是选择最新 state-r 快照。
只报告 iOS 26.1 用户实测结果，不推断其他版本兼容性。MIT 许可证。
