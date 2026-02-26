# tools/leetcode_scraper.py
import requests
import json
import time
import random
import logging
from typing import List, Dict, Optional
from django.db import transaction
from api.models import LeetCodeProblem, ProblemTag

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('leetcode_scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LeetCodeScraper:
    """LeetCode题目爬虫类"""

    def __init__(self):
        self.base_url = "https://leetcode.cn"
        self.graphql_url = "https://leetcode.cn/graphql"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Content-Type': 'application/json',
            'Referer': 'https://leetcode.cn/problemset/all/',
            'Origin': 'https://leetcode.cn',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
        })


    def get_problems_list(self, limit: int = 200) -> List[Dict]:
        """获取LeetCode题目列表"""
        # 使用已验证的工作查询
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

        variables = {
            "categorySlug": "",
            "limit": limit
        }

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

    def get_problem_detail(self, title_slug: str) -> Optional[Dict]:
        """获取单个题目的详细信息"""
        query = """
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

        try:
            response = self.session.post(
                self.graphql_url,
                json={
                    "query": query,
                    "variables": {"titleSlug": title_slug}
                }
            )
            response.raise_for_status()

            data = response.json()
            if 'errors' in data:
                logger.warning(f"获取题目详情失败 {title_slug}: {data['errors']}")
                return None

            return data['data']['question']

        except Exception as e:
            logger.warning(f"获取题目详情异常 {title_slug}: {e}")
            return None

    def parse_stats(self, stats_str: str) -> Dict:
        """解析统计数据"""
        try:
            stats = json.loads(stats_str)
            return {
                'total_accepted': int(stats.get('totalAccepted', 0)),
                'total_submission': int(stats.get('totalSubmission', 0)),
                'ac_rate': float(stats.get('acRate', 0))
            }
        except:
            return {
                'total_accepted': 0,
                'total_submission': 0,
                'ac_rate': 0.0
            }

    def save_problem_to_db(self, problem_data: Dict) -> bool:
        """将题目数据保存到数据库"""
        try:
            with transaction.atomic():
                # 解析统计数据
                stats_info = self.parse_stats(problem_data.get('stats', '{}'))

                # 准备题目数据
                problem_dict = {
                    'problem_id': int(problem_data['questionFrontendId']),
                    'title': problem_data.get('translatedTitle') or problem_data['title'],
                    'title_slug': problem_data['titleSlug'],
                    'difficulty': problem_data['difficulty'].lower(),
                    'is_premium': problem_data.get('paidOnly', False),
                    'content': problem_data.get('translatedContent') or problem_data.get('content', ''),
                    'acceptance_rate': stats_info['ac_rate'],
                    'submission_count': stats_info['total_submission'],
                    'accepted_count': stats_info['total_accepted'],
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
                            'name': tag_data.get('translatedName') or tag_data['name']
                        }
                    )

                action = "创建" if created else "更新"
                logger.info(f"{action}题目: {problem_obj.problem_id}. {problem_obj.title}")
                return True

        except Exception as e:
            logger.error(f"保存题目到数据库失败: {e}")
            return False

    def scrape_problems(self, limit: int = 200, delay_range: tuple = (1, 3)) -> Dict:
        """爬取LeetCode题目并保存到数据库"""
        logger.info(f"开始爬取LeetCode题目，目标数量: {limit}")

        # 获取题目列表
        problems_list = self.get_problems_list(limit)
        if not problems_list:
            logger.error("无法获取题目列表")
            return {"success": False, "message": "无法获取题目列表"}

        success_count = 0
        fail_count = 0

        # 逐个获取题目详情并保存
        for i, problem in enumerate(problems_list, 1):
            logger.info(f"处理第 {i}/{len(problems_list)} 道题目: {problem['title']}")

            # 获取详细信息
            detail = self.get_problem_detail(problem['titleSlug'])
            if detail:
                if self.save_problem_to_db(detail):
                    success_count += 1
                else:
                    fail_count += 1
            else:
                fail_count += 1

            # 随机延迟，避免请求过于频繁
            if i < len(problems_list):  # 最后一个不需要延迟
                delay = random.uniform(*delay_range)
                time.sleep(delay)

        result = {
            "success": True,
            "total": len(problems_list),
            "success_count": success_count,
            "fail_count": fail_count,
            "message": f"爬取完成！成功: {success_count}, 失败: {fail_count}"
        }

        logger.info(result["message"])
        return result

def run_scraper(limit: int = 200):
    """运行爬虫的便捷函数"""
    scraper = LeetCodeScraper()
    return scraper.scrape_problems(limit=limit)

if __name__ == "__main__":
    # 测试运行
    result = run_scraper(limit=5)  # 先测试5道题目
    print(json.dumps(result, ensure_ascii=False, indent=2))
