#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QS 世界大学排名 MCP 服务器测试脚本

适配改进版 API，验证:
1. 参数验证
2. 错误响应格式
3. 统一国家信息结构 (iso_code + name)
4. 一致的数据结构
"""

import asyncio
import json


def format_country(country_info):
    """格式化国家信息显示"""
    if isinstance(country_info, dict):
        iso = country_info.get('iso_code', '??')
        name = country_info.get('name', 'Unknown')
        return f"{iso or '??'}: {name}"
    return str(country_info)


async def test_mcp_tools():
    """测试 MCP 工具函数"""
    # 导入 MCP 服务器模块
    from mcp_server import (
        search_university,
        get_top_universities,
        get_country_stats,
        get_country_scores,
        get_rank_changes,
        get_top100_distribution,
        get_summary,
        list_available_years,
        list_countries
    )
    
    print("=" * 60)
    print("🧪 开始测试 QS 世界大学排名 MCP 服务器 (改进版)")
    print("=" * 60)
    
    # 测试 1: 查看可用年份
    print("\n📅 测试 1: 查看可用年份")
    print("-" * 40)
    try:
        result = await list_available_years()
        data = json.loads(result)
        if data.get('status') == 'success':
            years_data = data.get('data', {})
            print(f"可用年份: {years_data.get('available_years', [])}")
            print(f"最新年份: {years_data.get('latest_year')}")
            print(f"最早年份: {years_data.get('earliest_year')}")
            for stat in years_data.get('year_statistics', []):
                print(f"  {stat['year']}年: {stat['total_universities']}所大学, {stat['ranked_universities']}所有排名")
            print("✅ 查看可用年份测试通过")
        else:
            print(f"❌ 返回状态异常: {data.get('status')}")
    except Exception as e:
        print(f"❌ 查看可用年份测试失败: {e}")
    
    # 测试 2: 大学搜索
    print("\n🏫 测试 2: 大学搜索")
    print("-" * 40)
    try:
        result = await search_university(keyword="MIT", year=2026)
        data = json.loads(result)
        if data.get('status') == 'success':
            search_data = data.get('data', {})
            query = search_data.get('query', {})
            summary = search_data.get('summary', {})
            print(f"关键词: {query.get('keyword')}")
            print(f"找到大学数: {summary.get('total_universities')}")
            for uni in search_data.get('universities', [])[:3]:
                print(f"  🎓 {uni.get('name')}")
                print(f"     国家: {format_country(uni.get('country'))}")
                for year_info in uni.get('years_data', []):
                    print(f"     {year_info.get('year')}年排名: {year_info.get('rank')}")
            print("✅ 大学搜索测试通过")
        else:
            print(f"❌ 返回状态异常: {data}")
    except Exception as e:
        print(f"❌ 大学搜索测试失败: {e}")
    
    # 测试 2b: 大学搜索 - 错误参数验证
    print("\n🔴 测试 2b: 大学搜索 - 无效参数")
    print("-" * 40)
    try:
        result = await search_university(keyword="X", year=2026)  # 关键词太短
        data = json.loads(result)
        if data.get('status') == 'error':
            err = data.get('data', {})
            print(f"错误类型: {err.get('error_type')}")
            print(f"错误信息: {err.get('message')}")
            print("✅ 参数验证测试通过")
        else:
            print(f"⚠️ 应该返回错误，但返回了: {data.get('status')}")
    except Exception as e:
        print(f"❌ 参数验证测试失败: {e}")
    
    # 测试 3: 排名查询（全球）
    print("\n🌍 测试 3: 全球排名查询")
    print("-" * 40)
    try:
        result = await get_top_universities(year=2026, top_n=10)
        data = json.loads(result)
        if data.get('status') == 'success':
            top_data = data.get('data', {})
            query = top_data.get('query', {})
            summary = top_data.get('summary', {})
            print(f"年份: {query.get('year')}")
            print(f"返回数量: {summary.get('returned_count')}")
            print(f"Top 10 大学:")
            for uni in top_data.get('universities', []):
                country = format_country(uni.get('country'))
                print(f"  {uni.get('rank'):>3}. {uni.get('name')[:40]:<40} ({country})")
            print("✅ 全球排名查询测试通过")
        else:
            print(f"❌ 返回状态异常: {data.get('status')}")
    except Exception as e:
        print(f"❌ 全球排名查询测试失败: {e}")
    
    # 测试 4: 排名查询（中国）
    print("\n🇨🇳 测试 4: 中国大学排名查询 (使用 ISO 代码 CN)")
    print("-" * 40)
    try:
        result = await get_top_universities(year=2026, country="CN", top_n=10)
        data = json.loads(result)
        if data.get('status') == 'success':
            top_data = data.get('data', {})
            query = top_data.get('query', {})
            summary = top_data.get('summary', {})
            print(f"年份: {query.get('year')}")
            print(f"筛选国家: {format_country(query.get('country_filter'))}")
            print(f"返回数量: {summary.get('returned_count')}")
            for uni in top_data.get('universities', []):
                overall = uni.get('scores', {}).get('overall_score', {}).get('value', 'N/A')
                print(f"  {uni.get('rank'):>3}. {uni.get('name')[:35]:<35} 分数: {overall}")
            print("✅ 中国大学排名查询测试通过")
        else:
            print(f"❌ 返回状态异常: {data.get('status')}")
    except Exception as e:
        print(f"❌ 中国大学排名查询测试失败: {e}")
    
    # 测试 5: 国家统计
    print("\n📊 测试 5: 国家统计")
    print("-" * 40)
    try:
        result = await get_country_stats(year=2026, top_n=10)
        data = json.loads(result)
        if data.get('status') == 'success':
            stats_data = data.get('data', {})
            query = stats_data.get('query', {})
            summary = stats_data.get('summary', {})
            print(f"年份: {query.get('year')}")
            print(f"总大学数: {summary.get('total_universities')}")
            print(f"有排名大学: {summary.get('total_ranked')}")
            print(f"国家总数: {summary.get('total_countries')}")
            print("Top 10 国家:")
            for item in stats_data.get('countries', []):
                country = format_country(item.get('country'))
                stats = item.get('statistics', {})
                print(f"  {item.get('rank'):>2}. {country:<25} {stats.get('total'):>4} 所 ({stats.get('percentage_of_total')}%)")
            print("✅ 国家统计测试通过")
        else:
            print(f"❌ 返回状态异常: {data.get('status')}")
    except Exception as e:
        print(f"❌ 国家统计测试失败: {e}")
    
    # 测试 6: 国家平均分对比
    print("\n📈 测试 6: 国家平均分对比")
    print("-" * 40)
    try:
        result = await get_country_scores(year=2026, top_n=10)
        data = json.loads(result)
        if data.get('status') == 'success':
            score_data = data.get('data', {})
            query = score_data.get('query', {})
            summary = score_data.get('summary', {})
            print(f"年份: {query.get('year')}")
            print(f"使用分数列: {summary.get('score_column_used')}")
            print("Top 10 国家（按平均分）:")
            for item in score_data.get('countries', []):
                country = format_country(item.get('country'))
                scores = item.get('scores', {})
                stats = item.get('statistics', {})
                print(f"  {item.get('rank'):>2}. {country:<22} "
                      f"平均: {scores.get('average'):>5.1f}  "
                      f"最高: {scores.get('maximum'):>5.1f}  "
                      f"大学数: {stats.get('university_count')}")
            print("✅ 国家平均分对比测试通过")
        else:
            print(f"❌ 返回状态异常: {data.get('status')}")
    except Exception as e:
        print(f"❌ 国家平均分对比测试失败: {e}")
    
    # 测试 7: 排名变化
    print("\n📉 测试 7: 排名变化（上升）")
    print("-" * 40)
    try:
        result = await get_rank_changes(year=2026, top_n=10, direction="rise")
        data = json.loads(result)
        if data.get('status') == 'success':
            change_data = data.get('data', {})
            query = change_data.get('query', {})
            summary = change_data.get('summary', {})
            print(f"对比年份: {query.get('compare_year')} → {query.get('year')}")
            print(f"变化方向: {query.get('direction')} ({query.get('direction_description')})")
            print(f"找到 {summary.get('total_found')} 所大学:")
            for uni in change_data.get('universities', [])[:10]:
                ranking = uni.get('ranking', {})
                print(f"  {uni.get('name')[:35]:<35} "
                      f"{ranking.get('previous_rank')} → {ranking.get('current_rank')} "
                      f"({ranking.get('change_display')})")
            print("✅ 排名变化测试通过")
        else:
            print(f"❌ 返回状态异常: {data.get('status')}")
    except Exception as e:
        print(f"❌ 排名变化测试失败: {e}")

    # 测试 7b: 排名变化 - 无效参数
    print("\n🔴 测试 7b: 排名变化 - 无效 direction")
    print("-" * 40)
    try:
        result = await get_rank_changes(year=2026, top_n=10, direction="invalid")
        data = json.loads(result)
        if data.get('status') == 'error':
            err = data.get('data', {})
            print(f"错误类型: {err.get('error_type')}")
            print(f"错误信息: {err.get('message')}")
            print(f"有效选项: {err.get('details', {}).get('valid_options')}")
            print("✅ 参数验证测试通过")
        else:
            print(f"⚠️ 应该返回错误，但返回了: {data.get('status')}")
    except Exception as e:
        print(f"❌ 参数验证测试失败: {e}")
    
    # 测试 8: Top 100 分布
    print("\n🏆 测试 8: Top 100 分布")
    print("-" * 40)
    try:
        result = await get_top100_distribution(year=2026)
        data = json.loads(result)
        if data.get('status') == 'success':
            dist_data = data.get('data', {})
            query = dist_data.get('query', {})
            summary = dist_data.get('summary', {})
            print(f"年份: {query.get('year')}")
            print(f"涉及国家数: {summary.get('total_countries')}")
            print("分布情况:")
            for item in dist_data.get('distribution', [])[:10]:
                country = format_country(item.get('country'))
                stats = item.get('statistics', {})
                bar_len = int(stats.get('count', 0) / 2)
                bar = "█" * bar_len
                print(f"  {country:<25} {bar} {stats.get('count')} ({stats.get('percentage')}%)")
            print("✅ Top 100 分布测试通过")
        else:
            print(f"❌ 返回状态异常: {data.get('status')}")
    except Exception as e:
        print(f"❌ Top 100 分布测试失败: {e}")
    
    # 测试 9: 综合统计
    print("\n📋 测试 9: 综合统计")
    print("-" * 40)
    try:
        result = await get_summary(year=2026)
        data = json.loads(result)
        if data.get('status') == 'success':
            summary_data = data.get('data', {})
            basic = summary_data.get('basic_info', {})
            print(f"年份: {summary_data.get('query', {}).get('year')}")
            print(f"参评大学: {basic.get('total_universities')}")
            print(f"获得排名: {basic.get('ranked_universities')}")
            print(f"覆盖国家: {basic.get('countries_covered')}")
            print("\nTop 10 大学:")
            for uni in summary_data.get('top_10', []):
                country = format_country(uni.get('country'))
                print(f"  {uni.get('rank'):>2}. {uni.get('name')[:40]} ({country})")
            score_stats = summary_data.get('score_stats')
            if score_stats:
                print(f"\n分数统计:")
                print(f"  平均分: {score_stats.get('average')}")
                print(f"  中位数: {score_stats.get('median')}")
                print(f"  最高分: {score_stats.get('maximum')}")
            comparison = summary_data.get('comparison_with_prev_year')
            if comparison:
                print(f"\n与上年对比: {comparison.get('description')}")
            print("✅ 综合统计测试通过")
        else:
            print(f"❌ 返回状态异常: {data.get('status')}")
    except Exception as e:
        print(f"❌ 综合统计测试失败: {e}")

    # 测试 9b: 综合统计 - 无效年份
    print("\n🔴 测试 9b: 综合统计 - 无效年份")
    print("-" * 40)
    try:
        result = await get_summary(year=1999)
        data = json.loads(result)
        if data.get('status') == 'error':
            err = data.get('data', {})
            print(f"错误类型: {err.get('error_type')}")
            print(f"错误信息: {err.get('message')}")
            print(f"可用年份: {err.get('details', {}).get('available_years')}")
            print("✅ 年份验证测试通过")
        else:
            print(f"⚠️ 应该返回错误，但返回了: {data.get('status')}")
    except Exception as e:
        print(f"❌ 年份验证测试失败: {e}")
    
    # 测试 10: 查看国家列表
    print("\n🌐 测试 10: 查看国家列表")
    print("-" * 40)
    try:
        result = await list_countries(year=2026)
        data = json.loads(result)
        if data.get('status') == 'success':
            countries_data = data.get('data', {})
            query = countries_data.get('query', {})
            summary = countries_data.get('summary', {})
            print(f"年份筛选: {query.get('year_filter')}")
            print(f"国家总数: {summary.get('count')}")
            print("部分国家（带 ISO 代码的）:")
            countries = countries_data.get('countries', [])
            with_iso = [c for c in countries if c.get('iso_code')][:10]
            for c in with_iso:
                print(f"  [{c.get('iso_code')}] {c.get('name')}")
            print("✅ 查看国家列表测试通过")
        else:
            print(f"❌ 返回状态异常: {data.get('status')}")
    except Exception as e:
        print(f"❌ 查看国家列表测试失败: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 所有测试完成！")
    print("=" * 60)


def main():
    """主函数"""
    asyncio.run(test_mcp_tools())


if __name__ == "__main__":
    main()
