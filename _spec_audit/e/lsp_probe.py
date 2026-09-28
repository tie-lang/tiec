import json, subprocess, sys

def frame(obj):
    b = json.dumps(obj).encode('utf-8')
    return b"Content-Length: %d\r\n\r\n%s" % (len(b), b)

exe = sys.argv[1]
p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

init = {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"processId":None,"rootUri":None,"capabilities":{}}}
p.stdin.write(frame(init)); p.stdin.flush()

# read one message
import time
time.sleep(1.5)
p.stdin.close()
try:
    out, err = p.communicate(timeout=5)
except subprocess.TimeoutExpired:
    p.kill(); out, err = p.communicate()
print("STDOUT:", out[:800].decode('utf-8','replace'))
print("STDERR:", err[:400].decode('utf-8','replace'))
