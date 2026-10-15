import copy
import json
import plistlib
from pathlib import Path
import sys
import re
import unittest
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from state_v2 import StateError, load, migrate, initialize, summary, check_in, restore_preview

NOW = datetime.fromisoformat('2026-01-12T03:00:00+08:00')

def fixture():
    return dict(schema_version=1, started_at='2026-01-05T00:00:00+08:00',
                deadline_time='02:00', deadline_next_day=1, records={
                    'a': dict(record_id='a', consumed_at='2026-01-11T22:00:00+08:00',
                              brushing_deadline='2026-01-12T02:00:00+08:00', rinsed_at='',
                              brushed_at='', week_start='2026-01-05', status='pending', violation_reason='')})


class ReferenceTests(unittest.TestCase):
    def test_migration_numbers_use_native_number_outputs(self):
        from local_storage import LocalFlow
        flow = LocalFlow()
        flow.validate_local()
        for action in flow.actions:
            if action['WFWorkflowActionIdentifier'] == 'is.workflow.actions.setvalueforkey':
                params = action['WFWorkflowActionParameters']
                if params['WFDictionaryKey'] in ('schema_version', 'revision'):
                    self.assertEqual(params['WFDictionaryValue']['WFSerializationType'], 'WFTextTokenString')

    def test_native_empty_value_normalization_preserves_escaped_quotes(self):
        source = {'text':'quoted "" and : ""', 'nested': {'blank':''}, 'items':['','quote"']}
        raw = json.dumps(source)
        normalized = re.sub(r'(:\s*)""(?=\s*[,}])', r'\g<1>"__COLA_EMPTY__"', raw)
        restored = json.dumps(json.loads(normalized)).replace('"__COLA_EMPTY__"', '""')
        self.assertEqual(json.loads(restored), source)

    def test_first_install_requires_confirmation(self):
        with self.assertRaises(StateError): initialize(NOW)
        self.assertEqual(initialize(NOW, True)['records'], {})

    def test_repeat_load_is_idempotent_and_keeps_records(self):
        first = load(json.dumps(fixture()), NOW)
        self.assertEqual(load(json.dumps(first), NOW), first)
        self.assertEqual(len(first['records']), 1)

    def test_migration_preserves_unknown_fields_and_original(self):
        old = fixture()
        old['custom'] = {'text': 'say ""', 'empty': ''}
        old['records']['a']['custom'] = [1, 2]
        before = copy.deepcopy(old)
        new = migrate(old, NOW)
        self.assertEqual(old, before)
        self.assertEqual(new['custom'], old['custom'])
        self.assertEqual(new['records'], old['records'])
        self.assertEqual(new['schema_version'], 2)

    def test_bad_input_never_initializes(self):
        for raw in ['', ' ', '{bad', '{}', '[]', '{"schema_version":99}', '__COLA_EMPTY__']:
            with self.subTest(raw=raw), self.assertRaises(StateError): load(raw, NOW)

    def test_record_id_mismatch(self):
        s = fixture(); s['records']['a']['record_id'] = 'b'
        with self.assertRaises(StateError): migrate(s, NOW)

    def test_future_check_in(self):
        for field in ['brushed_at', 'rinsed_at']:
            s = fixture(); s['records']['a'][field] = '2026-01-13T00:00:00+08:00'
            with self.assertRaises(StateError): migrate(s, NOW)

    def test_invalid_settings(self):
        for field, value in [('deadline_time','25:00'), ('deadline_next_day',9), ('records',[])]:
            s = fixture(); s[field] = value
            with self.assertRaises(StateError): migrate(s, NOW)

    def test_missing_check_in_and_bad_deadline(self):
        s = fixture(); del s['records']['a']['rinsed_at']
        with self.assertRaises(StateError): migrate(s, NOW)
        s = fixture(); s['records']['a']['brushing_deadline'] = '2026-01-15T00:00:00+08:00'
        with self.assertRaises(StateError): migrate(s, NOW)

    def test_rinse_and_duplicate(self):
        s = check_in(fixture(), 'a', 'rinsed_at', NOW)
        self.assertEqual(check_in(s, 'a', 'rinsed_at', NOW), s)
        self.assertEqual(summary(s, NOW)['today']['rinses'], 1)

    def test_brushing_at_deadline(self):
        at = datetime.fromisoformat('2026-01-12T02:00:00+08:00')
        s = check_in(fixture(), 'a', 'brushed_at', at)
        self.assertFalse(summary(s, NOW)['banned'])

    def test_late_brushing_keeps_penalty(self):
        s = check_in(fixture(), 'a', 'brushed_at', NOW)
        self.assertTrue(summary(s, NOW)['banned'])
        self.assertEqual(summary(s, NOW)['today']['brushes'], 1)

    def test_next_week_restores_allowance(self):
        later = datetime.fromisoformat('2026-01-19T00:00:00+08:00')
        self.assertEqual(summary(fixture(), later)['remaining'], 1)

    def test_pending_previous(self):
        now = datetime.fromisoformat('2026-01-12T01:00:00+08:00')
        self.assertTrue(summary(fixture(), now)['pending_previous'])

    def test_duplicate_week_rejected(self):
        s = fixture(); s['records']['b'] = dict(s['records']['a'], record_id='b')
        with self.assertRaises(StateError): summary(s, NOW)

    def test_empty_statistics(self):
        self.assertEqual(summary(initialize(NOW, True), NOW)['today'], dict(drinks=0,rinses=0,brushes=0))

    def test_restore_preview_does_not_modify_source(self):
        s = fixture(); raw = json.dumps(s)
        restored, preview = restore_preview(raw, NOW)
        self.assertEqual(json.dumps(s), raw)
        self.assertEqual(preview['total'], 1)
        self.assertEqual(restored['schema_version'], 2)

    def test_timezone_change_policy_is_explicit(self):
        s = fixture()
        a = summary(s, NOW, 'Asia/Shanghai')
        b = summary(s, NOW, 'America/Los_Angeles')
        self.assertTrue(a['banned'])
        self.assertFalse(b['banned'])


