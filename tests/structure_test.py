import pathlib,plistlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
class StructureTests(unittest.TestCase):
 def test_all_workflows_have_resolvable_action_references(self):
  for path in (ROOT/'work').glob('*.shortcut'):
   if path.name.startswith('Test.'):continue
   try:w=plistlib.loads(path.read_bytes())
   except Exception:continue
   seen=set();stack=[]
   def check(x):
    if isinstance(x,dict):
     if x.get('Type')=='ActionOutput':self.assertIn(x['OutputUUID'],seen,path.name)
     for v in x.values():check(v)
    elif isinstance(x,list):
     for v in x:check(v)
   for a in w['WFWorkflowActions']:
    p=a['WFWorkflowActionParameters'];check(p);mode=p.get('WFControlFlowMode');group=p.get('GroupingIdentifier')
    if mode==0:stack.append(group)
    if mode in (1,2):self.assertEqual(stack[-1],group,path.name)
    if mode==2:stack.pop()
    seen.add(p.get('UUID'))
   self.assertFalse(stack,path.name)
 def test_public_native_workflows_have_no_mac_or_third_party_runtime(self):
  for name in ['ColaManager','我要喝可乐','我已经漱口','我已经刷牙','查看可乐统计']:
   w=plistlib.loads((ROOT/'work'/(name+'.shortcut')).read_bytes())
   self.assertIn('NCWidget',w['WFWorkflowTypes'])
   for a in w['WFWorkflowActions']:
    s=a['WFWorkflowActionIdentifier'];self.assertNotIn('script',s);self.assertNotIn('ssh',s);self.assertTrue(s.startswith('is.workflow.actions.'))
 def test_entrypoints_share_one_manager(self):
  for name in ['我要喝可乐','我已经漱口','我已经刷牙','查看可乐统计']:
   w=plistlib.loads((ROOT/'work'/(name+'.shortcut')).read_bytes());a=w['WFWorkflowActions'][-1]
   self.assertEqual(a['WFWorkflowActionIdentifier'],'is.workflow.actions.runworkflow');self.assertEqual(a['WFWorkflowActionParameters']['WFWorkflowName'],'ColaManager')
if __name__=='__main__':unittest.main()
