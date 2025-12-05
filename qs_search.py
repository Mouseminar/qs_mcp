#!/usr/bin/env python
"""
qs_search.py — QS 大学排名搜索助手
==================================

使用方法:
    python qs_search.py <关键词>

示例:
    python qs_search.py MIT
    python qs_search.py "Peking University"
    python qs_search.py 清华
    python qs_search.py oxford
"""

import sys
from pathlib import Path
import pandas as pd

DATA_FILE = "qs_cleaned.csv"


def load_data() -> pd.DataFrame:
    if not Path(DATA_FILE).exists():
        print(f"错误: 找不到数据文件 {DATA_FILE}")
        print("请先运行 scripts/clean_data.py 生成清洗后的数据。")
        sys.exit(1)
    return pd.read_csv(DATA_FILE)


def search_university(df: pd.DataFrame, keyword: str) -> pd.DataFrame:
    """根据关键词模糊搜索大学名称（不区分大小写）"""
    kw = keyword.lower()
    mask = df["University"].str.lower().str.contains(kw, na=False)
    return df[mask].copy()


def display_results(df: pd.DataFrame, keyword: str):
    if df.empty:
        print(f"\n未找到包含 \"{keyword}\" 的大学。")
        return

    # Group by university and show each year
    universities = df["University"].unique()
    print(f"\n找到 {len(universities)} 所大学，共 {len(df)} 条年度记录：\n")

    # Determine columns to show (try both possible column names)
    indicator_cols = [
        (["Overall_Score", "Overall"], "Overall"),
        (["Academic Reputation", "AR_Score"], "学术声誉"),
        (["Employer Reputation", "ER_Score"], "雇主声誉"),
        (["Faculty Student", "FSR_Score"], "师生比"),
        (["Citations per Faculty", "CPF_Score"], "论文引用"),
        (["International Faculty", "IFR_Score"], "国际教师"),
        (["International Students", "ISR_Score"], "国际学生"),
        (["International Research Network", "IRN_Score"], "国际研究"),
        (["Employment Outcomes", "EO_Score"], "就业成果"),
        (["Sustainability", "SUS_Score"], "可持续"),
    ]

    # Resolve actual column names present in DataFrame
    resolved_cols = []
    for candidates, label in indicator_cols:
        for c in candidates:
            if c in df.columns:
                resolved_cols.append((c, label))
                break

    for uni in universities:
        uni_df = df[df["University"] == uni].sort_values("Year")
        country = uni_df["Country"].iloc[0] if "Country" in uni_df.columns else "N/A"
        print("=" * 80)
        print(f"🎓 {uni}")
        print(f"   国家/地区: {country}")
        print("-" * 80)
        print(f"{'年份':^6} {'排名':^8}", end="")
        for col, label in resolved_cols:
            print(f" {label:^8}", end="")
        print()
        print("-" * 80)

        for _, row in uni_df.iterrows():
            year = int(row["Year"]) if pd.notna(row["Year"]) else "?"
            rank = row["Rank"] if pd.notna(row["Rank"]) else "-"
            if isinstance(rank, float) and rank == int(rank):
                rank = int(rank)
            print(f"{year:^6} {str(rank):^8}", end="")
            for col, _ in resolved_cols:
                val = row[col]
                if pd.notna(val):
                    print(f" {val:^8.1f}", end="")
                else:
                    print(f" {'-':^8}", end="")
            print()

        # Show trend if multiple years
        if len(uni_df) > 1:
            ranks = uni_df["Rank"].dropna().tolist()
            if len(ranks) >= 2:
                first, last = ranks[0], ranks[-1]
                diff = first - last  # positive means improved (lower rank number is better)
                if diff > 0:
                    trend = f"📈 排名上升 {int(diff)} 位"
                elif diff < 0:
                    trend = f"📉 排名下降 {int(-diff)} 位"
                else:
                    trend = "➡️ 排名持平"
                print(f"\n   趋势: {trend}")
        print()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    keyword = " ".join(sys.argv[1:])
    df = load_data()
    results = search_university(df, keyword)
    display_results(results, keyword)


if __name__ == "__main__":
    main()
