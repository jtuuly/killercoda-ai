import subprocess, re, smtplib, json
from http.server import HTTPServer, BaseHTTPRequestHandler
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formatdate, make_msgid, formataddr


def get_mx_record(domain):
    try:
        r = subprocess.check_output(
            ["nslookup", "-query=mx", domain],
            text=True, timeout=5,
            stdin=subprocess.DEVNULL, stderr=subprocess.STDOUT,
        )
        m = re.findall(r'exchanger\s*=\s*(?:\d+\s+)?([^\s\n]+)', r, re.IGNORECASE)
        if m:
            return m[0].rstrip('.')
    except:
        pass
    return None


def send_email(to_email, subject, content, from_email=None, from_name=None):
    domain = to_email.split('@')[-1]
    mx = get_mx_record(domain)
    if not mx:
        return {"code": 500, "msg": f"MX not found for {domain}"}
    fe = from_email or f"noreply@{domain}"
    fn = from_name or "Mailer"
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['From'] = formataddr((fn, fe))
    msg['To'] = to_email
    msg['Subject'] = Header(subject, 'utf-8').encode()
    msg['Date'] = formatdate(localtime=True)
    msg['Message-ID'] = make_msgid(domain=domain.split('.')[-1])
    msg['MIME-Version'] = '1.0'
    try:
        s = smtplib.SMTP(mx, 25, timeout=15)
        s.ehlo_or_helo_if_needed()
        e = s.sendmail(fe, [to_email], msg.as_string())
        s.quit()
        if not e:
            return {"code": 200, "msg": "OK", "mx": mx}
        return {"code": 207, "msg": "partial", "errors": e, "mx": mx}
    except Exception as ex:
        return {"code": 500, "msg": str(ex)}


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self._j({"code": 200, "msg": "MX Mailer API", "usage": "POST /send {to,subject,content}"})

    def do_POST(self):
        if self.path == '/send':
            try:
                b = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))))
            except:
                return self._j({"code": 400, "msg": "bad json"}, 400)
            if not b.get('to') or not b.get('subject') or not b.get('content'):
                return self._j({"code": 400, "msg": "missing: to,subject,content"}, 400)
            r = send_email(b['to'], b['subject'], b['content'], b.get('from_email'), b.get('from_name'))
            self._j(r, 200 if r['code'] == 200 else 500)
        else:
            self._j({"code": 404}, 404)

    def _j(self, d, c=200):
        self.send_response(c)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(d, ensure_ascii=False).encode())


if __name__ == '__main__':
    print('MX Mailer API -> http://0.0.0.0:8080')
    HTTPServer(('0.0.0.0', 8080), H).serve_forever()
