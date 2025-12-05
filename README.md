# QS 世界大学排名 MCP 服务器

这是一个基于 FastMCP 的 QS 世界大学排名查询服务器，提供智能化的大学搜索、排名查询、国家统计等多维度查询功能。

## 功能特性

本 MCP 服务器提供以下九个工具：

### 1. search_university - 大学搜索

根据关键词搜索大学，查看其排名和各项指标。

**参数：**
- `keyword`: 大学名称关键词（支持模糊匹配，不区分大小写），如"MIT"、"Peking"、"清华"
- `year`: 年份（可选，如2024、2025、2026），不指定则显示所有年份

**返回：**
- 匹配大学的排名信息和各项指标
- 多年排名趋势分析

### 2. get_top_universities - 排名查询

按年份和国家/地区查询排名前N的大学。

**参数：**
- `year`: 年份（必填，如2024、2025、2026）
- `country`: 国家/地区代码或名称（可选，如CN、US、UK、China）
- `top_n`: 显示前N名（默认10，最大100）

**返回：**
- 排名前N的大学列表
- 包含各项评分指标

### 3. get_country_stats - 国家统计

按国家/地区统计大学数量和分布。

**参数：**
- `year`: 年份（必填）
- `top_n`: 显示前N个国家（默认20）

**返回：**
- 各国家/地区大学数量统计
- 有排名大学数量
- 占比百分比

### 4. get_country_scores - 国家平均分对比

按国家/地区统计平均分数。

**参数：**
- `year`: 年份（必填）
- `top_n`: 显示前N个国家（默认15）

**返回：**
- 各国平均分、最高分、最低分
- 最佳排名大学

### 5. get_rank_changes - 排名变化

查看排名变化最大的大学。

**参数：**
- `year`: 年份（必填，会与前一年对比）
- `top_n`: 显示前N所大学（默认20）
- `direction`: 变化方向，"rise"上升或"fall"下降

**返回：**
- 排名变化最大的大学列表
- 包含去年和今年排名对比

### 6. get_top100_distribution - Top 100 分布

查看 Top 100 大学的国家分布。

**参数：**
- `year`: 年份（必填）

**返回：**
- Top 100 大学的国家分布统计
- 各国占比

### 7. get_summary - 综合统计

获取指定年份的综合统计摘要。

**参数：**
- `year`: 年份（必填）

**返回：**
- 基本信息（总大学数、排名数、国家数）
- Top 10 大学
- Top 5 国家
- 分数统计
- 与去年对比

### 8. list_available_years - 查看可用年份

列出数据中所有可用的年份。

**返回：**
- 可用年份列表
- 最新年份

### 9. list_countries - 查看国家列表

列出数据中所有可用的国家/地区。

**参数：**
- `year`: 年份（可选）

**返回：**
- 可用国家/地区列表

## 数据来源

使用 QS 世界大学排名数据（2024-2026年），包含以下指标：
- Overall Score（综合分数）
- Academic Reputation（学术声誉）
- Employer Reputation（雇主声誉）
- Faculty Student Ratio（师生比）
- Citations per Faculty（论文引用）
- International Faculty（国际教师）
- International Students（国际学生）
- International Research Network（国际研究网络）
- Employment Outcomes（就业成果）
- Sustainability（可持续发展）

## 安装与运行

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务器
python mcp_server.py
```

### 阿里云函数计算部署

1. 确保 `qs_cleaned.csv` 数据文件在项目根目录
2. 运行构建脚本：
   ```bash
   chmod +x build.sh
   ./build.sh
   ```
3. 打包上传到阿里云函数计算
4. 设置启动命令为 `./run.sh`

## 环境变量

- `QS_CSV_PATH`: 数据文件路径（可选，默认自动查找）
- `PORT` / `MCP_PORT`: 服务端口（默认 9001）

## API 接口

服务器使用 SSE (Server-Sent Events) 模式运行，默认监听地址：
- 本地：`http://localhost:9001/sse`
- 网络：`http://0.0.0.0:9001/sse`

## 使用示例

### 搜索大学
```json
{
  "tool": "search_university",
  "arguments": {
    "keyword": "MIT",
    "year": 2026
  }
}
```

### 查询中国大学排名
```json
{
  "tool": "get_top_universities",
  "arguments": {
    "year": 2026,
    "country": "CN",
    "top_n": 20
  }
}
```

### 查看排名变化
```json
{
  "tool": "get_rank_changes",
  "arguments": {
    "year": 2026,
    "top_n": 10,
    "direction": "rise"
  }
}
```

## 项目结构

```
qs_mcp/
├── mcp_server.py      # MCP 服务器主程序
├── qs_cleaned.csv     # QS 排名数据文件
├── qs_search.py       # 原控制台搜索程序
├── qs_stats.py        # 原控制台统计程序
├── qs_top.py          # 原控制台排名程序
├── requirements.txt   # Python 依赖
├── build.sh           # 构建脚本
├── run.sh             # 启动脚本
└── README.md          # 项目说明
```

## 许可证

MIT License
