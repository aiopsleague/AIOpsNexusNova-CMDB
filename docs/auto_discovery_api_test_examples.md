# 自动发现 API 测试示例

> 面向 OneAgent / OneMaster 开发者的 CMDB 自动发现接口测试用例。
> 配套文档：[自动发现总览](auto_discovery.md)、[Agent 开发指南](agent_dev_guide.md)。

---

## 前置准备

### 1. 启动 CMDB 服务

```bash
cd cmdb-api && python main.py
```

### 2. 创建 Agent 账号并获取 Key/Secret

```bash
python cli.py cmdb-agent-init
```

输出示例：

```
cmdb_agent key: e8192713e651414eaf0ce4ce7e376c0f
cmdb_agent secret: ~bS16KDMunwIH?l5Bp2#NFGPz7$tifmy
```

> ⚠️ `secret` 可能包含特殊字符（`?`、`#`、`$` 等），在 curl 中使用时**必须先 URL 编码**：
>
> ```python
> from urllib.parse import quote
> raw_secret = "~bS16KDMunwIH?l5Bp2#NFGPz7$tifmy"
> print(quote(raw_secret, safe=''))
> # ~bS16KDMunwIH%3Fl5Bp2%23NFGPz7%24tifmy
> ```

---

## 1. 同步规则（GET /adt/sync）

Agent 从 CMDB 拉取属于自己的采集规则：

```bash
curl -X GET 'http://127.0.0.1:5000/api/v0.1/adt/sync?_key=e8192713e651414eaf0ce4ce7e376c0f&_secret=<ENCODED_SECRET>&oneagent_id=0xABCD&oneagent_name=test-agent&last_update_at=2026-01-01%2000:00:00'
```

---

## 2. 上报发现实例（POST /adc）

Agent 采集完成后，将实例数据上报给 CMDB：

```bash
curl -X POST 'http://127.0.0.1:5000/api/v0.1/adc?_key=e8192713e651414eaf0ce4ce7e376c0f&_secret=~bS16KDMunwIH%3Fl5Bp2%23NFGPz7%24tifmy' \
  -H 'Content-Type: application/json' \
  -d '{
    "type_id": 128,
    "adt_id": 8,
    "instance": {
      "uuid": "web-server-01",
      "ram_size": 8,
      "host_name": "abelit_web_server"
    },
    "unique_value": "web-server-01"
  }'
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type_id` | int | ✅ | CI 类型 ID（从规则同步的 `rules[].type_id` 获取） |
| `adt_id` | int | ✅ | ADT 映射 ID（从规则同步的 `rules[].id` 获取） |
| `instance` | object | ✅ | 采集到的原始数据，字段名使用 ad_key |
| `unique_value` | string | ✅ | 唯一标识字段的值，CMDB 以 `(type_id, unique_value)` 去重 |

### 常见错误

| 错误信息 | 原因 | 解决 |
|---------|------|------|
| `The request is missing parameters type_id` | JSON 格式错误（如多余逗号）或参数不在 body 中 | 检查 JSON 语法，确保 `application/json` Content-Type |
| `403 Forbidden` | 签名验证失败 | 检查 `_secret` 是否 URL 编码，签名算法是否正确 |
| `400 ad_not_unique_key` | `unique_value` 与模型唯一属性不对应 | 确认 `instance` 中包含唯一字段且值匹配 |

---

## 3. 删除发现实例（DELETE /adc）

资源消失时主动清理：

```bash
curl -X DELETE 'http://127.0.0.1:5000/api/v0.1/adc?_key=e8192713e651414eaf0ce4ce7e376c0f&_secret=<ENCODED_SECRET>&type_id=128&unique_value=web-server-01'
```

---

## 4. 上报执行历史（POST /adc/exec/histories）

每次采集后可选上报执行日志：

```bash
curl -X POST 'http://127.0.0.1:5000/api/v0.1/adc/exec/histories?_key=e8192713e651414eaf0ce4ce7e376c0f&_secret=<ENCODED_SECRET>' \
  -H 'Content-Type: application/json' \
  -d '{
    "type_id": 128,
    "stdout": "collect ok: 1 records"
  }'
```

---

## 签名算法参考（Python）

curl 中需手动计算签名，但实际 Agent 代码中应动态生成：

```python
import hashlib
from urllib.parse import quote


def build_signature(path: str, raw_secret: str, params: dict) -> str:
    """计算 CMDB API Key 签名。

    Args:
        path: 请求路径，如 "/api/v0.1/adc"
        raw_secret: cmdb-agent-init 打印的原始 secret
        params: 除 _key / _secret 外所有标量参数（排除 dict/list）

    Returns:
        SHA1 十六进制签名字符串
    """
    sorted_values = "".join(
        str(params[k]) for k in sorted(params.keys())
        if not isinstance(params[k], (dict, list))
    )
    sign_str = path + raw_secret + sorted_values
    return hashlib.sha1(sign_str.encode()).hexdigest()


def encode_secret(raw_secret: str) -> str:
    """对 secret 做 URL 编码（用于 curl query string）。"""
    return quote(raw_secret, safe='')
