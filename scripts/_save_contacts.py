"""直接将联系人列表保存到文件，绕过 stdout 干扰"""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 直接 import list_contacts 模块逻辑
sys.path.insert(0, os.path.dirname(__file__))
import importlib.util, types

# 动态加载 list_contacts
spec = importlib.util.spec_from_file_location("list_contacts",
    os.path.join(os.path.dirname(__file__), "list_contacts.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

decrypted_dir = "vendor/wechat-decrypt/decrypted"
contacts = mod.load_contacts(decrypted_dir)
counts = mod.count_messages(decrypted_dir, contacts)

result = []
for c in contacts:
    username, nick_name, remark = c
    display = remark or nick_name or username
    result.append({
        "username": username,
        "nick_name": nick_name,
        "remark": remark,
        "display_name": display,
        "message_count": counts.get(username, 0)
    })

result.sort(key=lambda x: x["message_count"], reverse=True)

os.makedirs("data", exist_ok=True)
with open("data/contacts.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"[OK] 共 {len(result)} 个联系人，已保存到 data/contacts.json")
for i, c in enumerate(result[:30], 1):
    print(f"{i:2}. {c['display_name']:30} {c['message_count']:6} 条")
