#!/usr/bin/env python
"""
qs_stats.py — QS 大学排名统计汇总
=================================

提供各种统计分析功能，包括国家/地区分布、平均分数对比、排名变化等。

使用方法:
    python qs_stats.py <命令> [选项]

命令:
    country     各国/地区大学数量统计
    score       各国/地区平均分数对比
    change      排名变化最大的大学
    top100      Top 100 大学国家分布
    summary     综合统计摘要

示例:
    python qs_stats.py country -y 2026              # 2026年各国大学数量
    python qs_stats.py country -y 2026 -n 20        # 显示前20个国家
    python qs_stats.py score -y 2026 -n 15          # 各国平均分数前15
    python qs_stats.py change -y 2026 --rise        # 排名上升最多的大学
    python qs_stats.py change -y 2026 --fall        # 排名下降最多的大学
    python qs_stats.py top100 -y 2026               # Top100国家分布
    python qs_stats.py summary -y 2026              # 综合统计
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


def normalize_country(country: str) -> str:
    """标准化国家名称（处理不同表述）"""
    country = str(country).strip()
    
    # 常见的国家名称映射
    mapping = {
        "US": "United States",
        "United States of America": "United States",
        "UK": "United Kingdom",
        "CN": "China (Mainland)",
        "China": "China (Mainland)",
        "HK": "Hong Kong SAR",
        "Hong Kong SAR, China": "Hong Kong SAR",
        "SG": "Singapore",
        "JP": "Japan",
        "KR": "South Korea",
        "Republic of Korea": "South Korea",
        "South Korea": "South Korea",
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
        "Russian Federation": "Russia",
        "TW": "Taiwan",
        "IN": "India",
        "BR": "Brazil",
        "MX": "Mexico",
        "Türkiye": "Turkey",
        "TR": "Turkey",
        "MO": "Macau SAR",
        "Macao SAR, China": "Macau SAR",
    }
    
    return mapping.get(country, country)


def stats_country(df: pd.DataFrame, year: int, top_n: int = 20):
    """各国/地区大学数量统计"""
    df_year = df[df["Year"] == year].copy()
    
    if df_year.empty:
        print(f"\n{year} 年没有数据。")
        return
    
    # 标准化国家名称
    df_year["Country_Normalized"] = df_year["Country"].apply(normalize_country)
    
    # 统计各国大学数量
    country_counts = df_year["Country_Normalized"].value_counts()
    
    # 统计有排名的大学数量
    df_ranked = df_year[df_year["Rank"].notna()]
    ranked_counts = df_ranked["Country_Normalized"].value_counts()
    
    print(f"\n📊 {year} 年 QS 世界大学排名 - 各国/地区大学数量统计\n")
    print("=" * 70)
    print(f"{'排序':^4} {'国家/地区':<25} {'总数':^8} {'有排名':^8} {'占比':^10}")
    print("-" * 70)
    
    total_all = len(df_year)
    total_ranked = len(df_ranked)
    
    for i, (country, count) in enumerate(country_counts.head(top_n).items(), 1):
        ranked = ranked_counts.get(country, 0)
        pct = count / total_all * 100
        print(f"{i:^4} {country:<25} {count:^8} {ranked:^8} {pct:^9.1f}%")
    
    print("=" * 70)
    print(f"{'':^4} {'合计':<25} {total_all:^8} {total_ranked:^8} {'100.0%':^10}")
    
    if len(country_counts) > top_n:
        print(f"\n（共 {len(country_counts)} 个国家/地区，仅显示前 {top_n} 个）")


def stats_score(df: pd.DataFrame, year: int, top_n: int = 15):
    """各国/地区平均分数对比"""
    df_year = df[df["Year"] == year].copy()
    
    if df_year.empty:
        print(f"\n{year} 年没有数据。")
        return
    
    # 只考虑有排名的大学
    df_year = df_year[df_year["Rank"].notna()]
    df_year["Country_Normalized"] = df_year["Country"].apply(normalize_country)
    
    # 计算各国平均分数
    score_col = "Overall_Score" if "Overall_Score" in df_year.columns else "Overall"
    
    stats = df_year.groupby("Country_Normalized").agg({
        score_col: ["mean", "max", "min", "count"],
        "Rank": "min"  # 最好排名
    }).round(1)
    
    stats.columns = ["平均分", "最高分", "最低分", "大学数", "最好排名"]
    stats = stats.sort_values("平均分", ascending=False)
    
    print(f"\n📊 {year} 年 QS 世界大学排名 - 各国/地区平均分数对比\n")
    print("=" * 80)
    print(f"{'排序':^4} {'国家/地区':<22} {'平均分':^8} {'最高分':^8} {'最低分':^8} {'大学数':^6} {'最好排名':^8}")
    print("-" * 80)
    
    for i, (country, row) in enumerate(stats.head(top_n).iterrows(), 1):
        best_rank = int(row["最好排名"]) if pd.notna(row["最好排名"]) else "-"
        print(f"{i:^4} {country:<22} {row['平均分']:^8.1f} {row['最高分']:^8.1f} {row['最低分']:^8.1f} {int(row['大学数']):^6} {str(best_rank):^8}")
    
    print("=" * 80)
    
    if len(stats) > top_n:
        print(f"\n（共 {len(stats)} 个国家/地区，仅显示前 {top_n} 个）")


def stats_change(df: pd.DataFrame, year: int, top_n: int = 20, rise: bool = True):
    """排名变化最大的大学"""
    prev_year = year - 1
    
    df_curr = df[df["Year"] == year][["University", "Country", "Rank"]].copy()
    df_prev = df[df["Year"] == prev_year][["University", "Rank"]].copy()
    
    if df_curr.empty:
        print(f"\n{year} 年没有数据。")
        return
    
    if df_prev.empty:
        print(f"\n{prev_year} 年没有数据，无法计算变化。")
        return
    
    # 合并数据
    df_curr = df_curr.rename(columns={"Rank": "Rank_Curr"})
    df_prev = df_prev.rename(columns={"Rank": "Rank_Prev"})
    
    merged = df_curr.merge(df_prev, on="University", how="inner")
    merged = merged[merged["Rank_Curr"].notna() & merged["Rank_Prev"].notna()]
    
    # 计算变化（正数表示上升，负数表示下降）
    merged["Change"] = merged["Rank_Prev"] - merged["Rank_Curr"]
    
    if rise:
        # 排名上升最多（Change 最大）
        result = merged.nlargest(top_n, "Change")
        result = result[result["Change"] > 0]
        direction = "上升"
        emoji = "📈"
    else:
        # 排名下降最多（Change 最小）
        result = merged.nsmallest(top_n, "Change")
        result = result[result["Change"] < 0]
        direction = "下降"
        emoji = "📉"
    
    print(f"\n{emoji} {year} 年 QS 排名{direction}最多的大学 (对比 {prev_year} 年)\n")
    print("=" * 90)
    print(f"{'序号':^4} {'大学名称':<40} {'国家':^12} {f'{prev_year}':^6} {f'{year}':^6} {'变化':^8}")
    print("-" * 90)
    
    for i, (_, row) in enumerate(result.iterrows(), 1):
        uni = row["University"]
        if len(uni) > 38:
            uni = uni[:36] + "..."
        country = normalize_country(row["Country"])
        if len(country) > 10:
            country = country[:10] + ".."
        prev_rank = int(row["Rank_Prev"])
        curr_rank = int(row["Rank_Curr"])
        change = int(row["Change"])
        change_str = f"+{change}" if change > 0 else str(change)
        print(f"{i:^4} {uni:<40} {country:^12} {prev_rank:^6} {curr_rank:^6} {change_str:^8}")
    
    print("=" * 90)
    print(f"共 {len(result)} 所大学")


def stats_top100(df: pd.DataFrame, year: int):
    """Top 100 大学国家分布"""
    df_year = df[(df["Year"] == year) & (df["Rank"].notna()) & (df["Rank"] <= 100)].copy()
    
    if df_year.empty:
        print(f"\n{year} 年没有 Top 100 数据。")
        return
    
    df_year["Country_Normalized"] = df_year["Country"].apply(normalize_country)
    
    country_counts = df_year["Country_Normalized"].value_counts()
    
    print(f"\n🏆 {year} 年 QS 世界大学排名 Top 100 国家分布\n")
    print("=" * 60)
    
    # 绘制简易柱状图
    max_count = country_counts.max()
    bar_width = 30
    
    for country, count in country_counts.items():
        bar_len = int(count / max_count * bar_width)
        bar = "█" * bar_len
        pct = count / 100 * 100
        print(f"{country:<20} {bar:<30} {count:>2} ({pct:>5.1f}%)")
    
    print("=" * 60)
    print(f"Top 100 共涉及 {len(country_counts)} 个国家/地区")


def stats_summary(df: pd.DataFrame, year: int):
    """综合统计摘要"""
    df_year = df[df["Year"] == year].copy()
    
    if df_year.empty:
        print(f"\n{year} 年没有数据。")
        return
    
    df_year["Country_Normalized"] = df_year["Country"].apply(normalize_country)
    
    # 基本统计
    total_unis = len(df_year)
    ranked_unis = df_year["Rank"].notna().sum()
    countries = df_year["Country_Normalized"].nunique()
    
    # 分数统计
    score_col = "Overall_Score" if "Overall_Score" in df_year.columns else "Overall"
    df_scored = df_year[df_year[score_col].notna()]
    
    print(f"\n📋 {year} 年 QS 世界大学排名 - 综合统计摘要\n")
    print("=" * 70)
    
    # 基本信息
    print("\n📌 基本信息")
    print("-" * 70)
    print(f"   参评大学总数：{total_unis}")
    print(f"   获得排名大学：{ranked_unis}")
    print(f"   覆盖国家/地区：{countries}")
    
    # Top 10 大学
    top10 = df_year[df_year["Rank"].notna()].nsmallest(10, "Rank")
    print("\n🥇 Top 10 大学")
    print("-" * 70)
    for _, row in top10.iterrows():
        rank = int(row["Rank"])
        uni = row["University"]
        if len(uni) > 45:
            uni = uni[:43] + "..."
        country = normalize_country(row["Country"])
        print(f"   {rank:>2}. {uni:<45} ({country})")
    
    # Top 5 国家
    print("\n🌍 大学数量 Top 5 国家/地区")
    print("-" * 70)
    country_counts = df_year["Country_Normalized"].value_counts().head(5)
    for i, (country, count) in enumerate(country_counts.items(), 1):
        pct = count / total_unis * 100
        print(f"   {i}. {country:<25} {count:>4} 所 ({pct:.1f}%)")
    
    # 分数分布
    if not df_scored.empty:
        print("\n📊 分数分布")
        print("-" * 70)
        avg_score = df_scored[score_col].mean()
        max_score = df_scored[score_col].max()
        min_score = df_scored[score_col].min()
        median_score = df_scored[score_col].median()
        
        print(f"   平均分：{avg_score:.1f}")
        print(f"   中位数：{median_score:.1f}")
        print(f"   最高分：{max_score:.1f}")
        print(f"   最低分：{min_score:.1f}")
        
        # 分数段分布
        bins = [0, 30, 50, 70, 90, 100]
        labels = ["0-30", "30-50", "50-70", "70-90", "90-100"]
        score_bins = pd.cut(df_scored[score_col], bins=bins, labels=labels, right=True)
        bin_counts = score_bins.value_counts().sort_index()
        
        print("\n   分数段分布：")
        for label in labels:
            count = bin_counts.get(label, 0)
            bar_len = int(count / 50)  # 每50所大学一个方块
            bar = "▓" * bar_len if bar_len > 0 else "▏"
            print(f"   {label:>8}: {bar} {count}")
    
    # 与去年对比
    prev_year = year - 1
    df_prev = df[df["Year"] == prev_year]
    if not df_prev.empty:
        prev_total = len(df_prev)
        prev_ranked = df_prev["Rank"].notna().sum()
        
        print(f"\n📈 与 {prev_year} 年对比")
        print("-" * 70)
        
        unis_change = total_unis - prev_total
        ranked_change = ranked_unis - prev_ranked
        
        unis_sign = "+" if unis_change > 0 else ""
        ranked_sign = "+" if ranked_change > 0 else ""
        
        print(f"   参评大学变化：{unis_sign}{unis_change}")
        print(f"   获得排名变化：{ranked_sign}{ranked_change}")
    
    print("\n" + "=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="QS 世界大学排名统计汇总",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest="command", help="统计命令")
    
    # country 命令
    p_country = subparsers.add_parser("country", help="各国/地区大学数量统计")
    p_country.add_argument("-y", "--year", type=int, required=True, choices=[2024, 2025, 2026])
    p_country.add_argument("-n", "--top", type=int, default=20, help="显示前 N 个国家 (默认 20)")
    
    # score 命令
    p_score = subparsers.add_parser("score", help="各国/地区平均分数对比")
    p_score.add_argument("-y", "--year", type=int, required=True, choices=[2024, 2025, 2026])
    p_score.add_argument("-n", "--top", type=int, default=15, help="显示前 N 个国家 (默认 15)")
    
    # change 命令
    p_change = subparsers.add_parser("change", help="排名变化最大的大学")
    p_change.add_argument("-y", "--year", type=int, required=True, choices=[2024, 2025, 2026])
    p_change.add_argument("-n", "--top", type=int, default=20, help="显示前 N 所大学 (默认 20)")
    p_change.add_argument("--rise", action="store_true", help="显示排名上升的大学 (默认)")
    p_change.add_argument("--fall", action="store_true", help="显示排名下降的大学")
    
    # top100 命令
    p_top100 = subparsers.add_parser("top100", help="Top 100 大学国家分布")
    p_top100.add_argument("-y", "--year", type=int, required=True, choices=[2024, 2025, 2026])
    
    # summary 命令
    p_summary = subparsers.add_parser("summary", help="综合统计摘要")
    p_summary.add_argument("-y", "--year", type=int, required=True, choices=[2024, 2025, 2026])
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    df = load_data()
    
    if args.command == "country":
        stats_country(df, args.year, args.top)
    elif args.command == "score":
        stats_score(df, args.year, args.top)
    elif args.command == "change":
        rise = not args.fall  # 默认显示上升，除非指定 --fall
        stats_change(df, args.year, args.top, rise)
    elif args.command == "top100":
        stats_top100(df, args.year)
    elif args.command == "summary":
        stats_summary(df, args.year)


if __name__ == "__main__":
    main()
