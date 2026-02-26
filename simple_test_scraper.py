#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简化版LeetCode爬虫测试
"""

import requests
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_simple_api():
    """测试简化版API调用"""
    graphql_url = "https://leetcode.cn/graphql"
    
    # 最简化的查询
    query = """
    query getProblems($limit: Int) {
        problemsetQuestionList(limit: $limit) {
            questions {
                frontendQuestionId
                title
                titleSlug
                difficulty
                acRate
            }
        }
    }
    """
    
    variables = {"limit": 5}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Content-Type': 'application/json',
        'Referer': 'https://leetcode.cn/problemset/all/',
        'Origin': 'https://leetcode.cn',
    }
    
    try:
        logger.info("发送API请求...")
        response = requests.post(
            graphql_url,
            json={"query": query, "variables": variables},
            headers=headers,
            timeout=10
        )
        
        logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            logger.info("响应数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            if 'errors' in data:
                logger.error("GraphQL错误:")
                for error in data['errors']:
                    logger.error(f"  {error}")
                return False
            else:
                questions = data['data']['problemsetQuestionList']['questions']
                logger.info(f"成功获取 {len(questions)} 道题目")
                for i, q in enumerate(questions, 1):
                    print(f"{i}. {q['frontendQuestionId']}. {q['title']} ({q['difficulty']}) - 通过率: {q['acRate']:.1f}%")
                return True
        else:
            logger.error(f"HTTP错误: {response.status_code}")
            logger.error(f"响应内容: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"请求异常: {e}")
        return False

if __name__ == "__main__":
    logger.info("开始测试LeetCode API...")
    success = test_simple_api()
    if success:
        logger.info("✅ API测试成功!")
    else:
        logger.error("❌ API测试失败!")