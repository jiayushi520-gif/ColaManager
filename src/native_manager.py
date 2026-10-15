from build_shortcuts import *
ISO="yyyy-MM-dd'T'HH:mm:ssXXXXX"
INPUT={'Value':{'Type':'ExtensionInput'},'WFSerializationType':'WFTextTokenAttachment'}
MODES=['我要喝可乐','我已经漱口','我已经刷牙','查看本周额度','查看统计报告','查看历史记录','设置截止时间','导出备份','恢复备份']

EMPTY='__COLA_EMPTY__'
def normalize(f,source):
    f.set('normalized',f.a('text.replace',WFInput=source,WFReplaceTextFind=r'(:\s*)""(?=\s*[,}])',WFReplaceTextReplace='$1"'+EMPTY+'"',WFReplaceTextRegularExpression=True))
    return var('normalized')
def jsonobj(f,n,txt): f.text(n+'raw',txt.replace('""','"'+EMPTY+'"')); f.set(n,f.a('detect.dictionary',WFInput=var(n+'raw')))
def choose(f,n,items,prompt):
    f.text(n+'items','\n'.join(items)); f.set(n+'list',f.a('text.split',text=token(var(n+'items')),WFTextSeparator='New Lines'))
    f.set(n,f.a('choosefromlist',WFInput=var(n+'list'),WFChooseFromListActionPrompt=prompt,WFChooseFromListActionSelectMultiple=False))
def assert_has(f,v,message):
    g=f.iff(v,101);f.stop(message);f.end(g)
    g=f.iff(v,4,EMPTY);f.stop(message);f.end(g)
def make_id(f):
    # Native random-list action, no third-party Generate UUID dependency.
    f.text('hexchars','\n'.join('0123456789abcdef'))
    f.set('hexlist',f.a('text.split',text=token(var('hexchars')),WFTextSeparator='New Lines'))
    f.text('idraw','')
    loop=uid();f.a('repeat.count',WFRepeatCount=32,GroupingIdentifier=loop,WFControlFlowMode=0)
    f.set('digit',f.a('getitemfromlist',WFInput=var('hexlist'),WFItemSpecifier='Random Item'))
    f.text('idraw',var('idraw'),var('digit'));f.end(loop,'repeat.count')
    f.set('id',f.a('text.replace',WFInput=var('idraw'),WFReplaceTextFind='^(.{8})(.{4}).(.{3}).(.{3})(.{12})$',WFReplaceTextReplace='$1-$2-4$3-8$4-$5',WFReplaceTextRegularExpression=True))
    f.get('collision',var('records'),token(var('id')))
    g=f.iff(var('collision'),100);f.stop('记录ID冲突，请重新运行；未写入数据。');f.end(g)

