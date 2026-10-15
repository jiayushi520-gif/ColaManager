"""Native picker storage. Immutable snapshots; no fabricated folder bookmarks."""
from build_shortcuts import Flow, var, token
from native_manager import ISO, EMPTY, MODES, choose, assert_has, normalize, jsonobj

LOCAL_MODES = MODES + ['查看今日状态', '每周报告', '截止检查', '关于']
STAMP = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$'


class LocalFlow(Flow):
    def alert(self, title, *message):
        self.a('alert', WFAlertActionTitle=title,
               WFAlertActionMessage=token(*message), WFAlertActionCancelButtonShown=True)

    def match_required(self, value, pattern, error):
        self.set('matched', self.a('text.match', text=token(value), WFMatchTextPattern=pattern))
        assert_has(self, var('matched'), error)

    def pick(self, name, message):
        self.alert('选择本地文件', message)
        self.set(name, self.a('file.select', SelectMultiple=False))
        assert_has(self, var(name), '没有选择文件，未修改已有数据。')
        self.set(name+'_text', self.a('gettext', WFTextActionText=token(var(name))))
        assert_has(self, var(name+'_text'), '文件为空，未初始化或覆盖。请重新运行并选择恢复备份。')

    def start_local(self):
        g = self.iff(var('mode'), 101)
        choose(self, 'mode', LOCAL_MODES, '可乐管理器 2.0.0')
        self.end(g)
        g = self.iff(var('mode'), 4, '关于')
        self.stop('ColaManager 2.0.0 本地选择器版。数据保存在你选择的位置，请使用“我的 iPhone”。每次选择最新状态文件；无需第三方 App、运行时 Python、账号或 API Key。新保存保留旧文件，非数据库事务。系统提醒事项只用于提醒。文件被删或设备丢失后需要独立备份。此完整版本仍需 iPhone 验收。')
        self.end(g)
        self.num('fresh', 0)
        self.text('original', '')
        self.text('original_file', '')
        g = self.iff(var('mode'), 4, '恢复备份')
        self.pick('restore', '选择要恢复的本地 JSON 备份。只生成新的状态文件，不覆盖当前状态；损坏的当前文件无需读取。')
        self.set('raw_state', var('restore_text'))
        self.otherwise(g)
        choose(self, 'source_mode', ['打开最新状态文件', '首次使用 / 无法取回旧数据'], '已有记录请选择最新 state 文件，切勿再次初始化')
        h = self.iff(var('source_mode'), 4, '首次使用 / 无法取回旧数据')
        self.alert('确认建立空历史？', '请先检查本地 state、backup、pending 及旧导出文件。仅首次使用或明确无法取回旧数据时继续。新文件不覆盖旧文件，但无法自动发现你的其他文件。')
        self.num('fresh', 1)
        self.fmt('created', var('now'), ISO)
        self.text('raw_state', '{"schema_version":2,"app_version":"2.0.0","revision":0,"started_at":"', var('created'),
                  '","created_at":"', var('created'), '","updated_at":"', var('created'),
                  '","deadline_time":"02:00","deadline_next_day":1,"reminder_time":"23:00","records":{}}')
        self.otherwise(h)
        self.pick('original_file', '在“我的 iPhone”中选择最新 state-r…json，或旧版 state.json。选取旧快照会形成分支，无法自动检测更晚文件。解析失败请重新运行“恢复备份”，不要初始化。')
        self.set('original', var('original_file_text'))
        self.set('raw_state', var('original'))
        self.end(h)
        self.end(g)
        self.set('reserved', self.a('text.match', text=token(var('raw_state')), WFMatchTextPattern=EMPTY))
        g = self.iff(var('reserved'), 100)
        self.stop('文件含内部保留标记，拒绝处理，原文件保持不变。')
        self.end(g)
        self.set('state', self.a('detect.dictionary', WFInput=normalize(self, var('raw_state'))))

    def timestamp(self, value, label):
        self.match_required(value, STAMP, label+'缺失或不含时区，未保存。')
        self.date('validation_date', token(value))
        self.diff('validation_age', var('validation_date'), var('now'))
        g = self.iff(var('validation_age'), 0, 0)
        self.stop(label+'在未来，未保存。')
        self.end(g)

    def validate_local(self):
        self.get('version', var('state'), 'schema_version')
        self.num('supported', 0)
        for version in [1, 2]:
            g = self.iff(var('version'), 4, version)
            self.num('supported', 1)
            self.end(g)
        g = self.iff(var('supported'), 4, 0)
        self.stop('只支持数据版本1和2。未修改文件。')
        self.end(g)
        self.get('started', var('state'), 'started_at')
        self.timestamp(var('started'), '初始化时间')
        self.date('startdate', token(var('started')))
        self.diff('history_age', var('startdate'), var('now'))
        g = self.iff(var('history_age'), 2, 630720000)
        self.stop('历史超过20年，需人工核对，未保存。')
        self.end(g)
        for field in ['deadline_time', 'reminder_time']:
            self.get(field, var('state'), field)
            if field == 'reminder_time':
                g = self.iff(var(field), 101)
                self.text(field, '23:00')
                self.put('state', field, var(field))
                self.end(g)
            self.match_required(var(field), r'^(?:[01][0-9]|2[0-3]):[0-5][0-9]$', '设置时间格式无效，未保存。')
        self.get('nextday', var('state'), 'deadline_next_day')
        self.match_required(var('nextday'), r'^[01]$', '截止日期设置无效，未保存。')
        self.get('records', var('state'), 'records')
        self.set('record_text', self.a('gettext', WFTextActionText=token(var('records'))))
        self.match_required(var('record_text'), r'^\s*\{[\s\S]*\}\s*$', 'records 必须是字典，不能是列表、缺失或空文本。')
        self.set('keys', self.a('getvalueforkey', WFInput=var('records'), WFGetDictionaryValueType='All Keys'))
        loop = self.repeat(var('keys'))
        self.set('record_key', var('Repeat Item'))
        self.get('checking', var('records'), token(var('record_key')))
        self.get('check_id', var('checking'), 'record_id')
        g = self.iff(var('check_id'), 5, token(var('record_key')))
        self.stop('记录ID与字典键不一致，未保存。')
        self.end(g)
        for field in ['consumed_at', 'rinsed_at', 'brushed_at']:
            self.get('check_time', var('checking'), field)
            if field != 'consumed_at':
                # Empty strings use EMPTY internally; missing fields are rejected below.
                missing = self.iff(var('check_time'), 101)
                self.stop('记录缺少'+field+'，未保存。')
                self.end(missing)
                optional = self.iff(var('check_time'), 5, EMPTY)
            self.timestamp(var('check_time'), field)
            if field == 'consumed_at':
                self.set('consumption_date', var('validation_date'))
                self.diff('since_start', var('startdate'), var('consumption_date'))
                g = self.iff(var('since_start'), 0, 0)
                self.stop('饮用早于初始化时间，未保存。')
                self.end(g)
            else:
                self.diff('after_consumption', var('consumption_date'), var('validation_date'))
                g = self.iff(var('after_consumption'), 0, 0)
                self.stop('打卡早于饮用，未保存。')
                self.end(g)
                self.end(optional)
        self.get('check_due', var('checking'), 'brushing_deadline')
        self.match_required(var('check_due'), STAMP, '截止时间缺失或无时区，未保存。')
        self.end(loop, 'repeat.each')
        g = self.iff(var('version'), 4, 2)
        for field in ['created_at', 'updated_at']:
            self.get('metadata_time', var('state'), field)
            self.timestamp(var('metadata_time'), field)
        self.end(g)
        # Upgrade by adding metadata; keep all old fields and unknown extensions.
        g = self.iff(var('version'), 4, 1)
        self.num('migrated_schema', 2)
        self.put('state', 'schema_version', var('migrated_schema'))
        self.put('state', 'created_at', var('started'))
        self.num('migrated_revision', 0)
        self.put('state', 'revision', var('migrated_revision'))
        self.end(g)
        self.put('state', 'app_version', '2.0.0')
        self.get('revision', var('state'), 'revision')
        self.match_required(var('revision'), r'^\d{1,9}$', '修订号无效，未保存。')

    def serialize_local(self):
        self.put('state', 'records', var('records'))
        self.set('serialized', self.a('gettext', WFTextActionText=token(var('state'))))
        self.set('serialized', self.a('text.replace', WFInput=var('serialized'),
                 WFReplaceTextFind='"'+EMPTY+'"', WFReplaceTextReplace='""', WFReplaceTextRegularExpression=False))

    def save(self, value, path, ask=True):
        basename = path.rsplit('/', 1)[-1] if isinstance(path, str) else 'ColaManager-report.txt'
        # Separate filenames allow rollback even if the final save is cancelled.
        self.set('save_now', self.a('date', WFDateActionMode='Current Date'))
        self.fmt('file_stamp', var('save_now'), 'yyyyMMdd-HHmmss-SSS')
        stem, _, ext = basename.rpartition('.')
        filename = token(stem or basename, '-', var('file_stamp'), '.', ext or 'json')
        if basename == 'state-r.json':
            filename = token('state-r', var('revision'), '-', var('file_stamp'), '.json')
        self.set('expected_save', self.a('gettext', WFTextActionText=token(value)))
        self.alert('保存新文件', '请保存到“我的 iPhone”。保留旧文件，不覆盖。保存后需要重新选择刚保存的文件核对。')
        named = self.a('setitemname', WFInput=var('expected_save'), WFName=filename)
        self.set('saved_file', self.a('documentpicker.save', WFInput=named,
                      WFAskWhereToSave=True, WFSaveFileOverwrite=False))
        assert_has(self, var('saved_file'), '保存没有返回文件，无法确认保存；旧文件未覆盖。')
        self.set('saved_content', self.a('gettext', WFTextActionText=token(var('saved_file'))))
        g = self.iff(var('saved_content'), 5, token(var('expected_save')))
        self.stop('保存输出内容不一致。保留旧文件；本次不能确认成功。')
        self.end(g)
        self.pick('readback', '选择刚保存的新文件（时间戳最新）。找不到则取消；请保留旧文件。')
        g = self.iff(var('readback_text'), 5, token(var('expected_save')))
        self.stop('重新读取内容不一致，可能选错文件。旧文件未覆盖；请核对最新文件后再操作。')
        self.end(g)
        return var('readback')

    def commit_local(self):
        self.set('now', self.a('date', WFDateActionMode='Current Date'))
        self.fmt('saved_at', var('now'), ISO)
        self.put('state', 'updated_at', var('saved_at'))
        self.get('revision', var('state'), 'revision')
        self.math('revision', var('revision'), '+', 1)
        self.put('state', 'revision', var('revision'))
        self.serialize_local()
        self.save(var('serialized'), 'state-r.json')
        self.set('original_file', var('readback'))
        self.set('original', var('readback_text'))
        self.num('fresh', 0)

    def after_evaluate(self):
        g = self.iff(var('mode'), 4, '恢复备份')
        self.alert('恢复预览', '初始化时间：', var('started'), '\n记录数：', var('total'),
                   '\n当前禁喝：', var('banned'), '\n将生成新的状态文件，原文件保留。')
        self.alert('确认恢复为新状态？', '只有保存并重新读取校验通过才算恢复成功。下一次请选择新状态文件。')
        self.end(g)
        # A first installation must be persisted even if the chosen business action exits.
        g = self.iff(var('fresh'), 4, 1)
        self.commit_local()
        self.end(g)
        g = self.iff(var('version'), 4, 1)
        h = self.iff(var('mode'), 5, '恢复备份')
        self.alert('旧版迁移', '已保留全部旧字段；写入新的版本2状态文件，原文件不变。')
        self.commit_local()
        self.end(h)
        self.end(g)
        g = self.iff(var('mode'), 4, '查看今日状态')
        self.fmt('today', var('now'), 'yyyy-MM-dd')
        for name in ['daily_drinks','daily_rinses','daily_brushes']:
            self.num(name, 0)
        self.set('daily_records', self.a('getvalueforkey', WFInput=var('records'), WFGetDictionaryValueType='All Values'))
        loop = self.repeat(var('daily_records'))
        self.set('daily_record', var('Repeat Item'))
        for field, name in [('consumed_at','daily_drinks'),('rinsed_at','daily_rinses'),('brushed_at','daily_brushes')]:
            self.get('daily_time', var('daily_record'), field)
            h = self.iff(var('daily_time'), 5, EMPTY)
            self.date('daily_date', token(var('daily_time')))
            self.fmt('daily_day', var('daily_date'), 'yyyy-MM-dd')
            j = self.iff(var('daily_day'), 4, token(var('today')))
            self.math(name, var(name), '+', 1)
            self.end(j)
            self.end(h)
        self.end(loop, 'repeat.each')
        self.stop('今日 ', var('today'), '\n饮用 ', var('daily_drinks'), '\n漱口打卡 ', var('daily_rinses'),
                  '\n刷牙打卡（含迟到） ', var('daily_brushes'), '\n本周剩余 ', var('remaining'), ' 瓶')
        self.end(g)
