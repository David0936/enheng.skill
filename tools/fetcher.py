#!/usr/bin/env python3
"""
fetcher.py — 从推特/X API 获取素材

支持：
- 按用户拉取推文
- 按关键词搜索
- 按时间范围过滤
- 增量抓取（只抓新内容）
- 后台守护模式

作者: David小鱼
X: @shark1996_
"""

import os
import sys
import json
import time
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# 尝试导入 tweepy，如未安装则提示
try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('enheng-fetcher')


class TwitterFetcher:
    """推特/X 数据获取器"""

    def __init__(self, config_path: str = "channels/twitter.md"):
        self.config = self._load_config(config_path)
        self.client = None
        self._init_api()

    def _load_config(self, config_path: str) -> Dict:
        """加载推特渠道配置"""
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            return self._default_config()

        # 解析 Markdown 格式的配置
        config = self._default_config()
        in_config_section = False

        with open(config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('```json'):
                    in_config_section = True
                    continue
                if line.startswith('```') and in_config_section:
                    in_config_section = False
                    continue
                if in_config_section:
                    # 尝试解析 JSON 配置
                    try:
                        parsed = json.loads(line)
                        config.update(parsed)
                    except json.JSONDecodeError:
                        pass

        return config

    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            "handles": ["EnHeng456"],
            "keywords": ["BNB", "CZ", "交易", "BTC", "ETH", "DeFi"],
            "fetch_interval_hours": 24,
            "max_tweets_per_fetch": 50,
            "include_replies": False,
            "include_retweets": False,
            "time_range_days": 7,
            "output_dir": "fetched",
            "state_file": ".fetcher_state.json"
        }

    def _init_api(self):
        """初始化 Twitter API"""
        if not TWEEPY_AVAILABLE:
            logger.warning("tweepy 未安装，将使用模拟模式")
            return

        # 从环境变量读取 API 密钥
        bearer_token = os.environ.get('TWITTER_BEARER_TOKEN')
        api_key = os.environ.get('TWITTER_API_KEY')
        api_secret = os.environ.get('TWITTER_API_SECRET')
        access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
        access_secret = os.environ.get('TWITTER_ACCESS_SECRET')

        if bearer_token:
            self.client = tweepy.Client(
                bearer_token=bearer_token,
                wait_on_rate_limit=True
            )
            logger.info("已初始化 Twitter API (Bearer Token)")
        elif api_key and api_secret:
            self.client = tweepy.Client(
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_secret,
                wait_on_rate_limit=True
            )
            logger.info("已初始化 Twitter API (User Auth)")
        else:
            logger.warning("未找到 Twitter API 密钥，将使用模拟模式")

    def _load_state(self) -> Dict:
        """加载上次抓取状态"""
        state_file = Path(self.config.get('state_file', '.fetcher_state.json'))
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_state(self, state: Dict):
        """保存抓取状态"""
        state_file = Path(self.config.get('state_file', '.fetcher_state.json'))
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def _get_since_id(self, handle: str) -> Optional[str]:
        """获取上次抓取的最新推文 ID"""
        state = self._load_state()
        return state.get(handle, {}).get('last_tweet_id')

    def _update_state(self, handle: str, last_tweet_id: str, count: int):
        """更新抓取状态"""
        state = self._load_state()
        state[handle] = {
            'last_tweet_id': last_tweet_id,
            'last_fetch': datetime.now().isoformat(),
            'total_fetched': state.get(handle, {}).get('total_fetched', 0) + count
        }
        self._save_state(state)

    def fetch_user_tweets(self, handle: str, max_results: int = None) -> List[Dict]:
        """获取指定用户的推文"""
        if max_results is None:
            max_results = self.config.get('max_tweets_per_fetch', 50)

        since_id = self._get_since_id(handle)

        if not self.client:
            logger.warning(f"API 未初始化，返回模拟数据: @{handle}")
            return self._mock_tweets(handle, max_results)

        try:
            # 获取用户 ID
            user = self.client.get_user(username=handle.replace('@', ''))
            if not user or not user.data:
                logger.error(f"未找到用户: @{handle}")
                return []

            user_id = user.data.id

            # 获取推文
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=min(max_results, 100),  # API 限制
                since_id=since_id,
                exclude=['retweets', 'replies'] if not self.config.get('include_retweets') else None,
                tweet_fields=['created_at', 'public_metrics', 'context_annotations', 'entities']
            )

            if not tweets or not tweets.data:
                logger.info(f"@{handle} 没有新推文")
                return []

            results = []
            for tweet in tweets.data:
                tweet_dict = {
                    'id': str(tweet.id),
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat() if tweet.created_at else None,
                    'public_metrics': tweet.public_metrics,
                    'source': f"twitter://{handle}",
                    'url': f"https://twitter.com/{handle}/status/{tweet.id}"
                }
                results.append(tweet_dict)

            # 更新状态
            if results:
                self._update_state(handle, results[0]['id'], len(results))

            logger.info(f"成功获取 @{handle} 的 {len(results)} 条推文")
            return results

        except tweepy.errors.TooManyRequests:
            logger.error("Twitter API 速率限制，请稍后重试")
            return []
        except Exception as e:
            logger.error(f"获取推文失败: {e}")
            return []

    def fetch_by_keywords(self, keywords: List[str], max_results: int = 50) -> List[Dict]:
        """按关键词搜索推文"""
        if not self.client:
            logger.warning("API 未初始化，返回模拟数据")
            return self._mock_search(keywords, max_results)

        query = ' OR '.join(keywords)

        try:
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=min(max_results, 100),
                tweet_fields=['created_at', 'public_metrics', 'author_id', 'entities']
            )

            if not tweets or not tweets.data:
                return []

            results = []
            for tweet in tweets.data:
                tweet_dict = {
                    'id': str(tweet.id),
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat() if tweet.created_at else None,
                    'public_metrics': tweet.public_metrics,
                    'author_id': str(tweet.author_id) if tweet.author_id else None,
                    'source': 'twitter://search',
                    'url': f"https://twitter.com/i/web/status/{tweet.id}"
                }
                results.append(tweet_dict)

            logger.info(f"关键词搜索返回 {len(results)} 条推文")
            return results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    def _mock_tweets(self, handle: str, count: int) -> List[Dict]:
        """模拟推文数据（用于测试或 API 不可用时）"""
        logger.info(f"生成模拟数据: @{handle} x {count}")
        mock_data = []
        now = datetime.now()

        for i in range(min(count, 5)):
            tweet = {
                'id': f'mock_{handle}_{i}_{int(time.time())}',
                'text': f'[模拟数据] 这是 @{handle} 的第 {i+1} 条模拟推文。实际使用时请配置 Twitter API 密钥。',
                'created_at': (now - timedelta(hours=i*6)).isoformat(),
                'public_metrics': {
                    'retweet_count': 10 + i * 5,
                    'like_count': 50 + i * 10,
                    'reply_count': 5 + i
                },
                'source': f'twitter://{handle}',
                'url': f'https://twitter.com/{handle}/status/mock_{i}',
                '_mock': True
            }
            mock_data.append(tweet)

        return mock_data

    def _mock_search(self, keywords: List[str], count: int) -> List[Dict]:
        """模拟搜索结果"""
        logger.info(f"生成模拟搜索数据: {keywords} x {count}")
        return self._mock_tweets('search_result', min(count, 3))

    def save_tweets(self, tweets: List[Dict], output_dir: str = None) -> str:
        """保存推文到文件"""
        if output_dir is None:
            output_dir = self.config.get('output_dir', 'fetched')

        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"raw_twitter_{timestamp}.json"
        filepath = os.path.join(output_dir, filename)

        data = {
            'fetch_time': datetime.now().isoformat(),
            'source': 'twitter',
            'tweet_count': len(tweets),
            'tweets': tweets
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"推文已保存: {filepath}")
        return filepath

    def run(self, mode: str = 'user'):
        """执行抓取"""
        all_tweets = []

        if mode == 'user':
            for handle in self.config.get('handles', []):
                tweets = self.fetch_user_tweets(handle)
                all_tweets.extend(tweets)

        elif mode == 'search':
            keywords = self.config.get('keywords', [])
            if keywords:
                tweets = self.fetch_by_keywords(keywords)
                all_tweets.extend(tweets)

        elif mode == 'all':
            # 先抓用户推文，再抓关键词
            for handle in self.config.get('handles', []):
                tweets = self.fetch_user_tweets(handle)
                all_tweets.extend(tweets)

            keywords = self.config.get('keywords', [])
            if keywords:
                tweets = self.fetch_by_keywords(keywords)
                all_tweets.extend(tweets)

        if all_tweets:
            filepath = self.save_tweets(all_tweets)
            return filepath
        else:
            logger.info("没有新内容")
            return None

    def daemon_mode(self):
        """后台守护模式"""
        interval = self.config.get('fetch_interval_hours', 24)
        logger.info(f"启动守护模式，抓取间隔: {interval} 小时")

        while True:
            try:
                filepath = self.run(mode='all')
                if filepath:
                    # 自动触发 digest
                    self._trigger_digest(filepath)
            except Exception as e:
                logger.error(f"守护模式出错: {e}")

            logger.info(f"下次抓取: {interval} 小时后")
            time.sleep(interval * 3600)

    def _trigger_digest(self, filepath: str):
        """触发 digest.py 处理新抓取的内容"""
        digest_script = Path(__file__).parent / 'digest.py'
        if digest_script.exists():
            logger.info(f"触发 digest: {filepath}")
            os.system(f"python {digest_script} --input {filepath}")
        else:
            logger.warning(f"digest.py 不存在，跳过自动处理")


def main():
    parser = argparse.ArgumentParser(description='嗯哼.skill — 推特/X 素材获取工具')
    parser.add_argument('--channel', default='twitter', help='渠道名称 (默认: twitter)')
    parser.add_argument('--mode', choices=['user', 'search', 'all'], default='all',
                        help='抓取模式')
    parser.add_argument('--daemon', action='store_true', help='后台守护模式')
    parser.add_argument('--config', default='channels/twitter.md', help='配置文件路径')
    parser.add_argument('--output', default='fetched', help='输出目录')
    parser.add_argument('--mock', action='store_true', help='强制使用模拟数据')

    args = parser.parse_args()

    if args.mock:
        global TWEEPY_AVAILABLE
        TWEEPY_AVAILABLE = False

    fetcher = TwitterFetcher(config_path=args.config)

    if args.daemon:
        fetcher.daemon_mode()
    else:
        result = fetcher.run(mode=args.mode)
        if result:
            print(f"\n✅ 抓取完成: {result}")
            print(f"   推文数量: 见文件内容")
            print(f"\n下一步: python tools/digest.py --input {result}")
        else:
            print("\n⚠️ 没有新内容")


if __name__ == '__main__':
    main()
