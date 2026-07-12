import socket

def send_email(to_email, subject, content, from_email=None, from_name=None):
    domain = to_email.split('@')[-1]
    mx_server = get_mx_record(domain)
    if not mx_server:
        return {"code": 500, "msg": f"MX not found for {domain}"}

    # 强制解析为 IPv4 地址
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
        smtp = smtplib.SMTP(ipv4, 25, timeout=15)  # 用 IPv4 地址连接
        smtp.ehlo_or_helo_if_needed()
        errors = smtp.sendmail(fake_from_addr, [to_email], msg.as_string())
        smtp.quit()
        if not errors:
            return {"code": 200, "msg": "OK", "mx": mx_server}
        return {"code": 207, "msg": "partial error", "errors": errors, "mx": mx_server}
    except Exception as e:
        return {"code": 500, "msg": str(e)}
