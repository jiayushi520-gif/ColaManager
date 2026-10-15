"""Build local-only artifacts in a separate staging area. No automatic signing."""
from pathlib import Path
import build_shortcuts as b
from native_manager import main, wrappers
from local_storage import LocalFlow

ROOT = Path(__file__).resolve().parents[1]
b.WORK = ROOT / 'work' / 'v2'
b.WORK.mkdir(parents=True, exist_ok=True)
main('ColaManager', flow=LocalFlow())
wrappers()
f = b.Flow()
f.a('notification', WFNotificationActionTitle='可乐管理：睡前提醒', WFNotificationActionBody='如果今天喝了可乐，请刷牙后运行“我已经刷牙”。')
f.output('可乐睡前提醒')
f = b.Flow()
f.show('可乐管理器2.0.0导入测试通过；此提示不代表本地数据已保存。')
f.output('ColaManager-Test')
main('ColaManager-v2-Rules-Test', test=True, flow=LocalFlow())