def evaluate(f):
    f.week('cw',var('now'));f.adjust('nwdate',var('cwdate'),7);f.fmt('nw',var('nwdate'),'yyyy-MM-dd')
    for n in ['count','banned','violations','rinse_total','brush_total','total','pending_previous','this_violation','this_rinse','this_brush']: f.num(n,0)
    f.text('current_lines','本周尚无饮用记录；漱口和刷牙打卡：不适用'); f.text('candidate',EMPTY); f.text('candidate_time','');f.date('candidate_date','1970-01-01T00:00:00Z')
    jsonobj(f,'weeks','{}'); f.set('values',f.a('getvalueforkey',WFInput=var('records'),WFGetDictionaryValueType='All Values'))
    loop=f.repeat(var('values')); f.set('r',var('Repeat Item'))
    for k in ['record_id','consumed_at','brushing_deadline','rinsed_at','brushed_at']: f.get(k,var('r'),k)
    for k in ['record_id','consumed_at','brushing_deadline']: assert_has(f,var(k),'记录缺少必要字段；已停止，未写入数据。请从备份恢复。')
    f.date('consumed_date',token(var('consumed_at')));f.week('rw',var('consumed_date'))
    f.date('deadline_date',token(var('brushing_deadline')));f.diff('duration',var('consumed_date'),var('deadline_date'));h=f.iff(var('duration'),0,0);f.stop('记录截止时间早于饮用，数据无效。');f.end(h);h=f.iff(var('duration'),2,172800);f.stop('记录截止时间超出48小时，数据无效。');f.end(h);f.diff('record_age',var('consumed_date'),var('now'));h=f.iff(var('record_age'),0,0);f.stop('记录饮用时间在未来，数据无效。');f.end(h); f.diff('due',var('deadline_date'),var('now'))
    f.text('status','pending'); f.num('bad',0); f.num('rinsed',0);f.num('brushed',0)
    g=f.iff(var('rinsed_at'),5,EMPTY);f.num('rinsed',1);f.math('rinse_total',var('rinse_total'),'+',1);f.end(g)
    g=f.iff(var('brushed_at'),5,EMPTY)
    f.date('brush_date',token(var('brushed_at')));f.diff('brush_age',var('consumed_date'),var('brush_date'));h=f.iff(var('brush_age'),0,0);f.stop('刷牙打卡早于饮用，数据无效。');f.end(h);f.diff('late',var('deadline_date'),var('brush_date'))
    late=f.iff(var('late'),2,0);f.num('bad',1);f.text('status','late');f.otherwise(late);f.num('brushed',1);f.text('status','compliant');f.math('brush_total',var('brush_total'),'+',1);f.end(late)
    f.otherwise(g);due=f.iff(var('due'),3,0);f.num('bad',1);f.text('status','missed');f.end(due);f.end(g)
    f.put('r','status',var('status'));f.put('r','week_start',var('rw'));f.put('r','violation_reason',EMPTY)
    g=f.iff(var('bad'),4,1);f.put('r','violation_reason','未在约定截止时间前完成刷牙打卡（不验证实际刷牙行为）');f.math('violations',var('violations'),'+',1);f.end(g)
    f.put('records',token(var('record_id')),var('r'));f.math('total',var('total'),'+',1)
    # One slot per week; duplicated historical weeks fail closed.
    f.get('existing',var('weeks'),token(var('rw')))
    g=f.iff(var('existing'),100);f.stop('数据冲突：同一自然周发现多条饮用记录。请核对备份；本次未写入。');f.end(g)
    f.put('weeks',token(var('rw')),var('r'))
    f.adjust('penalty_date',var('rwdate'),7);f.fmt('penalty',var('penalty_date'),'yyyy-MM-dd')
    g=f.iff(var('penalty'),4,token(var('cw')))
    bad=f.iff(var('bad'),4,1);f.num('banned',1);f.end(bad)
    p=f.iff(var('status'),4,'pending');f.num('pending_previous',1);f.end(p);f.end(g)
    g=f.iff(var('rw'),4,token(var('cw')))
    f.math('count',var('count'),'+',1);f.set('this_violation',var('bad'));f.set('this_rinse',var('rinsed'));f.set('this_brush',var('brushed'))
    f.text('current_lines','饮用：',var('consumed_at'),'\n漱口打卡：',var('rinsed_at'),'\n刷牙打卡：',var('brushed_at'),'\n截止：',var('brushing_deadline'),'\n记录状态：',var('status'))
    f.end(g)
    # Choose latest eligible record: within 48h, still associated by immutable ID.
    f.diff('age',var('consumed_date'),var('now'))
    g=f.iff(var('age'),1,172800)
    h=f.iff(var('age'),3,0)
    f.diff('newer',var('candidate_date'),var('consumed_date'));j=f.iff(var('newer'),2,0);f.set('candidate',var('record_id'));f.set('candidate_time',var('consumed_at'));f.set('candidate_date',var('consumed_date'));f.end(j);f.end(h);f.end(g)
    f.end(loop,'repeat.each')
    f.num('allowance',1);g=f.iff(var('banned'),4,1);f.num('allowance',0);f.end(g)
    f.math('remaining',var('allowance'),'-',var('count'));g=f.iff(var('remaining'),0,0);f.num('remaining',0);f.end(g)
    f.text('next_allowance','1（尚有未到期记录时为暂定）');g=f.iff(var('this_violation'),4,1);f.text('next_allowance','0');f.end(g)

