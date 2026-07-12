import subprocess
import re
import smtplib
import socket
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formatdate, make_msgid, formataddr


HTML = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MX Mailer</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0f0f0f;color:#e0e0e0;font-family:system-ui,sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh}
.box{background:#1a1a2e;border:1px solid #333;border-radius:12px;padding:32px;width:460px}
h1{font-size:20px;margin-bottom:24px;color:#00d4ff}
label{display:block;font-size:13px;color:#888;margin-bottom:4px}
input,textarea{width:100%;padding:10px 12px;border:1px solid #333;border-radius:6px;background:#111;color:#fff;font-size:14px;margin-bottom:14px;outline:none}
input:focus,textarea:focus{border-color:#00d4ff}
textarea{height:80px;resize:vertical}
button{width:100%;padding:12px;background:#00d4ff;color:#000;border:none;border-radius:6px;font-size:15px;font-weight:bold;cursor:pointer}
button:hover{background:#00b8d9}
#result{margin-top:14px;padding:10px;border-radius:6px;font-size:13px;display:none;word-break:break-all}
.ok{display:block!important;background:#0a2e1a;border:1px solid #00ff88;color:#00ff88}
.err{display:block!important;background:#2e0a0a;border:1px solid #ff4444;color:#ff4444}
</style>
</head>
<body>
<div class="box">
<h1>MX Mailer</h1>
<label>收件人 (To)</label>
<input id="to" placeholder="target@example.com">
<label>发件人邮箱 (From Email)</label>
<input id="fe" placeholder="admin@example.com">
<label>发件人名称 (From Name)</label>
<input id="fn" placeholder="Matrix Mailer">
<label>主题 (Subject)</label>
<input id="subject" placeholder="邮件标题">
<label>正文 (Content)</label>
<textarea id="content" placeholder="邮件正文"></textarea>
<button onclick="send()">发送</button>
<div id="result"></div>
</div>
<script>
async function send(){
  var r=document.getElementById('result');
  r.className='';r.style.display='none';r.textContent='';
  var body={to:document.getElementById('to').value,subject:document.getElementById('subject').value,
    content:document.getElementById('content').value,
    from_email:document.getElementById('fe').value||undefined,
    from_name:document.getElementById('fn').value||undefined};
  try{
    var res=await fetch('/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    var data=await res.json();
    r.textContent=JSON.stringify(data,null,2);
    r.className=data.code===200?'ok':'err';
  }catch(e){r.textContent='请求失败: '+e.message;r.className='err';}
}
</script>
</body>
</html>"""


def get_mx_record(domain):
    try:
        result = subprocess.check_output(
            ["nslookup", "-query=mx", domain],
            text=True, timeout=5,
            stdin=subprocess.DEVNULL, stderr=subprocess.STDOUT,
        )
        raw_servers = re.findall(r'exchanger\s*=\s*(?:\d+\s+)?([^\s\n]+)', result, re.IGNORECASE)
        if raw_servers:
            return raw_servers[0].rstrip('.')
    except Exception:
        pass
    return None


def send_email(to_email, subject, content, from_email=None, from_name=None):
    domain = to_email.split('@')[-1]
    mx_server = get_mx_record(domain)
    if not mx_server:
        return {"code": 500, "msg": f"MX not found for {domain}"}
    try:
        ipv4 = socket.getaddrinfo(mx_server, 25, socket.AF_INET)[0][4][0]
    except Exception:
        ipv4 = mx_server
    fake_from_addr = from_email or f"admin@{domain}"
    fake_from_name = from_name or "Matrix Mailer"
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['From'] = f'"{fake_from_name}" <{fake_from_addr}>'
    msg['To'] = to_email
    msg['Subject'] = Header(subject, 'utf-8').encode()
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid(domain=domain.split('.')[-1])
    msg['MIME-Version'] = '1.0'
    try:
        smtp = smtplib.SMTP(ipv4, 25, timeout=15)
        smtp.ehlo_or_helo_if_needed()
        errors = smtp.sendmail(fake_from_addr, [to_email], msg.as_string())
        smtp.quit()
        if not errors:
            return {"code": 200, "msg": "OK", "mx": mx_server}
        return {"code": 207, "msg": "partial error", "errors": errors, "mx": mx_server}
    except Exception as e:
        return {"code": 500, "msg": str(e)}


class MailHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(HTML.encode())

    def do_POST(self):
        if self.path == '/send':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length).decode())
            except Exception:
                return self._json({"code": 400, "msg": "invalid JSON"}, 400)
            to = body.get('to')
            subject = body.get('subject')
            content = body.get('content')
            if not to or not subject or not content:
                return self._json({"code": 400, "msg": "missing: to, subject, content"}, 400)
            result = send_email(to, subject, content,
                                from_email=body.get('from_email'),
                                from_name=body.get('from_name'))
            self._json(result, 200 if result['code'] == 200 else 500)
        else:
            self._json({"code": 404, "msg": "not found"}, 404)

    def _json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())


if __name__ == '__main__':
    print('MX Mailer -> http://0.0.0.0:8080')
    HTTPServer(('0.0.0.0', 8080), MailHandler).serve_forever()
