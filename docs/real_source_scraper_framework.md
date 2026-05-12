# 五大六小招标平台抓取改造框架

本文档说明如何基于现有程序接入“五大六小”招标平台，获取光伏、风电、储能、柔性支架、漂浮光伏等招标信息，并继续使用现有的本地存储和企业微信推送能力。

## 目标

1. 从官方招标/采购平台抓取公告。
2. 按新能源关键词筛选：
   - 光伏
   - 风电
   - 储能
   - 柔性支架
   - 漂浮光伏
3. 匹配公司和平台来源。
4. 保存到本地 SQLite 数据库。
5. 对未推送过的新公告发送企业微信消息。

## 已加入的配置

平台清单已写入：

```text
config/sources.yaml
```

关键词已扩展到：

```text
config/keywords.yaml
```

当前覆盖平台：

| 类别 | 企业 | 平台 |
| --- | --- | --- |
| 五大 | 国家能源集团 | 国家能源招标网 / 国能e招 |
| 五大 | 中国华能集团 | 华能电子商务平台 |
| 五大 | 中国大唐集团 | 大唐集团电子商务平台 |
| 五大 | 中国华电集团 | 华电集团电子商务平台 |
| 五大 | 国家电力投资集团 | 国家电投电子商务平台 / 电能e招采 |
| 六小 | 国投集团 / 国投电力 | 国投集团电子采购平台 |
| 六小 | 中国三峡集团 | 中国三峡集团电子采购平台 |
| 六小 | 中国广核集团 | 中广核电子商务平台 |
| 六小 | 华润集团 / 华润电力 | 华润集团守正电子招标采购平台 |
| 六小 | 中国节能环保集团 | 中国节能电子采购平台 |
| 六小 | 中国核工业集团 | 中核集团电子采购平台 |

## 当前代码框架

### 1. 来源配置模型

文件：

```text
src/source_config.py
```

作用：

- 读取 `config/sources.yaml`
- 转换成 `TenderSource`
- 过滤 `enabled: true` 的平台

### 2. 抓取器入口

文件：

```text
src/scraper.py
```

当前包含：

- `TenderScraper`：抓取器接口
- `DemoTenderScraper`：示例数据源
- `ConfiguredSourceScraper`：真实平台占位抓取器
- `build_scrapers()`：根据配置组装多个抓取器

### 3. 主流程

文件：

```text
src/pipeline.py
```

现在流程是：

```text
加载配置 -> 创建多个 scraper -> 抓取公告 -> 匹配关键词/公司 -> 保存数据库 -> 企业微信推送
```

## 后续实现真实抓取的建议步骤

### 第一步：先接 1 个平台

建议从页面结构最容易解析的平台开始，不要一次写 11 个。

推荐顺序：

1. 中国节能电子采购平台
2. 中国三峡集团电子采购平台
3. 国家能源招标网 / 国能e招
4. 华润守正平台

### 第二步：为每个平台新增专用解析器

建议新增目录：

```text
src/scrapers/
```

示例文件：

```text
src/scrapers/cecep.py
src/scrapers/ctg.py
src/scrapers/chnenergy.py
```

每个文件实现统一方法：

```python
def crawl(source: TenderSource, timeout: int) -> list[TenderItem]:
    ...
```

### 第三步：解析字段

每条公告至少需要：

```text
title         公告标题
url           官方公告链接
source        平台名称
published_at  发布时间
```

程序会自动补充：

```text
matched_keywords
matched_companies
notified
created_at
```

### 第四步：处理动态页面

多数招标平台可能存在：

- 动态渲染
- 分页接口
- 查询接口
- 验证码
- 登录限制
- 反爬限制

优先查找网页背后的公开 JSON 接口。如果没有稳定接口，再考虑 Playwright 浏览器自动化。

### 第五步：合规检查

正式抓取前应检查：

- robots.txt
- 平台用户协议
- 是否要求登录
- 是否限制自动访问
- 访问频率是否合理

建议设置低频率定时任务，例如每 30 分钟或每 1 小时运行一次。

## 运行方式

只抓取并保存：

```powershell
& C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe "d:/Python Code/Tender Information/main.py" crawl-only
```

抓取、保存并推送：

```powershell
& C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe "d:/Python Code/Tender Information/main.py" run-once
```

查看最近记录：

```powershell
& C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe "d:/Python Code/Tender Information/main.py" list-latest --limit 10
```

测试企业微信：

```powershell
& C:/ProgramData/spyder-6/envs/spyder-runtime/python.exe "d:/Python Code/Tender Information/main.py" test-wecom
```

