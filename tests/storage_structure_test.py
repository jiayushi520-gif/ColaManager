"""Structural checks only; these do not certify Apple runtime behavior."""
import json
import plistlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class StorageChecks(unittest.TestCase):
    def test_probe_has_no_cloud_or_third_party_actions(self):
        wf = plistlib.loads((ROOT/'work/ColaManager-Local-Probe-v2.shortcut').read_bytes())
        raw = json.dumps(wf)
        for forbidden in ['WFFileStorageService', 'WFFileDestination', '/Users/', 'runworkflow']:
            self.assertNotIn(forbidden, raw)
        allowed = {'comment','gettext','setvariable','text.split','choosefromlist',
                   'conditional','setitemname','documentpicker.save','showresult',
                   'output','file.select','detect.dictionary','getvalueforkey','alert'}
        for a in wf['WFWorkflowActions']:
            self.assertIn(a['WFWorkflowActionIdentifier'].removeprefix('is.workflow.actions.'), allowed)

    def test_probe_never_overwrites(self):
        wf = plistlib.loads((ROOT/'work/ColaManager-Local-Probe-v2.shortcut').read_bytes())
        saves = [a['WFWorkflowActionParameters'] for a in wf['WFWorkflowActions']
                 if a['WFWorkflowActionIdentifier'].endswith('documentpicker.save')]
        self.assertEqual(len(saves), 1)
        self.assertTrue(saves[0]['WFAskWhereToSave'])
        self.assertFalse(saves[0]['WFSaveFileOverwrite'])

    def test_pending_check_precedes_initialization(self):
        wf = plistlib.loads((ROOT/'work/ColaManager.shortcut').read_bytes())
        actions = wf['WFWorkflowActions']
        read_index = next(i for i,a in enumerate(actions) if
                          a['WFWorkflowActionParameters'].get('WFGetFilePath')=='ColaManager/state.pending.json')
        init_index = next(i for i,a in enumerate(actions) if
                          a['WFWorkflowActionParameters'].get('WFAlertActionTitle')=='初始化可乐管理')
        self.assertLess(read_index, init_index)

    def test_commit_reloads_after_write(self):
        wf = plistlib.loads((ROOT/'work/ColaManager.shortcut').read_bytes())
        actions = wf['WFWorkflowActions']
        saves = [i for i,a in enumerate(actions) if
                 a['WFWorkflowActionParameters'].get('WFFileDestinationPath')=='ColaManager/state.json']
        self.assertTrue(saves)
        for i in saves:
            self.assertEqual(actions[i+1]['WFWorkflowActionParameters'].get('WFGetFilePath'),
                             'ColaManager/state.json')

if __name__ == '__main__':
    unittest.main()