def commit(f,root='ColaManager'):
    if hasattr(f,'commit_local'):
        f.commit_local()
        return
    f.load('latest',root+'/state.json');f.set('latest_text',f.a('gettext',WFTextActionText=token(var('latest'))))
    present=f.iff(var('original_file'),100)
    concurrent=f.iff(var('latest_text'),5,token(var('original')));f.stop('数据已被另一运行修改，已取消本次保存。请重新运行并确认 iCloud 已同步。');f.end(concurrent)
    f.otherwise(present);concurrent=f.iff(var('latest'),100);f.stop('另一次运行已初始化数据，请重新运行。');f.end(concurrent);f.end(present)
    f.put('state','records',var('records'));f.fmt('saved_at',var('now'),ISO);f.put('state','updated_at',var('saved_at'))
    f.set('serialized',f.a('gettext',WFTextActionText=token(var('state'))));f.set('serialized',f.a('text.replace',WFInput=var('serialized'),WFReplaceTextFind='"'+EMPTY+'"',WFReplaceTextReplace='""',WFReplaceTextRegularExpression=False))
    # Backup before replacement; pending write and parse/readback before promotion.
    g=f.iff(var('original_file'),100);f.save(var('original'),root+'/state.backup.json');f.end(g)
    f.save(var('serialized'),root+'/state.pending.json');f.load('pending',root+'/state.pending.json')
    f.set('verified',f.a('detect.dictionary',WFInput=var('pending')));f.get('verified_version',var('verified'),'schema_version')
    g=f.iff(var('verified_version'),5,1);f.stop('待写文件校验失败，主文件未覆盖。');f.end(g)
    f.save(var('pending'),root+'/state.json')
    f.load('saved_file',root+'/state.json')
    f.set('saved_text',f.a('gettext',WFTextActionText=token(var('saved_file'))))
    g=f.iff(var('saved_text'),5,token(var('serialized')));f.stop('正式文件读回不一致。请保留 state.backup.json 和 state.pending.json 并恢复；不能确认本次保存成功。');f.end(g)

