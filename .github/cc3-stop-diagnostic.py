from pathlib import Path

path = Path('.github/scripts/server-persistence-smoke.sh')
text = path.read_text(encoding='utf-8')
old = '''    echo "Server did not stop cleanly after the RCON stop command." >&2
    cat "${log_file}" >&2
    return 1
'''
new = '''    capture_save_flush_thread_dumps
    echo "Server did not stop cleanly after the RCON stop command." >&2
    cat "${log_file}" >&2
    return 1
'''
if old not in text:
    raise SystemExit('Expected stop timeout block was not found')
path.write_text(text.replace(old, new, 1), encoding='utf-8')
