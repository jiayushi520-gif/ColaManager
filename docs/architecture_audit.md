# ColaManager v2.0.0 源码审计

审计日期：2026-10-15。状态：重构前基线审计，本目录不是已发布 v2。
原始 ZIP 保持不变；本目录是独立解压副本。历史 evidence 属于旧交付，不是本轮测试。

## 真实结构

原包含 dist、src、tests、evidence，共 39 个文件；没有根 README、LICENSE 或 docs。
src/native_manager.py 生成主程序；build_shortcuts.py 提供原生动作和 plist 序列化；
build_release.py 生成入口及开发验收；sign.py 调用 Apple shortcuts sign；
package_release.py 打包签名文件。cola_core.js 是只读规则引擎，widget.js 是可选
Scriptable 组件。state.schema.json 和 config.example.json 描述 v1 数据。

## 功能及调用关系

| 入口 | 源码中的真实行为 |
|---|---|
| ColaManager | 主菜单、读取状态、计算额度、饮用、打卡、设置、备份恢复、历史 |
| 我要喝可乐 | 传入同名命令，调用 ColaManager |
| 我已经漱口 / 我已经刷牙 | 传入同名命令，关联最近 48 小时的最新记录 |
| 查看可乐统计 | 传入“查看统计报告” |
| 可乐每周报告 | 传入“每周报告”，主程序保存文本报告并通知 |
| 可乐截止检查 | 传入“截止检查”，主程序计算并通知 |
| 可乐睡前提醒 | 独立通知，不读写状态 |
| ColaManager-Test | 只显示成功文字；不是完整测试套件 |
| ColaManager-Widget.js | Scriptable 只读数值组件，需第三方 App 和 iCloud 书签 |

业务规则：周一开始的自然周最多一瓶；未按时刷牙打卡会禁喝下一自然周；
处罚不累计；上周待结算时禁止提前消费新周额度；超时补打卡不能撤销处罚；
重复饮用、重复打卡受到限制；历史有 4/12/52 周及全部；统计含连续合规、
最长连续合规、完成率及违规周。饮用同时创建系统提醒事项，提醒事项不是数据库。
今日独立视图、CSV、关于页不是现有功能，应明确为新增。

## 数据与读写

schema_version=1，records 为按 ID 索引的字典，不是数组。
顶层包含 started_at、updated_at、deadline_time、deadline_next_day、reminder_time。
记录包含 record_id、consumed_at、rinsed_at、brushed_at、brushing_deadline、
week_start、status、violation_reason。时间格式含时区偏移；周归属按运行设备时区重算。

Flow.load 强制 WFFileStorageService='iCloud Drive'，Flow.save 强制
WFFileDestination='iCloud Drive'。相对目录为 Shortcuts/ColaManager。
主文件 state.json、上次备份 state.backup.json、候选 state.pending.json。
读取先设置 WFFileErrorIfNotFound=False，再判断是否有输出；该标志不能证明
目标 iOS 在权限不足、同步失败、文件夹缺失时一定不会中断。

首次启动：选命令→读主文件→若空则创建目录→检查 backup→提示初始化。
未检查 pending 和初始化标记，不能可靠区分首次安装与数据遗失。
恢复入口选择文件、解析、确认、验证版本和记录后提交。
写入：重读主文件比较→备份旧文本→写 pending→解析并仅检查版本→保存正式文件。
没有正式文件读回验证；没有原子替换或事务锁，比较与写入间仍有竞争窗口。

## 已确认缺陷与限制

1. 强制 iCloud Drive，与新要求冲突。
2. 主文件缺失但 pending 存在时可能提示初始化，遗漏恢复线索。
3. 解析错误会终止工作流，没有完整 JSON 损坏恢复界面；不能当作首次安装。
4. pending 校验只查版本，正式写入不校验结果全文。
5. 原生逻辑未完整验证 record_id 与字典键一致、未来漱口/刷牙、started_at 边界；
   JS 验证比原生更严格，不能用 JS 通过替代原生保证。
6. normalize 全局替换空字符串，可能改变含引号的用户扩展字段。
7. 设备时区改变可能重新归属历史周，迁移需明确策略。
8. 原生循环无与 JS 相同的历史上限，异常早期日期可能造成长循环。
9. Scriptable 动态组件不能在“无第三方 App”条件下原样保留；原生按钮组件不等价。
10. 恢复确认缺少完整记录数/范围预览；读取错误类别未充分区分。
11. 原包有签名二进制；其签名内容应与重建源码分别核验，源码审计不等于
    每个已签名包的完整反序列化审计。

本轮副本已修复第 2 项 pending 遗漏及第 4 项正式文件读回缺失，并通过结构检查。
这些是原存储流程的加固，不等于本地存储重构完成；iPhone 运行仍待验收。

## 版本、依赖与发布

旧数据版本固定为 1，没有独立 app_version。Python、Node 仅用于开发测试；
原生主程序动作无 Python/JS 运行依赖；可选组件依赖 Scriptable。
本机 git、gh、shortcuts sign 可用。联网 gh auth status 成功；目标仓库只读查询
未找到可访问的 ColaManager 仓库。未创建仓库、未推送、未发布。
旧 evidence 不能作为 v2 本地存储或 iPhone 验证证据。
没有选择许可证，不新增 LICENSE。

## 本地方案及门槛

候选一：用户在编辑器绑定“我的 iPhone”文件夹，之后免交互读写。
需设备导出的真实动作参数及关闭 iCloud Drive 后重启验证，不能硬编码猜测书签。
候选二：每次运行系统文件选择器，保存时选择本地位置。交互较多，但可以先
用独立 Local-Probe 检验基础持久化。探针不保证无交互覆盖、目录创建或原子替换。
探针成功后才应选择适配器并接入原业务。不能用 Mac 路径或 Python 文件读写替代 iPhone 能力。

公开发布门槛：本地适配器完成、旧功能逐项对照、静态及回归测试通过、iPhone
验证、敏感信息检查、许可证选择、用户确认公开发布。当前不满足正式发布条件。

参考：Apple 分享文档 https://support.apple.com/guide/shortcuts/share-shortcuts-apdf01f8c054/ios
及 RoutineHub 当前 API 文档 https://routinehub.co/docs/api/ 。Apple 分享链接不等于
运行时 iCloud Drive；RoutineHub 分发需要实际分享链接及发布者认证，用户运行不需 API Key。