def stats(f):
    f.get('started',var('state'),'started_at');f.date('startdate',token(var('started')));f.week('first',var('startdate'))
    f.fmt('firstmjd',var('firstdate'),'g');f.fmt('currentmjd',var('cwdate'),'g');f.math('days',var('currentmjd'),'-',var('firstmjd'));f.math('wcount',var('days'),'÷',7);f.math('wcount',var('wcount'),'+',1)
    for n in ['streak','longest','compliant_weeks','banned_weeks']: f.num(n,0)
    f.text('history','');f.text('history4','');f.text('history12','');f.text('history52',''); f.text('trend','');f.text('previous_bad','0');f.set('iterdate',var('firstdate'))
    loop=uid();f.a('repeat.count',WFRepeatCount=token(var('wcount')),GroupingIdentifier=loop,WFControlFlowMode=0)
    f.fmt('iterweek',var('iterdate'),'yyyy-MM-dd');f.adjust('iterenddate',var('iterdate'),7);f.fmt('iterend',var('iterenddate'),'yyyy-MM-dd');f.get('wr',var('weeks'),token(var('iterweek')))
    f.text('wstatus','compliant');f.text('wrinse','不适用');f.text('wbrush','不适用');f.num('wdrinks',0);f.text('wreason','无');f.text('wbad','0')
    g=f.iff(var('wr'),100);f.num('wdrinks',1);f.get('wstatus',var('wr'),'status');f.get('wrinse',var('wr'),'rinsed_at');f.get('wbrush',var('wr'),'brushed_at');f.get('wreason',var('wr'),'violation_reason')
    h=f.iff(var('wreason'),5,EMPTY);f.text('wbad','1');f.end(h);f.end(g)
    g=f.iff(var('previous_bad'),4,'1');f.math('banned_weeks',var('banned_weeks'),'+',1);f.end(g)
    # Only closed, settled weeks contribute to streaks. Current week is provisional.
    g=f.iff(var('iterweek'),5,token(var('cw')))
    b=f.iff(var('wbad'),4,'1');f.num('streak',0);f.otherwise(b)
    p=f.iff(var('wstatus'),5,'pending');f.math('streak',var('streak'),'+',1);f.math('compliant_weeks',var('compliant_weeks'),'+',1)
    f.math('streakdiff',var('streak'),'-',var('longest'));h=f.iff(var('streakdiff'),2,0);f.set('longest',var('streak'));f.end(h);f.end(p);f.end(b);f.end(g)
    f.text('weekline','\n',var('iterweek'),' → ',var('iterend'),'（不含）\n饮用 ',var('wdrinks'),'；漱口 ',var('wrinse'),'；刷牙 ',var('wbrush'),'\n状态 ',var('wstatus'),'；原因 ',var('wreason'),'；禁喝 ',var('previous_bad'),'\n')
    f.text('history',var('history'),var('weekline'));f.math('weeksleft',var('wcount'),'-',var('Repeat Index'))
    for span in [4,12,52]:
        h=f.iff(var('weeksleft'),0,span);f.text('history'+str(span),var('history'+str(span)),var('weekline'));f.end(h)
    f.set('previous_bad',var('wbad'));f.set('iterdate',var('iterenddate'));f.end(loop,'repeat.count')
    f.text('rinse_rate','不适用');f.text('brush_rate','不适用')
    g=f.iff(var('total'),2,0)
    for n in ['rinse','brush']:
        f.math(n+'_ratio',var(n+'_total'),'÷',var('total'));f.math(n+'_percent',var(n+'_ratio'),'×',100);f.text(n+'_rate',var(n+'_percent'),'%')
    f.end(g)
    for display in ['history','history4','history12','history52','current_lines']:
        f.set(display,f.a('text.replace',WFInput=var(display),WFReplaceTextFind=EMPTY,WFReplaceTextReplace='未打卡',WFReplaceTextRegularExpression=False))
    f.text('report','🥤 可乐管理\n本周：',var('cw'),' → ',var('nw'),'（不含结束）\n允许 ',var('allowance'),' 瓶；已饮用 ',var('count'),' 瓶；剩余 ',var('remaining'),' 瓶\n禁喝：',var('banned'),'；本周违规：',var('this_violation'),'\n上周未到期记录待结算：',var('pending_previous'),'\n',var('current_lines'),'\n下周预计额度：',var('next_allowance'),'\n\n累计饮用 ',var('total'),' 瓶\n累计合规 ',var('compliant_weeks'),' 周；当前连续 ',var('streak'),' 周；最长 ',var('longest'),' 周（仅已结束且结算周）\n漱口完成率 ',var('rinse_rate'),'；按时刷牙打卡率 ',var('brush_rate'),'\n累计违规 ',var('violations'),' 次；累计禁喝 ',var('banned_weeks'),' 周\n0=否，1=是；打卡不验证实际刷牙行为。')

