# -*- coding: utf-8 -*-
"""
QS 世界大学排名 MCP 服务器
基于 FastMCP 框架构建的 QS 大学排名查询系统

改进说明:
1. 增强参数验证 - 对年份、top_n 等参数进行严格验证
2. 统一错误处理 - 使用标准化错误响应格式，包含错误类型和详细信息
3. 统一国家标识符 - 所有 API 返回统一的国家信息结构（ISO 代码 + 显示名称）
4. 优化数据结构 - 返回结构更加一致，包含 query、summary、data 三层结构
"""

import os
import logging
import json
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP
import pandas as pd
from datetime import datetime

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("qs_rankings_mcp.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建 FastMCP 服务器实例
mcp = FastMCP("qs-university-rankings")

# 全局数据存储
_df = None
_csv_path = None

# 数据文件名
DATA_FILE = "qs_cleaned.csv"

# ========== 国家代码映射 (ISO 3166-1 alpha-2) ==========
# 标准化为 ISO 代码，便于统一识别
# 注意：所有数据中的国家名称变体都需要映射到对应的 ISO 代码
COUNTRY_TO_ISO = {
    # 美国（数据中存在多种写法）
    "United States": "US",
    "United States of America": "US",
    "USA": "US",
    "America": "US",
    # 英国
    "United Kingdom": "GB",
    "UK": "GB",
    "England": "GB",
    "Britain": "GB",
    # 中国大陆
    "China (Mainland)": "CN",
    "China": "CN",
    # 香港（数据中存在多种写法）
    "Hong Kong SAR": "HK",
    "Hong Kong": "HK",
    "Hong Kong SAR, China": "HK",
    # 澳门（数据中存在多种写法）
    "Macau SAR": "MO",
    "Macao SAR": "MO",
    "Macao SAR, China": "MO",
    "Macau": "MO",
    # 台湾
    "Taiwan": "TW",
    "Taiwan, China": "TW",
    # 新加坡
    "Singapore": "SG",
    # 日本
    "Japan": "JP",
    # 韩国
    "South Korea": "KR",
    "Republic of Korea": "KR",
    "Korea": "KR",
    "Korea, Republic of": "KR",
    # 德国
    "Germany": "DE",
    # 法国
    "France": "FR",
    # 澳大利亚
    "Australia": "AU",
    # 加拿大
    "Canada": "CA",
    # 瑞士
    "Switzerland": "CH",
    "Swiss": "CH",
    # 荷兰
    "Netherlands": "NL",
    "The Netherlands": "NL",
    # 瑞典
    "Sweden": "SE",
    # 意大利
    "Italy": "IT",
    # 西班牙
    "Spain": "ES",
    # 俄罗斯
    "Russia": "RU",
    "Russian Federation": "RU",
    # 印度
    "India": "IN",
    # 巴西
    "Brazil": "BR",
    # 墨西哥
    "Mexico": "MX",
    # 土耳其
    "Turkey": "TR",
    "Türkiye": "TR",
    # 其他常见国家
    "New Zealand": "NZ",
    "Ireland": "IE",
    "Belgium": "BE",
    "Austria": "AT",
    "Denmark": "DK",
    "Norway": "NO",
    "Finland": "FI",
    "Poland": "PL",
    "Portugal": "PT",
    "Czech Republic": "CZ",
    "Czechia": "CZ",
    "Greece": "GR",
    "Israel": "IL",
    "Saudi Arabia": "SA",
    "United Arab Emirates": "AE",
    "UAE": "AE",
    "Malaysia": "MY",
    "Thailand": "TH",
    "Indonesia": "ID",
    "Philippines": "PH",
    "Vietnam": "VN",
    "Viet Nam": "VN",
    "Pakistan": "PK",
    "Bangladesh": "BD",
    "Egypt": "EG",
    "South Africa": "ZA",
    "Nigeria": "NG",
    "Argentina": "AR",
    "Chile": "CL",
    "Colombia": "CO",
    "Peru": "PE",
    "Qatar": "QA",
    "Kuwait": "KW",
    "Bahrain": "BH",
    "Oman": "OM",
    "Jordan": "JO",
    "Lebanon": "LB",
    "Iran": "IR",
    "Iran, Islamic Republic of": "IR",
    "Iran (Islamic Republic of)": "IR",
    "Iraq": "IQ",
    # 欧洲补充
    "Armenia": "AM",
    "Azerbaijan": "AZ",
    "Belarus": "BY",
    "Bosnia and Herzegovina": "BA",
    "Bulgaria": "BG",
    "Croatia": "HR",
    "Cyprus": "CY",
    "Northern Cyprus": "CY",  # 归入塞浦路斯
    "Estonia": "EE",
    "Georgia": "GE",
    "Hungary": "HU",
    "Iceland": "IS",
    "Latvia": "LV",
    "Lithuania": "LT",
    "Luxembourg": "LU",
    "Malta": "MT",
    "Romania": "RO",
    "Serbia": "RS",
    "Slovakia": "SK",
    "Slovenia": "SI",
    "Ukraine": "UA",
    # 亚洲补充
    "Brunei": "BN",
    "Brunei Darussalam": "BN",
    "Kazakhstan": "KZ",
    "Kyrgyzstan": "KG",
    "Sri Lanka": "LK",
    "Uzbekistan": "UZ",
    # 中东补充
    "Palestine": "PS",
    "Libya": "LY",
    "Syria": "SY",
    "Syrian Arab Republic": "SY",
    # 非洲补充
    "Morocco": "MA",
    "Tunisia": "TN",
    "Kenya": "KE",
    "Ghana": "GH",
    "Ethiopia": "ET",
    "Uganda": "UG",
    "Sudan": "SD",
    # 美洲补充
    "Costa Rica": "CR",
    "Cuba": "CU",
    "Dominican Republic": "DO",
    "Ecuador": "EC",
    "Guatemala": "GT",
    "Honduras": "HN",
    "Panama": "PA",
    "Paraguay": "PY",
    "Puerto Rico": "PR",
    "Uruguay": "UY",
    "Venezuela": "VE",
    "Venezuela (Bolivarian Republic of)": "VE",
}

# ISO 代码到标准显示名称（完整映射，覆盖数据中所有 ISO 代码）
# 确保每个国家只有一个标准名称
ISO_TO_DISPLAY = {
    # 主要国家/地区
    "US": "United States",
    "GB": "United Kingdom",
    "UK": "United Kingdom",  # 别名
    "CN": "China (Mainland)",
    "HK": "Hong Kong SAR",
    "MO": "Macau SAR",
    "TW": "Taiwan",
    "SG": "Singapore",
    "JP": "Japan",
    "KR": "South Korea",
    "DE": "Germany",
    "FR": "France",
    "AU": "Australia",
    "CA": "Canada",
    "CH": "Switzerland",
    "NL": "Netherlands",
    "SE": "Sweden",
    "IT": "Italy",
    "ES": "Spain",
    "RU": "Russia",
    "IN": "India",
    "BR": "Brazil",
    "MX": "Mexico",
    "TR": "Turkey",
    # 欧洲
    "NZ": "New Zealand",
    "IE": "Ireland",
    "BE": "Belgium",
    "AT": "Austria",
    "DK": "Denmark",
    "NO": "Norway",
    "FI": "Finland",
    "PL": "Poland",
    "PT": "Portugal",
    "CZ": "Czech Republic",
    "GR": "Greece",
    "HU": "Hungary",
    "RO": "Romania",
    "BG": "Bulgaria",
    "HR": "Croatia",
    "SI": "Slovenia",
    "SK": "Slovakia",
    "RS": "Serbia",
    "BA": "Bosnia and Herzegovina",
    "EE": "Estonia",
    "LV": "Latvia",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "MT": "Malta",
    "CY": "Cyprus",
    "IS": "Iceland",
    "UA": "Ukraine",
    "BY": "Belarus",
    "GE": "Georgia",
    "AM": "Armenia",
    "AZ": "Azerbaijan",
    # 中东
    "IL": "Israel",
    "SA": "Saudi Arabia",
    "AE": "United Arab Emirates",
    "QA": "Qatar",
    "KW": "Kuwait",
    "BH": "Bahrain",
    "OM": "Oman",
    "JO": "Jordan",
    "LB": "Lebanon",
    "IR": "Iran",
    "IQ": "Iraq",
    "SY": "Syria",
    "PS": "Palestine",
    # 亚洲
    "MY": "Malaysia",
    "TH": "Thailand",
    "ID": "Indonesia",
    "PH": "Philippines",
    "VN": "Vietnam",
    "PK": "Pakistan",
    "BD": "Bangladesh",
    "LK": "Sri Lanka",
    "KZ": "Kazakhstan",
    "KG": "Kyrgyzstan",
    "BN": "Brunei",
    "UZ": "Uzbekistan",
    # 非洲
    "EG": "Egypt",
    "ZA": "South Africa",
    "NG": "Nigeria",
    "MA": "Morocco",
    "TN": "Tunisia",
    "KE": "Kenya",
    "GH": "Ghana",
    "ET": "Ethiopia",
    "UG": "Uganda",
    "SD": "Sudan",
    "LY": "Libya",
    # 美洲
    "AR": "Argentina",
    "CL": "Chile",
    "CO": "Colombia",
    "PE": "Peru",
    "VE": "Venezuela",
    "EC": "Ecuador",
    "BO": "Bolivia",
    "PY": "Paraguay",
    "UY": "Uruguay",
    "CR": "Costa Rica",
    "PA": "Panama",
    "GT": "Guatemala",
    "HN": "Honduras",
    "DO": "Dominican Republic",
    "CU": "Cuba",
    "PR": "Puerto Rico",
}

# 参数限制常量
MAX_TOP_N = 500
MIN_TOP_N = 1
DEFAULT_TOP_N = 20


def _get_csv_path():
    """获取 CSV 文件路径"""
    global _csv_path
    if _csv_path:
        return _csv_path
    
    possible_paths = [
        os.environ.get("QS_CSV_PATH", ""),
        os.path.join(os.path.dirname(__file__), DATA_FILE),
        os.path.join(os.path.dirname(__file__), "data", DATA_FILE),
        f"/code/{DATA_FILE}",
        DATA_FILE,
    ]
    
    for path in possible_paths:
        if path and os.path.exists(path):
            _csv_path = path
            logger.info(f"找到数据文件: {path}")
            return path
    
    logger.error("未找到 QS 排名数据文件")
    raise FileNotFoundError(f"未找到 {DATA_FILE} 文件，请设置 QS_CSV_PATH 环境变量")


def _load_data():
    """加载 CSV 数据"""
    global _df
    if _df is not None:
        return _df
    
    csv_path = _get_csv_path()
    _df = pd.read_csv(csv_path)
    
    logger.info(f"数据加载成功！共 {len(_df)} 条记录，"
                f"涵盖 {_df['Year'].nunique()} 个年份，"
                f"{_df['University'].nunique()} 所高校，"
                f"{_df['Country'].nunique()} 个国家/地区")
    return _df


def _to_json(data: Any, status: str = "success", message: str = None) -> str:
    """将数据转换为JSON格式"""
    result = {
        "status": status,
        "timestamp": datetime.now().isoformat(),
    }
    if message:
        result["message"] = message
    result["data"] = data
    return json.dumps(result, ensure_ascii=False, indent=2)


def _error_response(error_type: str, message: str, details: Dict = None) -> str:
    """生成标准化错误响应"""
    error_data = {
        "error_type": error_type,
        "message": message,
    }
    if details:
        error_data["details"] = details
    return _to_json(error_data, status="error")


def _get_country_iso(country: str) -> str:
    """获取国家的 ISO 代码"""
    if pd.isna(country):
        return None
    country = str(country).strip()
    # 先检查是否已经是 ISO 代码
    if country.upper() in ISO_TO_DISPLAY:
        return country.upper()
    # 从映射中查找
    return COUNTRY_TO_ISO.get(country, None)


def _get_country_display(country: str) -> str:
    """获取国家的标准显示名称"""
    if pd.isna(country):
        return None
    country = str(country).strip()
    # 如果是 ISO 代码，转换为显示名称
    if country.upper() in ISO_TO_DISPLAY:
        return ISO_TO_DISPLAY[country.upper()]
    # 否则尝试从映射中获取 ISO 再转回显示名称
    iso = COUNTRY_TO_ISO.get(country, None)
    if iso and iso in ISO_TO_DISPLAY:
        return ISO_TO_DISPLAY[iso]
    return country  # 保持原样


def _normalize_country_output(country: str) -> Dict[str, str]:
    """返回统一的国家信息结构"""
    if pd.isna(country):
        return {"iso_code": None, "name": None}
    country = str(country).strip()
    iso = _get_country_iso(country)
    display = _get_country_display(country)
    return {
        "iso_code": iso,
        "name": display if display else country
    }


def _filter_by_country(df: pd.DataFrame, country: str) -> pd.DataFrame:
    """按国家/地区筛选（支持 ISO 代码或全名，不区分大小写）"""
    c = country.lower().strip()
    c_upper = country.upper().strip()
    
    # 如果是 ISO 代码
    if c_upper in ISO_TO_DISPLAY:
        display_name = ISO_TO_DISPLAY[c_upper]
        # 匹配所有可能的原始名称
        possible_names = [k for k, v in COUNTRY_TO_ISO.items() if v == c_upper]
        possible_names.append(display_name)
        
        def match_iso(val):
            if pd.isna(val):
                return False
            val_str = str(val).strip()
            return val_str in possible_names or val_str.lower() in [n.lower() for n in possible_names]
        
        mask = df["Country"].apply(match_iso)
        return df[mask].copy()
    
    # 常用别名映射
    aliases = {
        "china": ["cn", "china (mainland)", "china(mainland)"],
        "cn": ["cn", "china (mainland)", "china(mainland)"],
        "usa": ["us", "united states"],
        "us": ["us", "united states"],
        "america": ["us", "united states"],
        "uk": ["gb", "united kingdom"],
        "gb": ["gb", "united kingdom"],
        "england": ["gb", "united kingdom"],
        "britain": ["gb", "united kingdom"],
        "hk": ["hk", "hong kong"],
        "hongkong": ["hk", "hong kong"],
        "hong kong": ["hk", "hong kong"],
        "singapore": ["sg", "singapore"],
        "sg": ["sg", "singapore"],
        "japan": ["jp", "japan"],
        "jp": ["jp", "japan"],
        "korea": ["kr", "korea", "south korea"],
        "kr": ["kr", "korea", "south korea"],
        "germany": ["de", "germany"],
        "de": ["de", "germany"],
        "france": ["fr", "france"],
        "fr": ["fr", "france"],
        "australia": ["au", "australia"],
        "au": ["au", "australia"],
        "canada": ["ca", "canada"],
        "ca": ["ca", "canada"],
        "switzerland": ["ch", "switzerland", "swiss"],
        "ch": ["ch", "switzerland", "swiss"],
    }
    
    search_terms = aliases.get(c, [c])
    
    def match_country(val):
        if pd.isna(val):
            return False
        val_lower = str(val).lower().strip()
        for term in search_terms:
            if val_lower == term or term in val_lower:
                if term in ["us", "united states"]:
                    if "australia" in val_lower:
                        continue
                return True
        return False
    
    mask = df["Country"].apply(match_country)
    return df[mask].copy()


def _get_available_years(df: pd.DataFrame) -> List[int]:
    """获取可用年份列表"""
    return sorted(df["Year"].dropna().unique().astype(int).tolist(), reverse=True)


def _validate_year(year: int, available_years: List[int]) -> Optional[str]:
    """验证年份参数，返回错误信息或 None"""
    if not isinstance(year, int):
        return f"年份必须是整数，收到: {type(year).__name__}"
    if year not in available_years:
        return f"无效的年份: {year}，可用年份: {available_years}"
    return None


def _validate_top_n(top_n: int, max_val: int = MAX_TOP_N) -> Optional[str]:
    """验证 top_n 参数，返回错误信息或 None"""
    if not isinstance(top_n, int):
        return f"top_n 必须是整数，收到: {type(top_n).__name__}"
    if top_n < MIN_TOP_N:
        return f"top_n 必须大于等于 {MIN_TOP_N}，收到: {top_n}"
    if top_n > max_val:
        return f"top_n 必须小于等于 {max_val}，收到: {top_n}"
    return None


def _get_score_columns(df: pd.DataFrame) -> List[tuple]:
    """获取可用的分数列"""
    indicator_cols = [
        (["Overall_Score", "Overall"], "overall_score", "Overall Score"),
        (["Academic Reputation"], "academic_reputation", "Academic Reputation"),
        (["Employer Reputation"], "employer_reputation", "Employer Reputation"),
        (["Faculty Student"], "faculty_student_ratio", "Faculty Student Ratio"),
        (["Citations per Faculty"], "citations_per_faculty", "Citations per Faculty"),
        (["International Faculty"], "international_faculty", "International Faculty"),
        (["International Students"], "international_students", "International Students"),
        (["International Research Network"], "international_research", "International Research Network"),
        (["Employment Outcomes"], "employment_outcomes", "Employment Outcomes"),
        (["Sustainability"], "sustainability", "Sustainability"),
    ]
    
    resolved_cols = []
    for candidates, key, label in indicator_cols:
        for c in candidates:
            if c in df.columns:
                resolved_cols.append((c, key, label))
                break
    
    return resolved_cols


def _get_completeness_note(years_with_rank: int, years_with_score: int, total_years: int) -> str:
    """生成数据完整性说明"""
    if total_years == 0:
        return "无数据"
    
    if years_with_rank == total_years and years_with_score == total_years:
        return "数据完整（所有年份均有排名和评分）"
    elif years_with_rank == total_years:
        return "排名数据完整，部分年份缺少评分"
    elif years_with_rank == 0:
        if years_with_score > 0:
            return "无排名数据，仅有评分数据（可能未进入排名）"
        return "数据不完整"
    elif years_with_rank < total_years:
        missing = total_years - years_with_rank
        return f"部分年份（{missing}年）缺少排名数据"
    return "数据部分完整"


# ========== MCP 工具定义 ==========

@mcp.tool()
async def search_university(
    keyword: str,
    year: Optional[int] = None
) -> str:
    """
    功能1: 大学搜索
    根据关键词搜索大学，查看其排名和各项指标
    
    参数:
        keyword: 大学名称关键词（支持模糊匹配，不区分大小写），如"MIT"、"Peking"
        year: 年份（可选，如2024、2025、2026），不指定则显示所有年份
    
    返回:
        匹配大学的排名信息和各项指标（JSON格式）
        - match_type: "exact"（精确匹配）或 "partial"（部分匹配）
        - data_completeness: 数据完整性标识
    
    注意:
        - keyword 请使用英文，如"MIT"、"Peking University"
        - 搜索可能返回多个结果，结果按匹配度排序（精确匹配优先）
        - 不同年份的数据完整性可能不同，请参考 data_completeness 字段
    """
    try:
        # 参数验证
        if not keyword or not isinstance(keyword, str):
            return _error_response(
                "INVALID_PARAMETER",
                "keyword 参数不能为空且必须是字符串",
                {"hint": "请提供有效的大学名称，如'MIT'、'Peking University'等"}
            )
        
        keyword = keyword.strip()
        if len(keyword) < 2:
            return _error_response(
                "INVALID_PARAMETER",
                "keyword 至少需要2个字符",
                {"received": keyword}
            )
        
        logger.info(f"开始大学搜索: keyword={keyword}, year={year}")
        
        df = _load_data()
        available_years = _get_available_years(df)
        
        # 年份验证
        if year is not None:
            year_error = _validate_year(year, available_years)
            if year_error:
                return _error_response(
                    "INVALID_YEAR",
                    year_error,
                    {"available_years": available_years}
                )
            df = df[df["Year"] == year].copy()
        
        # 模糊搜索
        kw = keyword.lower()
        mask = df["University"].str.lower().str.contains(kw, na=False)
        result_df = df[mask].copy()
        
        if len(result_df) == 0:
            return _error_response(
                "NOT_FOUND",
                f"未找到包含 '{keyword}' 的大学",
                {
                    "hint": "请检查大学名称拼写，或使用更短的关键词重试",
                    "searched_year": year,
                    "available_years": available_years
                }
            )
        
        # 获取分数列
        score_cols = _get_score_columns(result_df)
        
        universities = result_df["University"].unique().tolist()
        
        # 计算匹配度并排序（精确匹配 > 开头匹配 > 包含匹配）
        def match_score(uni_name):
            uni_lower = uni_name.lower()
            if uni_lower == kw:
                return 0  # 精确匹配
            elif uni_lower.startswith(kw):
                return 1  # 开头匹配
            else:
                return 2  # 包含匹配
        
        universities = sorted(universities, key=match_score)
        
        data = {
            "query": {
                "keyword": keyword,
                "year_filter": year,
                "available_years": available_years,
                "search_note": "结果按匹配度排序：精确匹配 > 名称开头匹配 > 包含匹配"
            },
            "summary": {
                "total_universities": len(universities),
                "total_records": len(result_df),
                "has_multiple_matches": len(universities) > 1
            },
            "universities": []
        }
        
        for uni in universities:
            uni_df = result_df[result_df["University"] == uni].sort_values("Year")
            country_raw = uni_df["Country"].iloc[0] if "Country" in uni_df.columns else None
            country_info = _normalize_country_output(country_raw)
            
            # 判断匹配类型
            uni_lower = uni.lower()
            if uni_lower == kw:
                match_type = "exact"
            elif uni_lower.startswith(kw):
                match_type = "prefix"
            else:
                match_type = "partial"
            
            uni_data = {
                "name": uni,
                "match_type": match_type,
                "country": country_info,
                "years_data": [],
                "data_completeness": {
                    "years_with_rank": 0,
                    "years_with_score": 0,
                    "total_years": 0
                }
            }
            
            years_with_rank = 0
            years_with_score = 0
            
            for _, row in uni_df.iterrows():
                rank_val = row["Rank"]
                has_rank = pd.notna(rank_val)
                rank = int(rank_val) if has_rank and float(rank_val) == int(rank_val) else None
                
                year_info = {
                    "year": int(row["Year"]) if pd.notna(row["Year"]) else None,
                    "rank": rank,
                    "has_rank": has_rank,
                    "scores": {}
                }
                
                has_any_score = False
                for col, key, label in score_cols:
                    if col in row and pd.notna(row[col]):
                        year_info["scores"][key] = {
                            "value": round(float(row[col]), 1),
                            "label": label
                        }
                        has_any_score = True
                
                year_info["has_scores"] = has_any_score
                
                # 统计数据完整性
                if has_rank:
                    years_with_rank += 1
                if has_any_score:
                    years_with_score += 1
                
                uni_data["years_data"].append(year_info)
            
            # 更新数据完整性统计
            total_years = len(uni_data["years_data"])
            uni_data["data_completeness"] = {
                "years_with_rank": years_with_rank,
                "years_with_score": years_with_score,
                "total_years": total_years,
                "completeness_note": _get_completeness_note(years_with_rank, years_with_score, total_years)
            }
            
            # 计算趋势
            ranks = [y["rank"] for y in uni_data["years_data"] if y["rank"] is not None]
            if len(ranks) >= 2:
                first, last = ranks[0], ranks[-1]
                diff = first - last
                uni_data["trend"] = {
                    "direction": "up" if diff > 0 else ("down" if diff < 0 else "stable"),
                    "change": abs(int(diff)),
                    "description": f"排名{'上升' if diff > 0 else ('下降' if diff < 0 else '持平')} {abs(int(diff))} 位" if diff != 0 else "排名持平"
                }
            
            data["universities"].append(uni_data)
        
        # 如果有多个匹配结果，添加提示
        if len(universities) > 1:
            data["disambiguation_note"] = f"找到 {len(universities)} 所名称相似的大学，请根据 match_type 和具体名称确认目标大学"
        
        logger.info(f"大学搜索完成: 找到 {len(universities)} 所大学")
        return _to_json(data, "success", f"找到 {len(universities)} 所匹配的大学")
        
    except Exception as e:
        logger.error(f"大学搜索失败: {str(e)}")
        return _error_response("INTERNAL_ERROR", f"大学搜索失败: {str(e)}")


@mcp.tool()
async def get_top_universities(
    year: int,
    country: Optional[str] = None,
    top_n: int = 10
) -> str:
    """
    功能2: 排名查询
    按年份和国家/地区查询排名前N的大学
    
    参数:
        year: 年份（必填，如2024、2025、2026）
        country: 国家/地区 ISO 代码或名称（可选，如 CN、US、GB、China、"United States"）
        top_n: 显示前N名（默认10，范围1-500）
    
    返回:
        排名前N的大学列表（JSON格式）
    """
    try:
        df = _load_data()
        available_years = _get_available_years(df)
        
        # 参数验证
        year_error = _validate_year(year, available_years)
        if year_error:
            return _error_response(
                "INVALID_YEAR",
                year_error,
                {"available_years": available_years}
            )
        
        top_n_error = _validate_top_n(top_n, MAX_TOP_N)
        if top_n_error:
            return _error_response(
                "INVALID_PARAMETER",
                top_n_error,
                {"valid_range": f"{MIN_TOP_N}-{MAX_TOP_N}"}
            )
        
        logger.info(f"开始排名查询: year={year}, country={country}, top_n={top_n}")
        
        # 年份筛选
        df = df[df["Year"] == year].copy()
        
        # 国家筛选
        country_info = None
        if country:
            df_filtered = _filter_by_country(df, country)
            if len(df_filtered) == 0:
                return _error_response(
                    "NOT_FOUND",
                    f"未找到国家/地区 '{country}' 的数据",
                    {
                        "hint": "请使用 ISO 代码（如 CN、US、GB）或完整国家名称",
                        "examples": ["CN", "US", "GB", "JP", "DE", "FR", "AU"]
                    }
                )
            df = df_filtered
            # 获取标准化的国家信息
            sample_country = df["Country"].iloc[0]
            country_info = _normalize_country_output(sample_country)
        
        # 获取有排名的并排序
        df_valid = df[df["Rank"].notna()].copy()
        total_ranked = len(df_valid)
        df_valid = df_valid.sort_values("Rank").head(top_n)
        
        if len(df_valid) == 0:
            return _error_response(
                "NO_DATA",
                f"{year} 年没有找到符合条件的排名数据",
                {
                    "year": year,
                    "country_filter": country,
                    "hint": "该年份或地区可能没有排名数据"
                }
            )
        
        # 获取分数列
        score_cols = _get_score_columns(df_valid)
        
        data = {
            "query": {
                "year": year,
                "country_filter": country_info,
                "top_n": top_n,
                "available_years": available_years
            },
            "summary": {
                "total_ranked_in_scope": total_ranked,
                "returned_count": len(df_valid)
            },
            "universities": []
        }
        
        for _, row in df_valid.iterrows():
            rank_val = row["Rank"]
            rank = int(rank_val) if pd.notna(rank_val) and float(rank_val) == int(rank_val) else None
            
            uni_country = _normalize_country_output(row["Country"])
            
            uni_info = {
                "rank": rank,
                "name": row["University"],
                "country": uni_country,
                "scores": {}
            }
            
            for col, key, label in score_cols:
                if col in row and pd.notna(row[col]):
                    uni_info["scores"][key] = {
                        "value": round(float(row[col]), 1),
                        "label": label
                    }
            
            data["universities"].append(uni_info)
        
        logger.info(f"排名查询完成: {year}年前{top_n}名")
        return _to_json(data, "success", f"返回 {len(df_valid)} 所大学的排名信息")
        
    except Exception as e:
        logger.error(f"排名查询失败: {str(e)}")
        return _error_response("INTERNAL_ERROR", f"排名查询失败: {str(e)}")


@mcp.tool()
async def get_country_stats(
    year: int,
    top_n: int = 20
) -> str:
    """
    功能3: 国家统计
    按国家/地区统计大学数量和分布
    
    参数:
        year: 年份（必填，如2024、2025、2026）
        top_n: 显示前N个国家（默认20，范围1-500）
    
    返回:
        各国家/地区大学数量统计（JSON格式）
    """
    try:
        df = _load_data()
        available_years = _get_available_years(df)
        
        # 参数验证
        year_error = _validate_year(year, available_years)
        if year_error:
            return _error_response(
                "INVALID_YEAR",
                year_error,
                {"available_years": available_years}
            )
        
        top_n_error = _validate_top_n(top_n, MAX_TOP_N)
        if top_n_error:
            return _error_response(
                "INVALID_PARAMETER",
                top_n_error,
                {"valid_range": f"{MIN_TOP_N}-{MAX_TOP_N}"}
            )
        
        logger.info(f"开始国家统计: year={year}, top_n={top_n}")
        
        df_year = df[df["Year"] == year].copy()
        
        # 标准化国家信息
        df_year["Country_Display"] = df_year["Country"].apply(_get_country_display)
        df_year["Country_ISO"] = df_year["Country"].apply(_get_country_iso)
        
        # 统计各国大学数量
        country_counts = df_year["Country_Display"].value_counts()
        
        # 统计有排名的大学数量
        df_ranked = df_year[df_year["Rank"].notna()]
        ranked_counts = df_ranked["Country_Display"].value_counts()
        
        total_all = len(df_year)
        total_ranked = len(df_ranked)
        total_countries = len(country_counts)
        
        data = {
            "query": {
                "year": year,
                "top_n": top_n,
                "available_years": available_years
            },
            "summary": {
                "total_universities": total_all,
                "total_ranked": total_ranked,
                "total_countries": total_countries,
                "description": f"{year}年共有{total_countries}个国家/地区的{total_all}所大学参与排名，其中{total_ranked}所获得排名"
            },
            "countries": []
        }
        
        for i, (country_display, count) in enumerate(country_counts.head(top_n).items(), 1):
            ranked = ranked_counts.get(country_display, 0)
            pct = round(count / total_all * 100, 2)
            
            # 获取该国家的 ISO 代码
            country_df = df_year[df_year["Country_Display"] == country_display]
            iso_code = country_df["Country_ISO"].iloc[0] if len(country_df) > 0 else None
            
            data["countries"].append({
                "rank": i,
                "country": {
                    "iso_code": iso_code,
                    "name": country_display
                },
                "statistics": {
                    "total": int(count),
                    "ranked": int(ranked),
                    "unranked": int(count - ranked),
                    "percentage_of_total": pct
                }
            })
        
        if total_countries > top_n:
            data["note"] = f"共 {total_countries} 个国家/地区，仅显示前 {top_n} 个"
        
        logger.info(f"国家统计完成: {year}年共{total_countries}个国家/地区")
        return _to_json(data, "success", f"统计了 {min(top_n, total_countries)} 个国家/地区的数据")
        
    except Exception as e:
        logger.error(f"国家统计失败: {str(e)}")
        return _error_response("INTERNAL_ERROR", f"国家统计失败: {str(e)}")


@mcp.tool()
async def get_country_scores(
    year: int,
    top_n: int = 15
) -> str:
    """
    功能4: 国家平均分对比
    按国家/地区统计平均分数
    
    参数:
        year: 年份（必填，如2024、2025、2026）
        top_n: 显示前N个国家（默认15，范围1-500）
    
    返回:
        各国家/地区平均分数对比（JSON格式）
    """
    try:
        df = _load_data()
        available_years = _get_available_years(df)
        
        # 参数验证
        year_error = _validate_year(year, available_years)
        if year_error:
            return _error_response(
                "INVALID_YEAR",
                year_error,
                {"available_years": available_years}
            )
        
        top_n_error = _validate_top_n(top_n, MAX_TOP_N)
        if top_n_error:
            return _error_response(
                "INVALID_PARAMETER",
                top_n_error,
                {"valid_range": f"{MIN_TOP_N}-{MAX_TOP_N}"}
            )
        
        logger.info(f"开始国家平均分对比: year={year}, top_n={top_n}")
        
        df_year = df[df["Year"] == year].copy()
        df_year = df_year[df_year["Rank"].notna()]
        df_year["Country_Display"] = df_year["Country"].apply(_get_country_display)
        df_year["Country_ISO"] = df_year["Country"].apply(_get_country_iso)
        
        # 确定分数列
        score_col = "Overall_Score" if "Overall_Score" in df_year.columns else "Overall"
        
        if score_col not in df_year.columns:
            return _error_response(
                "DATA_ERROR",
                "数据中没有找到分数列",
                {"available_columns": list(df_year.columns)}
            )
        
        # 过滤掉没有分数的记录
        df_scored = df_year[df_year[score_col].notna()]
        
        if len(df_scored) == 0:
            return _error_response(
                "NO_DATA",
                f"{year} 年没有有效的分数数据"
            )
        
        # 计算各国平均分数
        stats = df_scored.groupby("Country_Display").agg({
            score_col: ["mean", "max", "min", "count", "std"],
            "Rank": "min",
            "Country_ISO": "first"
        }).round(2)
        
        stats.columns = ["avg_score", "max_score", "min_score", "university_count", "std_dev", "best_rank", "iso_code"]
        stats = stats.sort_values("avg_score", ascending=False)
        
        total_countries = len(stats)
        
        data = {
            "query": {
                "year": year,
                "top_n": top_n,
                "available_years": available_years
            },
            "summary": {
                "total_countries_with_scores": total_countries,
                "score_column_used": score_col,
                "description": f"{year}年共有{total_countries}个国家/地区有分数数据"
            },
            "countries": []
        }
        
        for i, (country, row) in enumerate(stats.head(top_n).iterrows(), 1):
            data["countries"].append({
                "rank": i,
                "country": {
                    "iso_code": row["iso_code"],
                    "name": country
                },
                "scores": {
                    "average": float(row["avg_score"]),
                    "maximum": float(row["max_score"]),
                    "minimum": float(row["min_score"]),
                    "std_deviation": float(row["std_dev"]) if pd.notna(row["std_dev"]) else None
                },
                "statistics": {
                    "university_count": int(row["university_count"]),
                    "best_rank": int(row["best_rank"]) if pd.notna(row["best_rank"]) else None
                }
            })
        
        if total_countries > top_n:
            data["note"] = f"共 {total_countries} 个国家/地区有分数数据，仅显示前 {top_n} 个"
        
        logger.info(f"国家平均分对比完成: {year}年前{top_n}个国家")
        return _to_json(data, "success", f"返回 {min(top_n, total_countries)} 个国家/地区的分数统计")
        
    except Exception as e:
        logger.error(f"国家平均分对比失败: {str(e)}")
        return _error_response("INTERNAL_ERROR", f"国家平均分对比失败: {str(e)}")


@mcp.tool()
async def get_rank_changes(
    year: int,
    top_n: int = 20,
    direction: str = "rise"
) -> str:
    """
    功能5: 排名变化
    查看排名变化最大的大学（上升或下降）
    
    参数:
        year: 年份（必填，如2025、2026，会与前一年对比）
        top_n: 显示前N所大学（默认20，范围1-500）
        direction: 变化方向，"rise"表示上升，"fall"表示下降（默认"rise"）
    
    返回:
        排名变化最大的大学列表（JSON格式）
    """
    try:
        # 参数验证
        if direction not in ["rise", "fall"]:
            return _error_response(
                "INVALID_PARAMETER",
                f"无效的 direction 参数: '{direction}'",
                {"valid_options": ["rise", "fall"], "description": {"rise": "排名上升", "fall": "排名下降"}}
            )
        
        df = _load_data()
        available_years = _get_available_years(df)
        
        year_error = _validate_year(year, available_years)
        if year_error:
            return _error_response(
                "INVALID_YEAR",
                year_error,
                {"available_years": available_years}
            )
        
        top_n_error = _validate_top_n(top_n, MAX_TOP_N)
        if top_n_error:
            return _error_response(
                "INVALID_PARAMETER",
                top_n_error,
                {"valid_range": f"{MIN_TOP_N}-{MAX_TOP_N}"}
            )
        
        prev_year = year - 1
        if prev_year not in available_years:
            return _error_response(
                "NO_COMPARISON_DATA",
                f"{prev_year} 年没有数据，无法计算排名变化",
                {"available_years": available_years, "hint": f"请选择 {min(available_years) + 1} 至 {max(available_years)} 年份"}
            )
        
        logger.info(f"开始排名变化查询: year={year}, top_n={top_n}, direction={direction}")
        
        df_curr = df[df["Year"] == year][["University", "Country", "Rank"]].copy()
        df_prev = df[df["Year"] == prev_year][["University", "Rank"]].copy()
        
        df_curr = df_curr.rename(columns={"Rank": "Rank_Curr"})
        df_prev = df_prev.rename(columns={"Rank": "Rank_Prev"})
        
        merged = df_curr.merge(df_prev, on="University", how="inner")
        merged = merged[merged["Rank_Curr"].notna() & merged["Rank_Prev"].notna()]
        
        if len(merged) == 0:
            return _error_response(
                "NO_DATA",
                f"没有找到 {prev_year} 和 {year} 年都有排名的大学"
            )
        
        # 计算变化（正数表示上升）
        merged["Change"] = merged["Rank_Prev"] - merged["Rank_Curr"]
        
        if direction == "rise":
            result = merged[merged["Change"] > 0].nlargest(top_n, "Change")
            direction_cn = "上升"
        else:
            result = merged[merged["Change"] < 0].nsmallest(top_n, "Change")
            direction_cn = "下降"
        
        if len(result) == 0:
            return _error_response(
                "NO_DATA",
                f"没有找到排名{direction_cn}的大学",
                {"year": year, "compare_year": prev_year}
            )
        
        data = {
            "query": {
                "year": year,
                "compare_year": prev_year,
                "direction": direction,
                "direction_description": direction_cn,
                "top_n": top_n
            },
            "summary": {
                "total_found": len(result),
                "total_comparable": len(merged),
                "description": f"在 {len(merged)} 所可比较的大学中，找到 {len(result)} 所排名{direction_cn}的大学"
            },
            "universities": []
        }
        
        for i, (_, row) in enumerate(result.iterrows(), 1):
            change = int(row["Change"])
            country_info = _normalize_country_output(row["Country"])
            
            data["universities"].append({
                "rank_order": i,
                "name": row["University"],
                "country": country_info,
                "ranking": {
                    "previous_year": prev_year,
                    "previous_rank": int(row["Rank_Prev"]),
                    "current_year": year,
                    "current_rank": int(row["Rank_Curr"]),
                    "change": abs(change),
                    "change_display": f"+{change}" if change > 0 else str(change)
                }
            })
        
        logger.info(f"排名变化查询完成: {year}年排名{direction_cn}前{len(result)}所")
        return _to_json(data, "success", f"找到 {len(result)} 所排名{direction_cn}的大学")
        
    except Exception as e:
        logger.error(f"排名变化查询失败: {str(e)}")
        return _error_response("INTERNAL_ERROR", f"排名变化查询失败: {str(e)}")


@mcp.tool()
async def get_top100_distribution(
    year: int
) -> str:
    """
    功能6: Top 100 分布
    查看 Top 100 大学的国家分布
    
    参数:
        year: 年份（必填，如2024、2025、2026）
    
    返回:
        Top 100 大学的国家分布统计（JSON格式）
    """
    try:
        df = _load_data()
        available_years = _get_available_years(df)
        
        year_error = _validate_year(year, available_years)
        if year_error:
            return _error_response(
                "INVALID_YEAR",
                year_error,
                {"available_years": available_years}
            )
        
        logger.info(f"开始 Top 100 分布查询: year={year}")
        
        df_year = df[(df["Year"] == year) & (df["Rank"].notna()) & (df["Rank"] <= 100)].copy()
        
        if len(df_year) == 0:
            return _error_response(
                "NO_DATA",
                f"{year} 年没有 Top 100 排名数据",
                {"available_years": available_years}
            )
        
        df_year["Country_Display"] = df_year["Country"].apply(_get_country_display)
        df_year["Country_ISO"] = df_year["Country"].apply(_get_country_iso)
        
        country_counts = df_year["Country_Display"].value_counts()
        total_countries = len(country_counts)
        
        data = {
            "query": {
                "year": year,
                "scope": "Top 100",
                "available_years": available_years
            },
            "summary": {
                "total_universities": len(df_year),
                "total_countries": total_countries,
                "description": f"{year}年 Top 100 大学来自 {total_countries} 个国家/地区"
            },
            "distribution": []
        }
        
        for country_display, count in country_counts.items():
            country_df = df_year[df_year["Country_Display"] == country_display]
            iso_code = country_df["Country_ISO"].iloc[0] if len(country_df) > 0 else None
            best_rank = int(country_df["Rank"].min())
            
            pct = round(count / len(df_year) * 100, 1)
            data["distribution"].append({
                "country": {
                    "iso_code": iso_code,
                    "name": country_display
                },
                "statistics": {
                    "count": int(count),
                    "percentage": pct,
                    "best_rank": best_rank
                }
            })
        
        logger.info(f"Top 100 分布查询完成: {year}年涉及{total_countries}个国家/地区")
        return _to_json(data, "success", f"Top 100 大学分布在 {total_countries} 个国家/地区")
        
    except Exception as e:
        logger.error(f"Top 100 分布查询失败: {str(e)}")
        return _error_response("INTERNAL_ERROR", f"Top 100 分布查询失败: {str(e)}")


# @mcp.tool()
# async def get_summary(
#     year: int
# ) -> str:
#     """
#     功能7: 综合统计
#     获取指定年份的综合统计摘要，包括基本信息、Top 10、国家分布等
    
#     参数:
#         year: 年份（必填，如2024、2025、2026）
    
#     返回:
#         综合统计摘要（JSON格式）
#     """
#     try:
#         df = _load_data()
#         available_years = _get_available_years(df)
        
#         year_error = _validate_year(year, available_years)
#         if year_error:
#             return _error_response(
#                 "INVALID_YEAR",
#                 year_error,
#                 {"available_years": available_years}
#             )
        
#         logger.info(f"开始综合统计: year={year}")
        
#         df_year = df[df["Year"] == year].copy()
#         df_year["Country_Display"] = df_year["Country"].apply(_get_country_display)
#         df_year["Country_ISO"] = df_year["Country"].apply(_get_country_iso)
        
#         # 基本统计
#         total_unis = len(df_year)
#         ranked_unis = int(df_year["Rank"].notna().sum())
#         countries = int(df_year["Country_Display"].nunique())
        
#         # 分数统计
#         score_col = "Overall_Score" if "Overall_Score" in df_year.columns else "Overall"
#         df_scored = df_year[df_year[score_col].notna()] if score_col in df_year.columns else pd.DataFrame()
        
#         data = {
#             "query": {
#                 "year": year,
#                 "available_years": available_years
#             },
#             "basic_info": {
#                 "total_universities": total_unis,
#                 "ranked_universities": ranked_unis,
#                 "unranked_universities": total_unis - ranked_unis,
#                 "countries_covered": countries,
#                 "description": f"{year}年共有来自{countries}个国家/地区的{total_unis}所大学参与排名"
#             },
#             "top_10": [],
#             "top_5_countries": [],
#             "score_stats": None,
#             "comparison_with_prev_year": None
#         }
        
#         # Top 10 大学
#         top10 = df_year[df_year["Rank"].notna()].nsmallest(10, "Rank")
#         for _, row in top10.iterrows():
#             rank = int(row["Rank"])
#             country_info = _normalize_country_output(row["Country"])
#             data["top_10"].append({
#                 "rank": rank,
#                 "name": row["University"],
#                 "country": country_info
#             })
        
#         # Top 5 国家
#         country_counts = df_year["Country_Display"].value_counts().head(5)
#         for i, (country, count) in enumerate(country_counts.items(), 1):
#             pct = round(count / total_unis * 100, 1)
#             country_df = df_year[df_year["Country_Display"] == country]
#             iso_code = country_df["Country_ISO"].iloc[0] if len(country_df) > 0 else None
            
#             data["top_5_countries"].append({
#                 "rank": i,
#                 "country": {
#                     "iso_code": iso_code,
#                     "name": country
#                 },
#                 "count": int(count),
#                 "percentage": pct
#             })
        
#         # 分数分布
#         if not df_scored.empty and score_col in df_scored.columns:
#             data["score_stats"] = {
#                 "score_column": score_col,
#                 "average": round(float(df_scored[score_col].mean()), 1),
#                 "median": round(float(df_scored[score_col].median()), 1),
#                 "maximum": round(float(df_scored[score_col].max()), 1),
#                 "minimum": round(float(df_scored[score_col].min()), 1),
#                 "std_deviation": round(float(df_scored[score_col].std()), 1)
#             }
        
#         # 与去年对比
#         prev_year = year - 1
#         if prev_year in available_years:
#             df_prev = df[df["Year"] == prev_year]
#             prev_total = len(df_prev)
#             prev_ranked = int(df_prev["Rank"].notna().sum())
#             data["comparison_with_prev_year"] = {
#                 "prev_year": prev_year,
#                 "universities_change": total_unis - prev_total,
#                 "ranked_change": ranked_unis - prev_ranked,
#                 "description": f"相比{prev_year}年，参与大学{'增加' if total_unis > prev_total else '减少'}{abs(total_unis - prev_total)}所"
#             }
        
#         logger.info(f"综合统计完成: {year}年")
#         return _to_json(data, "success", f"{year}年综合统计数据")
        
#     except Exception as e:
#         logger.error(f"综合统计失败: {str(e)}")
#         return _error_response("INTERNAL_ERROR", f"综合统计失败: {str(e)}")


@mcp.tool()
async def list_available_years() -> str:
    """
    功能7: 查看可用年份
    列出数据中所有可用的年份及其数据统计
    
    参数:
        无（此函数不需要任何参数）
    
    返回:
        可用年份列表及每年的数据统计（JSON格式）
    
    说明:
        - 此函数无需传入任何参数，直接调用即可
        - 不同年份的数据完整性可能存在差异
        - 建议使用最新年份（如2026年）获取最完整的数据
    """
    try:
        logger.info("查询可用年份")
        
        df = _load_data()
        available_years = _get_available_years(df)
        
        # 每年的统计信息
        year_stats = []
        for year in available_years:
            df_year = df[df["Year"] == year]
            total = len(df_year)
            ranked = int(df_year["Rank"].notna().sum())
            countries = int(df_year["Country"].nunique())
            
            year_stats.append({
                "year": year,
                "total_universities": total,
                "ranked_universities": ranked,
                "unranked_universities": total - ranked,
                "countries_count": countries,
                "ranking_coverage": f"{round(ranked/total*100, 1)}%" if total > 0 else "0%"
            })
        
        # 添加数据说明
        latest = available_years[0] if available_years else None
        
        data = {
            "available_years": available_years,
            "count": len(available_years),
            "latest_year": latest,
            "earliest_year": available_years[-1] if available_years else None,
            "recommended_year": latest,
            "year_statistics": year_stats,
            "note": "不同年份的排名覆盖率可能不同，建议使用最新年份获取最完整数据"
        }
        
        logger.info(f"可用年份查询完成: {available_years}")
        return _to_json(data, "success", f"共有 {len(available_years)} 个可用年份，推荐使用 {latest} 年数据")
        
    except Exception as e:
        logger.error(f"查询可用年份失败: {str(e)}")
        return _error_response("INTERNAL_ERROR", f"查询可用年份失败: {str(e)}")


@mcp.tool()
async def list_countries(
    year: Optional[int] = None
) -> str:
    """
    功能8: 查看国家列表
    列出数据中所有可用的国家/地区（包含 ISO 代码）
    
    参数:
        year: 年份（可选，不指定则显示所有年份的国家）
    
    返回:
        可用国家/地区列表（JSON格式，包含 ISO 代码和标准名称）
    """
    try:
        logger.info(f"查询国家列表: year={year}")
        
        df = _load_data()
        available_years = _get_available_years(df)
        
        if year is not None:
            year_error = _validate_year(year, available_years)
            if year_error:
                return _error_response(
                    "INVALID_YEAR",
                    year_error,
                    {"available_years": available_years}
                )
            df = df[df["Year"] == year]
        
        # 获取唯一国家并标准化（使用标准化名称去重）
        countries_raw = df["Country"].dropna().unique()
        
        # 使用字典按标准化名称去重
        countries_map = {}  # key: 标准化名称, value: {iso_code, name, original_variants}
        
        for c in countries_raw:
            iso = _get_country_iso(c)
            display = _get_country_display(c)
            name = display if display else c
            
            if name in countries_map:
                # 已存在，记录原始变体名称
                if c != name and c not in countries_map[name]["original_variants"]:
                    countries_map[name]["original_variants"].append(c)
            else:
                # 新增
                countries_map[name] = {
                    "iso_code": iso,
                    "name": name,
                    "original_variants": [c] if c != name else []
                }
        
        # 转换为列表并排序
        countries_list = []
        for name in sorted(countries_map.keys()):
            item = countries_map[name]
            entry = {
                "iso_code": item["iso_code"],
                "name": item["name"]
            }
            # 只有当存在原始变体时才添加该字段
            if item["original_variants"]:
                entry["original_variants"] = item["original_variants"]
            countries_list.append(entry)
        
        data = {
            "query": {
                "year_filter": year,
                "available_years": available_years
            },
            "summary": {
                "count": len(countries_list),
                "description": f"{'所有年份' if year is None else f'{year}年'}共有 {len(countries_list)} 个国家/地区"
            },
            "countries": countries_list
        }
        
        logger.info(f"国家列表查询完成: 共{len(countries_list)}个国家/地区")
        return _to_json(data, "success", f"共 {len(countries_list)} 个国家/地区")
        
    except Exception as e:
        logger.error(f"查询国家列表失败: {str(e)}")
        return _error_response("INTERNAL_ERROR", f"查询国家列表失败: {str(e)}")


# 兼容性处理：将被装饰为 MCP 工具的对象暴露出原始可 await 的函数
for _name in [
    'search_university', 'get_top_universities', 'get_country_stats',
    'get_country_scores', 'get_rank_changes', 'get_top100_distribution',
    'get_summary', 'list_available_years', 'list_countries'
]:
    _obj = globals().get(_name)
    if _obj is not None and hasattr(_obj, 'fn'):
        globals()[_name] = getattr(_obj, 'fn')


# ========== 运行服务器 ==========

def main():
    """启动 MCP 服务器"""
    logger.info("=" * 60)
    logger.info("🎓 QS 世界大学排名 MCP 服务器启动")
    logger.info("=" * 60)
    
    # 预加载数据
    try:
        _load_data()
    except Exception as e:
        logger.warning(f"预加载数据失败: {e}，将在首次请求时加载")
    
    # 获取端口配置
    port = int(os.environ.get("MCP_PORT", os.environ.get("PORT", "9000")))
    
    logger.info(f"[SSE模式] 启动 MCP 服务器")
    logger.info(f"[SSE模式] 监听地址: http://localhost:{port}/sse")
    logger.info(f"[SSE模式] 网络地址: http://0.0.0.0:{port}/sse")
    logger.info(f"[SSE模式] 使用 Ctrl+C 停止服务器")
    logger.info("-" * 60)
    
    # 启动 MCP 服务器
    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=port,
        path="/sse",
        log_level="info",
    )


if __name__ == "__main__":
    main()
