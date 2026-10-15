"""Generate unsigned native workflows and Scriptable bundle."""
from native_manager import *
WORK.mkdir(exist_ok=True);DIST.mkdir(exist_ok=True)
main(); wrappers()
f=Flow();f.show('可乐管理系统运行成功');f.output('ColaManager-Test')
f=Flow();f.a('notification',WFNotificationActionTitle='可乐管理：睡前提醒',WFNotificationActionBody='如果今天喝了可乐，请完成刷牙，并运行“我已经刷牙”打卡。');f.output('可乐睡前提醒')
main('可乐规则验收',test=True)
main('可乐最终写入验收',root='ColaManager-Development/Release',development=True)
(DIST/'ColaManager-Widget.js').write_text((ROOT/'src/cola_core.js').read_text()+'\n'+(ROOT/'src/widget.js').read_text())

f=Flow();f.set('now',f.a('date',WFDateActionMode='Current Date'));f.adjust('at',var('now'),5,unit='min');f.a('addnewreminder',WFCalendarItemTitle='[开发验收] 可乐刷牙提醒（可删除）',WFCalendarItemNotes='仅用于验证提醒事项动作，不是饮用记录。',WFAlertEnabled='Alert',WFAlertTrigger='At Time',WFAlertCustomTime=token(var('at')));f.stop('提醒动作已运行');f.output('可乐提醒验收')
