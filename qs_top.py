#!/usr/bin/env python
"""
qs_top.py — QS 大学排名 Top N 查询
===================================

按国家/地区和年份查询排名前 N 的高校。

使用方法:
    python qs_top.py --year <年份> [--country <国家>] [--top N]

参数:
    --year, -y     年份（必填，可选 2024, 2025, 2026）
    --country, -c  国家/地区代码或名称（可选，如 CN, US, UK, China, "United States"）
    --top, -n      显示前 N 名（默认 10）

示例:
    python qs_top.py -y 2026 -n 20                    # 2026年全球前20
    python qs_top.py -y 2025 -c CN                    # 2025年中国高校排名
    python qs_top.py -y 2024 -c US -n 30              # 2024年美国前30
    python qs_top.py -y 2026 -c "United Kingdom"      # 2026年英国高校
"""

import argparse
import sys
from pathlib import Path
from typing import Optional
import pandas as pd

DATA_FILE = "qs_cleaned.csv"


def load_data() -> pd.DataFrame:
    if not Path(DATA_FILE).exists():
        print(f"错误: 找不到数据文件 {DATA_FILE}")
        print("请先运行 scripts/clean_data.py 生成清洗后的数据。")
        sys.exit(1)
    return pd.read_csv(DATA_FILE)

def filter_by_year(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """筛选指定年份的数据"""
    return df[df["Year"] == year].copy()


def filter_by_country(df: pd.DataFrame, country: str) -> pd.DataFrame:
    """按国家/地区筛选（支持代码或全名，不区分大小写）
    
    支持多种匹配方式:
    - 精确匹配代码 (CN, US, UK)
    - 包含匹配 (China -> China (Mainland), Hong Kong SAR, China)
    - 常用别名映射 (China -> CN, China (Mainland))
    """
    c = country.lower().strip()
    
    # 常用别名映射 - 使用更精确的匹配词
    aliases = {
        "china": ["cn", "china (mainland)", "china(mainland)"],
        "cn": ["cn", "china (mainland)", "china(mainland)"],
        "usa": ["us", "united states"],
        "us": ["us", "united states"],
        "america": ["us", "united states"],
        "uk": ["uk", "united kingdom"],
        "england": ["uk", "united kingdom"],
        "britain": ["uk", "united kingdom"],
        "hk": ["hk", "hong kong"],
        "hongkong": ["hk", "hong kong"],
        "hong kong": ["hk", "hong kong"],
        "singapore": ["sg", "singapore"],
        "sg": ["sg", "singapore"],
        "japan": ["jp", "japan"],
        "jp": ["jp", "japan"],
        "korea": ["kr", "korea"],
        "kr": ["kr", "korea"],
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
    
    # 获取搜索关键词列表
    search_terms = aliases.get(c, [c])
    
    def match_country(val):
        if pd.isna(val):
            return False
        val_lower = str(val).lower().strip()
        for term in search_terms:
            # 精确匹配（代码如 US, CN）或者值包含搜索词
            if val_lower == term or term in val_lower:
                # 排除误匹配：如果搜索 "us"/"united states"，不应匹配 "australia"
                if term in ["us", "united states"]:
                    if "australia" in val_lower:
                        continue
                return True
        return False
    
    mask = df["Country"].apply(match_country)
    return df[mask].copy()


def get_top_n(df: pd.DataFrame, n: int) -> pd.DataFrame:
    """获取排名前 N 的高校（按 Rank 排序，忽略无排名的）"""
    df_valid = df[df["Rank"].notna()].copy()
    df_valid = df_valid.sort_values("Rank")
    return df_valid.head(n)


def display_results(df: pd.DataFrame, year: int, country: Optional[str], n: int):
    if df.empty:
        location = f" ({country})" if country else ""
        print(f"\n{year} 年{location}没有找到符合条件的高校。")
        return

    location_str = f" - {country}" if country else " - 全球"
    print(f"\n📊 {year} 年 QS 世界大学排名{location_str} Top {len(df)}\n")
    print("=" * 100)

    # Determine columns to show
    indicator_cols = [
        (["Overall_Score", "Overall"], "Overall"),
        (["Academic Reputation"], "学术声誉"),
        (["Employer Reputation"], "雇主声誉"),
        (["Citations per Faculty"], "论文引用"),
        (["Sustainability"], "可持续"),
    ]

    # Resolve actual column names
    resolved_cols = []
    for candidates, label in indicator_cols:
        for c in candidates:
            if c in df.columns:
                resolved_cols.append((c, label))
                break

    # Print header
    print(f"{'排名':^6} {'大学名称':<45} {'国家':^8}", end="")
    for _, label in resolved_cols:
        print(f" {label:^8}", end="")
    print()
    print("-" * 100)

    # Print rows
    for _, row in df.iterrows():
        rank = row["Rank"]
        if pd.notna(rank) and rank == int(rank):
            rank = int(rank)
        uni = row["University"]
        if len(uni) > 42:
            uni = uni[:40] + "..."
        country_code = row["Country"] if pd.notna(row["Country"]) else "-"

        print(f"{str(rank):^6} {uni:<45} {country_code:^8}", end="")
        for col, _ in resolved_cols:
            val = row[col]
            if pd.notna(val):
                print(f" {val:^8.1f}", end="")
            else:
                print(f" {'-':^8}", end="")
        print()

    print("=" * 100)
    print(f"共 {len(df)} 所高校")


def list_countries(df: pd.DataFrame):
    """列出所有可用的国家/地区代码"""
    countries = df["Country"].dropna().unique()
    countries = sorted(countries)
    print("\n可用的国家/地区代码:")
    print("-" * 40)
    for i, c in enumerate(countries, 1):
        print(f"  {c:<20}", end="")
        if i % 4 == 0:
            print()
    print()


def main():
    parser = argparse.ArgumentParser(
        description="QS 世界大学排名 Top N 查询",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument("-y", "--year", type=int, required=True,
                        choices=[2024, 2025, 2026],
                        help="查询年份 (2024, 2025, 2026)")
    parser.add_argument("-c", "--country", type=str, default=None,
                        help="国家/地区代码或名称 (如 CN, US, UK, China)")
    parser.add_argument("-n", "--top", type=int, default=10,
                        help="显示前 N 名 (默认 10)")
    parser.add_argument("--list-countries", action="store_true",
                        help="列出所有可用的国家/地区代码")

    args = parser.parse_args()

    df = load_data()

    if args.list_countries:
        list_countries(df)
        return

    # Filter by year
    df = filter_by_year(df, args.year)

    # Filter by country if specified
    if args.country:
        df = filter_by_country(df, args.country)

    # Get top N
    df = get_top_n(df, args.top)

    # Display results
    display_results(df, args.year, args.country, args.top)


if __name__ == "__main__":
    main()
