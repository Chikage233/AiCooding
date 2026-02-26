#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试详细内容获取问题
"""

import requests
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_detailed_content(slug="two-sum"):
    """测试获取题目详细内容"""
    graphql_url = "https://leetcode.cn/graphql"
    
    # 原始的详细查询
    original_query = """
    query questionData($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
            questionId
            questionFrontendId
            boundTopicId
            title
            titleSlug
            content
            translatedTitle
            translatedContent
            difficulty
            stats
            hints
            similarQuestions
            sampleTestCase
            exampleTestcases
            metaData
            apacId
            article
            solution {
                id
                canSeeDetail
                paidOnly
                hasVideoSolution
                paidOnlyVideo
            }
            topicTags {
                name
                slug
                translatedName
            }
            companyTagStats
            likes
            dislikes
            isLiked
            isFavor
            frequency
            progress
        }
    }
    """
    
    # 简化版查询（只保留必要字段）
    simple_query = """
    query questionData($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
            questionId
            questionFrontendId
            title
            titleSlug
            content
            translatedTitle
            translatedContent
            difficulty
            stats
            topicTags {
                name
                slug
                translatedName
            }
        }
    }
    """
    
    variables = {"titleSlug": slug}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Content-Type': 'application/json',
        'Referer': 'https://leetcode.cn/problemset/all/',
        'Origin': 'https://leetcode.cn',
    }
    
    # 测试原始查询
    logger.info("测试原始详细查询...")
    try:
        response = requests.post(
            graphql_url,
            json={"query": original_query, "variables": variables},
            headers=headers,
            timeout=10
        )
        
        logger.info(f"原始查询状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'errors' in data:
                logger.error("原始查询错误:")
                for error in data['errors']:
                    logger.error(f"  {error}")
            else:
                logger.info("原始查询成功")
                print("原始查询返回的数据结构:")
                print(json.dumps(data['data']['question'].keys(), indent=2, ensure_ascii=False))
        else:
            logger.error(f"原始查询HTTP错误: {response.status_code}")
            logger.error(f"响应内容: {response.text[:200]}")
    except Exception as e:
        logger.error(f"原始查询异常: {e}")
    
    # 测试简化查询
    logger.info("\n测试简化查询...")
    try:
        response = requests.post(
            graphql_url,
            json={"query": simple_query, "variables": variables},
            headers=headers,
            timeout=10
        )
        
        logger.info(f"简化查询状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            if 'errors' in data:
                logger.error("简化查询错误:")
                for error in data['errors']:
                    logger.error(f"  {error}")
            else:
                logger.info("简化查询成功")
                print("简化查询返回的数据:")
                question_data = data['data']['question']
                print(f"题目ID: {question_data.get('questionFrontendId')}")
                print(f"标题: {question_data.get('translatedTitle', question_data.get('title'))}")
                print(f"难度: {question_data.get('difficulty')}")
                print(f"内容长度: {len(question_data.get('translatedContent', question_data.get('content', '')))}")
                print(f"标签数量: {len(question_data.get('topicTags', []))}")
        else:
            logger.error(f"简化查询HTTP错误: {response.status_code}")
            logger.error(f"响应内容: {response.text[:200]}")
    except Exception as e:
        logger.error(f"简化查询异常: {e}")

if __name__ == "__main__":
    logger.info("开始调试详细内容获取...")
    test_detailed_content("two-sum")