class NativeBuildTests(unittest.TestCase):
    def setUp(self):
        names = ['ColaManager','我要喝可乐','我已经漱口','我已经刷牙','查看可乐统计',
                 '可乐每周报告','可乐截止检查','可乐睡前提醒','ColaManager-Test','ColaManager-v2-Rules-Test']
        self.paths = [ROOT/'work/v2'/(name+'.shortcut') for name in names]
        self.assertTrue(all(p.is_file() for p in self.paths), 'build_v2.py must run first')

    def test_no_cloud_path_or_external_runtime(self):
        for path in self.paths:
            wf = plistlib.loads(path.read_bytes())
            for action in wf['WFWorkflowActions']:
                ident = action['WFWorkflowActionIdentifier']
                self.assertTrue(ident.startswith('is.workflow.actions.'))
                for word in ['script','ssh','downloadurl','getcontents','openurl']:
                    self.assertNotIn(word, ident, path.name)
                p = action['WFWorkflowActionParameters']
                for key in ['WFFileStorageService','WFFileDestination','WFFileDestinationPath','WFGetFilePath']:
                    self.assertNotIn(key, p, path.name)
                self.assertNotIn('/Users/', json.dumps(p))

    def test_no_overwrite_or_delete_and_all_saves_are_interactive(self):
        for path in self.paths:
            wf = plistlib.loads(path.read_bytes())
            for a in wf['WFWorkflowActions']:
                self.assertNotIn('delete', a['WFWorkflowActionIdentifier'])
                if a['WFWorkflowActionIdentifier'].endswith('documentpicker.save'):
                    self.assertTrue(a['WFWorkflowActionParameters']['WFAskWhereToSave'])
                    self.assertFalse(a['WFWorkflowActionParameters']['WFSaveFileOverwrite'])

    def test_all_action_references_and_control_flow(self):
        for path in self.paths:
            wf = plistlib.loads(path.read_bytes()); seen = set(); stack = []
            def visit(value):
                if isinstance(value, dict):
                    if value.get('Type') == 'ActionOutput':
                        self.assertIn(value['OutputUUID'], seen, path.name)
                    for v in value.values(): visit(v)
                elif isinstance(value, list):
                    for v in value: visit(v)
            for action in wf['WFWorkflowActions']:
                p = action['WFWorkflowActionParameters']; visit(p)
                mode, group = p.get('WFControlFlowMode'), p.get('GroupingIdentifier')
                if mode == 0: stack.append(group)
                if mode in (1, 2): self.assertEqual(stack[-1], group)
                if mode == 2: stack.pop()
                self.assertNotIn(p['UUID'], seen)
                seen.add(p['UUID'])
            self.assertFalse(stack)

    def test_wrappers_resolve_and_new_features_exist(self):
        names = {plistlib.loads(p.read_bytes())['WFWorkflowName'] for p in self.paths}
        for path in self.paths:
            for a in plistlib.loads(path.read_bytes())['WFWorkflowActions']:
                if a['WFWorkflowActionIdentifier'].endswith('runworkflow'):
                    self.assertIn(a['WFWorkflowActionParameters']['WFWorkflowName'], names)
        text = (ROOT/'work/v2/ColaManager.json').read_text()
        for feature in ['查看今日状态','恢复预览','确认恢复为新状态','旧版迁移','最近52周','重新读取内容不一致']:
            self.assertIn(feature, text)

if __name__ == '__main__': unittest.main()
