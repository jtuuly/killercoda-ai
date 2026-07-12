# MX Mailer API

通过直接连接目标域名的 MX 服务器投递邮件，无需任何第三方 SMTP 服务、账号密码或 API Key。纯 Python 标准库实现，零依赖。

## 一键部署（Ubuntu / Killercoda）

```bash
git clone https://github.com/jtuuly/killercoda-ai.git && cd killercoda-ai && bash setup.sh
```

## 使用方法

### 发送邮件

```bash
curl -X POST http://localhost:8080/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "target@example.com",
    "subject": "邮件标题",
    "content": "邮件正文"
  }'
```

### 自定义发件人

```bash
curl -X POST http://localhost:8080/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "target@example.com",
    "subject": "邮件标题",
    "content": "邮件正文",
    "from_email": "admin@example.com",
    "from_name": "MyApp"
  }'
```

### 返回示例

成功：
```json
{"code": 200, "msg": "OK", "mx": "route2.mx.cloudflare.net"}
```

失败：
```json
{"code": 500, "msg": "MX not found for example.com"}
```

## API 接口

### `GET /`

服务状态检查。

### `POST /send`

| 参数 | 必填 | 说明 |
|------|------|------|
| `to` | ✅ | 收件人邮箱地址 |
| `subject` | ✅ | 邮件标题 |
| `content` | ✅ | 邮件正文（纯文本） |
| `from_email` | ❌ | 发件人邮箱，默认 `admin@收件人域名` |
| `from_name` | ❌ | 发件人名称，默认 `Matrix Mailer` |

## 原理

```
查询 MX 记录 → 直连目标 MX 服务器:25 → SMTP 握手 → 投递邮件
```

不经过任何中转 SMTP 服务器，直接与收件人域名的邮件服务器通信。

## 文件说明

| 文件 | 说明 |
|------|------|
| `setup.sh` | 自动安装依赖并启动服务 |
| `mail_api.py` | API 服务主程序 |

## 注意事项

- 需要出站 25 端口开放
- 直连投递的邮件可能被标记为垃圾邮件（缺少 SPF/DKIM/DMARC 验证）
- 仅用于学习和测试用途
