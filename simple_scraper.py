#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基础版LeetCode爬虫 - 只获取题目列表信息
"""

import requests
import json
import logging
from django.db import transaction
from api.models import LeetCodeProblem, ProblemTag

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleLeetCodeScraper:
    """简化版LeetCode爬虫"""
    
    def __init__(self):
        self.graphql_url = "https://leetcode.cn/graphql"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode.cn/problemset/all/',
            'Origin': 'https://leetcode.cn',
        })
    
    def get_problems_list(self, limit: int = 200) -> list:
        """获取题目列表"""
        query = """
        query getProblems($limit: Int) {
            problemsetQuestionList(limit: $limit) {
                questions {
                    frontendQuestionId
                    title
                    titleSlug
                    difficulty
                    acRate
                    paidOnly
                    status
                    topicTags {
                        name
                        slug
                        nameTranslated
                    }
                }
            }
        }
        """
        
        variables = {"limit": limit}
        
        try:
            response = self.session.post(
                self.graphql_url,
                json={"query": query, "variables": variables}
            )
            response.raise_for_status()
            
            data = response.json()
            if 'errors' in data:
                logger.error(f"GraphQL错误: {data['errors']}")
                return []
            
            problems = data['data']['problemsetQuestionList']['questions']
            logger.info(f"成功获取 {len(problems)} 道题目")
            return problems
            
        except Exception as e:
            logger.error(f"获取题目列表失败: {e}")
            return []
    
    def save_problem_to_db(self, problem_data: dict) -> bool:
        """保存题目到数据库"""
        try:
            with transaction.atomic():
                # 准备题目数据
                problem_dict = {
                    'problem_id': int(problem_data['frontendQuestionId']),
                    'title': problem_data.get('titleCn') or problem_data['title'],
                    'title_slug': problem_data['titleSlug'],
                    'difficulty': problem_data['difficulty'].lower(),
                    'is_premium': problem_data.get('paidOnly', False),
                    'content': '',  # 暂时不获取详细内容
                    'acceptance_rate': float(problem_data.get('acRate', 0)),
                    'submission_count': 0,  # 暂时设为0
                    'accepted_count': 0,    # 暂时设为0
                    'tags': [tag['slug'] for tag in problem_data.get('topicTags', [])]
                }
                
                # 更新或创建题目
                problem_obj, created = LeetCodeProblem.objects.update_or_create(
                    problem_id=problem_dict['problem_id'],
                    defaults=problem_dict
                )
                
                # 保存标签
                for tag_data in problem_data.get('topicTags', []):
                    tag_obj, _ = ProblemTag.objects.get_or_create(
                        slug=tag_data['slug'],
                        defaults={
                            'name': tag_data.get('nameTranslated') or tag_data['name']
                        }
                    )
                
                action = "创建" if created else "更新"
                logger.info(f"{action}题目: {problem_obj.problem_id}. {problem_obj.title}")
                return True
                
        except Exception as e:
            logger.error(f"保存题目到数据库失败: {e}")
            return False
    
    def scrape_problems(self, limit: int = 200) -> dict:
        """爬取题目"""
        logger.info(f"开始爬取LeetCode题目，目标数量: {limit}")
        
        # 获取题目列表
        problems_list = self.get_problems_list(limit)
        if not problems_list:
            logger.error("无法获取题目列表")
            return {"success": False, "message": "无法获取题目列表"}
        
        success_count = 0
        fail_count = 0
        
        # 保存题目到数据库
        for i, problem in enumerate(problems_list, 1):
            logger.info(f"处理第 {i}/{len(problems_list)} 道题目: {problem['title']}")
            
            if self.save_problem_to_db(problem):
                success_count += 1
            else:
                fail_count += 1
        
        result = {
            "success": True,
            "total": len(problems_list),
            "success_count": success_count,
            "fail_count": fail_count,
            "message": f"爬取完成！成功: {success_count}, 失败: {fail_count}"
        }
        
        logger.info(result["message"])
        return result

def run_simple_scraper(limit: int = 200):
    """运行简化爬虫"""
    scraper = SimpleLeetCodeScraper()
    return scraper.scrape_problems(limit=limit)

if __name__ == "__main__":
    # 测试运行
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AiCooding.settings')
    django.setup()
    
    result = run_simple_scraper(limit=10)
    print(json.dumps(result, ensure_ascii=False, indent=2))