def main(name='ColaManager',root='ColaManager',test=False,development=False,flow=None):
    f=flow or Flow()
    f.a('comment',WFCommentActionText='本地选择器版：仅在一个运行中修改数据；每次选择最新状态。没有事务锁。' if flow else '所有入口共用此主程序。iCloud 不是事务数据库，请只在一台设备写入，等待同步后再换设备。')
    if development:
        original_action=f.a
        def development_action(kind, **params):
            if kind=='alert': return original_action('comment', WFCommentActionText='开发验收：跳过确认界面')
            return original_action(kind, **params)
        f.a=development_action
    f.set('mode',INPUT); f.set('now',f.a('date',WFDateActionMode='Current Date'))
    if test:
        f.set('fixture',f.a('detect.dictionary',WFInput=normalize(f,INPUT)));f.get('state',var('fixture'),'state');f.get('testnow',var('fixture'),'now');f.date('now',token(var('testnow')))
    elif flow:
        f.start_local()
    else:
        g=f.iff(var('mode'),101);choose(f,'mode',MODES,'🥤 可乐管理');f.end(g)
        f.load('original_file',root+'/state.json');f.set('original',f.a('gettext',WFTextActionText=token(var('original_file'))))
        restorebranch=f.iff(var('mode'),4,'恢复备份')
        f.a('file.createfolder',WFFilePath=root)
        f.set('restorefile',f.a('file.select',SelectMultiple=False));f.set('state',f.a('detect.dictionary',WFInput=normalize(f,var('restorefile'))))
        f.a('alert',WFAlertActionTitle='恢复所选备份？',WFAlertActionMessage='恢复会替换当前状态。请确认备份包含最新饮用和打卡；旧状态会保存为 state.backup.json。',WFAlertActionCancelButtonShown=True)
        f.otherwise(restorebranch)
        g=f.iff(var('original_file'),101)
        f.a('file.createfolder',WFFilePath=root)
        f.load('backup_exists',root+'/state.backup.json');h=f.iff(var('backup_exists'),100);f.stop('主文件缺失但存在备份。请在文件 App 恢复 state.backup.json 为 state.json，避免错误重置额度。');f.end(h)
        f.load('pending_exists',root+'/state.pending.json');h=f.iff(var('pending_exists'),100);f.stop('主文件缺失但存在待提交数据。请先保留并核对 state.pending.json，未初始化或覆盖任何历史。');f.end(h)
        f.a('alert',WFAlertActionTitle='初始化可乐管理',WFAlertActionMessage='未找到数据。仅首次使用时继续；若其他设备已有数据，请取消并等待 iCloud 同步。',WFAlertActionCancelButtonShown=True)
        jsonobj(f,'state','{"schema_version":1,"records":{},"deadline_time":"02:00","deadline_next_day":1,"reminder_time":"23:00"}')
        f.fmt('started',var('now'),ISO);f.put('state','started_at',var('started'));f.otherwise(g)
        f.set('state',f.a('detect.dictionary',WFInput=normalize(f,var('original'))));f.end(g);f.end(restorebranch)
    if flow:
        f.validate_local()
    else:
        f.get('version',var('state'),'schema_version');g=f.iff(var('version'),5,1);f.stop('数据结构版本不支持，未修改文件。');f.end(g)
    f.get('records',var('state'),'records');evaluate(f)
    if flow and not test:
        f.after_evaluate()
    if test:
        stats(f)
        fields=['count','banned','violations','rinse_total','brush_total','total','pending_previous','this_violation','allowance','remaining','streak','longest','compliant_weeks','banned_weeks']
        parts=['{']
        for i,k in enumerate(fields):parts.extend([(',' if i else '')+'"'+k+'":',var(k)])
        parts.extend([',"week_start":"',var('cw'),'"}'])
        f.a('output',WFOutput=token(*parts));f.output(name);return
    restore=f.iff(var('mode'),4,'恢复备份');commit(f,root);f.stop('备份已恢复，并已重新计算当前处罚。');f.end(restore)
    g=f.iff(var('mode'),4,'我要喝可乐')
    h=f.iff(var('banned'),4,1);f.stop('本周禁喝：上一自然周未按时完成刷牙打卡。处罚只持续本周。');f.end(h)
    h=f.iff(var('count'),2,0);f.stop('本周已经登记饮用一瓶，额度已用完，不允许重复登记。');f.end(h)
    h=f.iff(var('pending_previous'),4,1);f.stop('上周饮用记录仍在刷牙期限内，尚未判违规。请先完成对应刷牙打卡，再使用新周额度。');f.end(h)
    f.a('alert',WFAlertActionTitle='确认饮用本周唯一一瓶无糖可乐？',WFAlertActionMessage='确认即登记并扣除额度。饮后立即清水漱口，并在截止时间前完成刷牙打卡。',WFAlertActionCancelButtonShown=True)
    f.set('now',f.a('date',WFDateActionMode='Current Date'));f.fmt('stamp',var('now'),ISO);f.week('newweek',var('now'));h=f.iff(var('newweek'),5,token(var('cw')));f.stop('确认期间自然周已切换，请重新运行以检查最新额度。');f.end(h)
    f.get('cutoff',var('state'),'deadline_time');f.get('nextday',var('state'),'deadline_next_day');f.set('deadline_base',var('now'))
    h=f.iff(var('nextday'),4,1);f.adjust('deadline_base',var('now'),1);f.end(h)
    f.fmt('deadline_day',var('deadline_base'),'yyyy-MM-dd');f.date('deadline',token(var('deadline_day'),'T',var('cutoff'),':00'))
    f.diff('future',var('now'),var('deadline'));h=f.iff(var('future'),1,0);f.stop('今天的刷牙截止时间已过，不能新增饮用记录。');f.end(h)
    f.fmt('deadline_iso',var('deadline'),ISO);make_id(f);jsonobj(f,'newrecord','{"rinsed_at":"","brushed_at":"","status":"pending","violation_reason":""}')
    for k,n in [('record_id','id'),('consumed_at','stamp'),('brushing_deadline','deadline_iso'),('week_start','newweek')]:f.put('newrecord',k,var(n))
    f.put('records',token(var('id')),var('newrecord'));commit(f,root)
    f.a('notification',WFNotificationActionTitle='饮用已登记',WFNotificationActionBody='请立即用清水漱口。今晚记得刷牙打卡。')
    if not development:
        f.get('reminder_clock',var('state'),'reminder_time');h=f.iff(var('reminder_clock'),101);f.text('reminder_clock','23:00');f.end(h)
        f.fmt('reminder_day',var('now'),'yyyy-MM-dd');f.date('reminder_at',token(var('reminder_day'),'T',var('reminder_clock'),':00'))
        f.diff('reminder_margin',var('reminder_at'),var('deadline'));h=f.iff(var('reminder_margin'),1,0);f.adjust('reminder_at',var('deadline'),30,unit='min',op='Subtract');f.end(h)
        f.diff('reminder_future',var('now'),var('reminder_at'));h=f.iff(var('reminder_future'),1,0);f.set('reminder_at',var('now'));f.end(h)
        f.a('addnewreminder',WFCalendarItemTitle='可乐管理：睡前刷牙并打卡',WFCalendarItemNotes=token('记录 ',var('id'),'；截止 ',var('deadline_iso'),'；打开“我已经刷牙”'),WFAlertEnabled='Alert',WFAlertTrigger='At Time',WFAlertCustomTime=token(var('reminder_at')))
    f.stop('已登记。本周剩余0瓶。请立即用清水漱口；刷牙截止：',var('deadline_iso'));f.end(g)
    for mode,field in [('我已经漱口','rinsed_at'),('我已经刷牙','brushed_at')]:
        g=f.iff(var('mode'),4,mode);assert_has(f,var('candidate'),'没有最近48小时内可关联的饮用记录。')
        f.get('selected',var('records'),token(var('candidate')));f.get('done',var('selected'),field)
        h=f.iff(var('done'),5,EMPTY);f.stop('这条记录已打卡，不重复计数：',var('candidate_time'));f.end(h)
        f.a('alert',WFAlertActionTitle='确认关联这次饮用？',WFAlertActionMessage=token('饮用时间：',var('candidate_time'),'\n记录ID：',var('candidate'),'\n仅记录打卡；超时刷牙不会撤销已生效处罚。'),WFAlertActionCancelButtonShown=True)
        f.set('now',f.a('date',WFDateActionMode='Current Date'));f.fmt('stamp',var('now'),ISO);f.put('selected',field,var('stamp'))
        if field=='brushed_at':
            f.get('selected_deadline',var('selected'),'brushing_deadline');f.date('selected_due',token(var('selected_deadline')));f.diff('selected_late',var('selected_due'),var('now'))
            h=f.iff(var('selected_late'),2,0);f.put('selected','status','late');f.put('selected','violation_reason','未在约定截止时间前完成刷牙打卡（不验证实际刷牙行为）');f.otherwise(h);f.put('selected','status','compliant');f.put('selected','violation_reason',EMPTY);f.end(h)
        f.put('records',token(var('candidate')),var('selected'));commit(f,root);f.stop('打卡已保存：',var('stamp'));f.end(g)
    g=f.iff(var('mode'),4,'设置截止时间')
    f.set('newcutoff',f.a('ask',WFInputType='Text',WFAskActionPrompt='刷牙截止时间（24小时 HH:mm，例如 02:00）',WFAskActionDefaultAnswer='02:00'))
    f.set('validtime',f.a('text.match',text=token(var('newcutoff')),WFMatchTextPattern='^(?:[01][0-9]|2[0-3]):[0-5][0-9]$'))
    assert_has(f,var('validtime'),'时间格式无效，设置未修改。');choose(f,'newday',['饮用当天','饮用次日'],'截止日期')
    f.set('newreminder',f.a('ask',WFInputType='Text',WFAskActionPrompt='睡前提醒时间（HH:mm）',WFAskActionDefaultAnswer='23:00'));f.set('validreminder',f.a('text.match',text=token(var('newreminder')),WFMatchTextPattern='^(?:[01][0-9]|2[0-3]):[0-5][0-9]$'));assert_has(f,var('validreminder'),'提醒时间格式无效，设置未保存。');f.put('state','reminder_time',var('newreminder'))
    f.put('state','deadline_time',var('newcutoff'));f.put('state','deadline_next_day',0);h=f.iff(var('newday'),4,'饮用次日');f.put('state','deadline_next_day',1);f.end(h)
    commit(f,root);f.stop('设置已保存，仅对新饮用记录生效。请同步调整个人自动化时间。');f.end(g)
    g=f.iff(var('mode'),4,'导出备份')
    if flow:
        f.serialize_local()
    else:
        commit(f,root)
    f.save(var('serialized'),'ColaManager-backup.json',ask=True);f.stop('备份已导出。');f.end(g)
    stats(f)
    firstsave=f.iff(var('original_file'),101);commit(f,root);f.end(firstsave)
    g=f.iff(var('mode'),4,'查看历史记录');choose(f,'range',['最近4周','最近12周','最近52周','全部历史记录'],'历史范围（从初始化周开始）');
    f.set('selectedhistory',var('history'))
    for span in [4,12,52]:
        h=f.iff(var('range'),4,'最近'+str(span)+'周');f.set('selectedhistory',var('history'+str(span)));f.end(h)
    f.show(var('selectedhistory'));f.stop();f.end(g)
    g=f.iff(var('mode'),4,'每周报告');f.save(var('report'),token(root+'/report-',var('cw'),'.txt'));f.a('notification',WFNotificationActionTitle='可乐每周报告已生成',WFNotificationActionBody=token(var('report')));f.stop();f.end(g)
    g=f.iff(var('mode'),4,'截止检查');f.a('notification',WFNotificationActionTitle='可乐打卡检查',WFNotificationActionBody=token('已按实际截止时间检查。累计未按时打卡：',var('violations'),'；本周禁喝：',var('banned')));f.stop();f.end(g)
    f.show(var('report'),'\n最近12周饮用及打卡：\n',var('history12'));f.output(name)

def wrappers():
    for name,mode in [('我要喝可乐','我要喝可乐'),('我已经漱口','我已经漱口'),('我已经刷牙','我已经刷牙'),('查看可乐统计','查看统计报告'),('可乐每周报告','每周报告'),('可乐截止检查','截止检查')]:
        f=Flow();f.text('command',mode);f.a('runworkflow',WFWorkflowName='ColaManager',WFInput=var('command'));f.output(name)
if __name__=='__main__':
    main();main('可乐原生规则测试',test=True);wrappers()
