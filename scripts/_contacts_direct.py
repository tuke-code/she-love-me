"""直接查询 SQLite 数据库列出联系人，输出到文件"""
import sqlite3, os, json, sys, re

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

DECRYPTED = "vendor/wechat-decrypt/decrypted"
OUT = "data/contacts.json"

os.makedirs("data", exist_ok=True)

# 1. 读取联系人
contacts = {}
contact_db = os.path.join(DECRYPTED, "contact", "contact.db")
if os.path.exists(contact_db):
    try:
        with sqlite3.connect(contact_db) as conn:
            rows = conn.execute("SELECT username, nick_name, remark FROM contact WHERE username NOT LIKE '%@chatroom%' AND username NOT LIKE 'gh_%' LIMIT 5000").fetchall()
        for username, nick_name, remark in rows:
            contacts[username] = {
                "username": username,
                "nick_name": nick_name or "",
                "remark": remark or "",
                "display_name": remark or nick_name or username,
                "message_count": 0
            }
        print(f"[联系人] 读取 {len(contacts)} 个", file=sys.stderr)
    except Exception as e:
        print(f"[ERR] contact.db: {e}", file=sys.stderr)

# 2. 统计消息数量
msg_dir = os.path.join(DECRYPTED, "message")
if os.path.exists(msg_dir):
    for fname in sorted(os.listdir(msg_dir)):
        if not fname.endswith(".db"):
            continue
        db_path = os.path.join(msg_dir, fname)
        try:
            with sqlite3.connect(db_path) as conn:
                # Name2Id: user_name 列
                import hashlib
                try:
                    rows2 = conn.execute("SELECT user_name FROM Name2Id").fetchall()
                except:
                    continue
                for (user_name,) in rows2:
                    if not user_name or user_name not in contacts:
                        continue
                    table_hash = hashlib.md5(user_name.encode()).hexdigest()
                    table_name = f"Msg_{table_hash}"
                    try:
                        cnt = conn.execute(f"SELECT COUNT(*) FROM [{table_name}]").fetchone()[0]
                        contacts[user_name]["message_count"] += cnt
                    except:
                        pass
        except Exception as e:
            print(f"[WARN] {fname}: {e}", file=sys.stderr)

# 3. 排序并输出
result = sorted(contacts.values(), key=lambda x: x["message_count"], reverse=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"[OK] {len(result)} 个联系人已保存到 {OUT}")
for i, c in enumerate(result[:30], 1):
    print(f"{i:2}. {c['display_name']:<30} {c['message_count']:>6} 条")
