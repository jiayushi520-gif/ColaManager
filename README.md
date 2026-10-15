# ColaManager / 可乐管理器

版本 **2.0.0**。已获用户授权公开发布，基础实机测试通过，专项验收范围见下文。记录可乐、漱口、刷牙，
执行每周额度及违规后禁喝规则。运行时无需 Python、第三方 App、API Key 或服务器。

## 安装及运行

交付包 dist/ColaManager-v2.0.0.shortcut 是主程序，安装后保持名称 **ColaManager**；
其他入口调用此名称。开发工作副本的新版位于 dist/v2/，上一级 dist 是旧版留档。
已有同名旧版时先导出数据及旧快捷指令副本，再安装新版，避免入口调用旧程序。

首次选择查看本周额度→首次使用→明确确认→保存至“我的 iPhone”下自建文件夹→
重新选择刚保存的文件校验。后续选择打开最新状态文件，选最新 state-r修订号-时间戳.json。
每次写入保留旧文件；修订号在恢复分支可能重复，需核对修改时间和实际内容。
文件夹由用户在系统界面创建，不宣称自动创建或无交互访问固定目录。

## 实际功能

- 每自然周一瓶；上一周未按时刷牙打卡则下一周禁喝；额度不累计。
- 饮用、漱口、刷牙；关联最近48小时最新记录；拒绝重复打卡，迟到不撤销处罚。
- 本周额度、连续合规、完成率、最近4/12/52周及全部历史。
- 截止时间/日期、睡前提醒设置；饮用后创建系统提醒。
- 睡前提醒、截止检查、每周报告入口。
- JSON 备份、恢复预览与二次确认、v1迁移保留旧字段和扩展字段。
- 新增今日状态与关于；每日统计按事件发生日计数。

## 存储、隐私和限制

请选择“我的 iPhone”。工作流无法自动证明文件提供方是本地；选择云位置不符合本地使用方式。
用户报告完整版在 iOS 26.1、关闭 iCloud Drive 后基础测试通过，包含记录重读、
漱口刷牙、重复操作、备份恢复、离线及重启读取；这是用户反馈，并非自动设备认证。
完整2.0.0实机验收尚未完成，最低兼容版本未认证；签名不等于运行验证。

新快照读回通过才报告成功。取消或写入失败不覆盖旧文件，但可能留下未确认的新文件。
没有事务锁、原子替换或自动最新文件发现；只允许一个运行修改，选旧快照会产生分支。
读取失败不自动初始化，原生解析或权限错误可能直接由系统中断。
文件选择器需交互，周报/截止检查不保证锁屏无人值守；独立睡前提醒仍可配系统自动化。
原可选 Scriptable 动态组件保留源码，但不进入无第三方 App 分发包；原生按钮组件不等价。

工作流没有联网动作，不自动上传数据。系统提醒事项可能按用户账户设置同步。
定期导出独立 JSON 备份；设备遗失、重置或文件删除后，无备份可能无法恢复。
Apple 安装分享与运行时 iCloud Drive 是不同用途。

## 截图、许可与发布

源码：[GitHub](https://github.com/jiayushi520-gif/ColaManager)。
安装文件：[GitHub Releases](https://github.com/jiayushi520-gif/ColaManager/releases)。
真实 iPhone 截图待补，不用模拟界面冒充。RoutineHub 和 Apple 分享链接尚未就绪；
可通过 Release 的 Apple 官方签名文件安装。所有者已选择 MIT 许可证，见 LICENSE。

## 开发

Python 3.10+、Node 18+；签名需支持 shortcuts sign 的 Mac。开发工具不在 iPhone 运行。

```sh
python3 src/build_release.py
python3 src/build_local_probe.py
python3 src/build_v2.py
python3 -m unittest discover -s tests -p '*_test.py'
TZ=Asia/Shanghai node --test tests/core.test.js tests/widget.test.js
TZ=America/New_York node --test tests/dst.test.js
python3 src/sign_v2.py
python3 src/package_v2.py
```

build_release.py 重建旧基线供回归；build_v2.py 才生成本地候选。
[架构](docs/architecture.md) · [迁移](docs/migration.md) · [故障处理](docs/troubleshooting.md)
· [iPhone 验收](docs/iphone_acceptance.md) · [发布说明](docs/release_notes.md)
