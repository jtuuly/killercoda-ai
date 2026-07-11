import subprocess
import re
import smtplib
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formatdate, make_msgid, formataddr


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
        smtp = smtplib.SMTP(mx_server, 25, timeout=15)
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
        if self.path == '/':
            self._json({"code": 200, "msg": "MX Mailer API", "usage": "POST /send {to,subject,content}"})
        else:
            self._json({"code": 404, "msg": "not found"}, 404)

    def do_POST(self):
        if self.path == '/send':
            try:
                length = int(self.headers.get('Content-Length', 0))
                body = json.loads(self.rfile.read(length).decode())
            except Exception:
                self._json({"code": 400, "msg": "invalid JSON"}, 400)
                return
            to = body.get('to')
            subject = body.get('subject')
            content = body.get('content')
            if not to or not subject or not content:
                self._json({"code": 400, "msg": "missing: to, subject, content"}, 400)
                return
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
    print('MX Mailer API -> http://0.0.0.0:8080')
    HTTPServer(('0.0.0.0', 8080), MailHandler).serve_forever()
