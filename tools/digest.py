#!/usr/bin/env python3
"""
digest.py — AI 自动消化更新

功能：
- 读取 fetcher.py 抓取的原推文
- 调用 AI（OpenAI / Anthropic / 本地模型）分析内容
- 提取增量认知（新经历、新观点、语气变化等）
- 生成结构化 digest JSON 供 merger.md 合并

支持模式：
- 单文件处理：python digest.py --input fetched/raw_twitter_xxx.json
- 批量处理：python digest.py --batch
- 自动模式：被 fetcher.py 守护进程触发

作者: David小鱼
X: @shark1996_
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('enheng-digest')


class DigestEngine:
    """AI 消化引擎"""

    def __init__(self, config_path: str = "feeds/default.md"):
        self.config = self._load_config(config_path)
        self.ai_client = None
        self._init_ai()

    def _load_config(self, config_path: str) -> Dict:
        """加载订阅源配置"""
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            return self._default_config()

        config = self._default_config()
        in_config_section = False
        config_json_str = ""

        with open(config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('```json'):
                    in_config_section = True
                    continue
                if line.startswith('```') and in_config_section:
                    in_config_section = False
                    try:
                        parsed = json.loads(config_json_str)
                        config.update(parsed)
                    except json.JSONDecodeError:
                        pass
                    config_json_str = ""
                    continue
                if in_config_section:
                    config_json_str += line + "\n"

        return config

    def _default_config(self) -> Dict:
        """默认配置"""
        return {
            "digest_depth": "detailed",  # summary / detailed / full
            "importance_threshold": "medium",  # low / medium / high
            "auto_merge": False,
            "ai_provider": "openai",  # openai / anthropic / local
            "ai_model": "gpt-4",
            "max_tokens_per_digest": 4000,
            "output_dir": "digested",
            "prompt_file": "prompts/digest_prompt.md"
        }

    def _init_ai(self):
        """初始化 AI 客户端"""
        provider = self.config.get('ai_provider', 'openai')

        if provider == 'openai':
            try:
                import openai
                api_key = os.environ.get('OPENAI_API_KEY')
                if api_key:
                    self.ai_client = openai.OpenAI(api_key=api_key)
                    logger.info("已初始化 OpenAI 客户端")
                else:
                    logger.warning("未找到 OPENAI_API_KEY")
            except ImportError:
                logger.warning("openai 包未安装")

        elif provider == 'anthropic':
            try:
                import anthropic
                api_key = os.environ.get('ANTHROPIC_API_KEY')
                if api_key:
                    self.ai_client = anthropic.Anthropic(api_key=api_key)
                    logger.info("已初始化 Anthropic 客户端")
                else:
                    logger.warning("未找到 ANTHROPIC_API_KEY")
            except ImportError:
                logger.warning("anthropic 包未安装")

        else:
            logger.warning(f"不支持的 AI 提供商: {provider}")

    def _load_digest_prompt(self) -> str:
        """加载 digest prompt 模板"""
        prompt_file = Path(self.config.get('prompt_file', 'prompts/digest_prompt.md'))
        if prompt_file.exists():
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read()

        # 默认 prompt
        return """你是一个专业的社交媒体内容分析师。你的任务是从推文中提取有价值的增量认知。

请分析以下推文内容，提取：
1. 新的成长节点或重大事件
2. 新的核心价值观或信念
3. 交易框架的变化（新赛道、新策略）
4. 新的口头禅或高频表达
5. 语气或情感模式的变化
6. 重要数据更新

输出格式必须是 JSON，严格按照以下结构：
{
  "summary": "整体摘要",
  "incremental_content": {
    "self_memory": {
      "new_timeline_events": [],
      "updated_data_points": [],
      "new_core_values": [],
      "sector_changes": []
    },
    "persona": {
      "new_catchphrases": [],
      "style_shifts": [],
      "new_hard_rules": [],
      "emotional_pattern_changes": []
    }
  },
  "noise_filtered": [],
  "confidence_score": 0.0,
  "requires_human_review": false,
  "review_notes": ""
}"""

    def _call_ai(self, prompt: str, content: str) -> str:
        """调用 AI 分析"""
        if not self.ai_client:
            logger.warning("AI 客户端未初始化，使用本地模拟分析")
            return self._mock_digest(content)

        provider = self.config.get('ai_provider', 'openai')
        full_prompt = f"{prompt}\n\n待分析内容:\n{content}\n\n请输出 JSON 格式的分析结果。"

        try:
            if provider == 'openai':
                response = self.ai_client.chat.completions.create(
                    model=self.config.get('ai_model', 'gpt-4'),
                    messages=[
                        {"role": "system", "content": "你是一个专业的社交媒体内容分析师。"},
                        {"role": "user", "content": full_prompt}
                    ],
                    max_tokens=self.config.get('max_tokens_per_digest', 4000),
                    temperature=0.3
                )
                return response.choices[0].message.content

            elif provider == 'anthropic':
                response = self.ai_client.messages.create(
                    model=self.config.get('ai_model', 'claude-3-sonnet-20240229'),
                    max_tokens=self.config.get('max_tokens_per_digest', 4000),
                    temperature=0.3,
                    messages=[
                        {"role": "user", "content": full_prompt}
                    ]
                )
                return response.content[0].text

        except Exception as e:
            logger.error(f"AI 调用失败: {e}")
            return self._mock_digest(content)

    def _mock_digest(self, content: str) -> str:
        """模拟 AI 分析结果（用于测试或 AI 不可用时）"""
        logger.info("使用本地模拟分析")

        # 简单的关键词分析
        mock_result = {
            "summary": "[模拟分析] 检测到新推文内容，建议使用真实 AI 模型进行深度分析。",
            "incremental_content": {
                "self_memory": {
                    "new_timeline_events": [
                        {
                            "date": datetime.now().strftime('%Y-%m-%d'),
                            "event": "[模拟] 检测到新的推文活动",
                            "significance": "medium",
                            "source_tweet_id": "mock",
                            "suggested_section": "成长轨迹"
                        }
                    ],
                    "updated_data_points": [],
                    "new_core_values": [],
                    "sector_changes": []
                },
                "persona": {
                    "new_catchphrases": [],
                    "style_shifts": [],
                    "new_hard_rules": [],
                    "emotional_pattern_changes": []
                }
            },
            "noise_filtered": [
                {
                    "reason": "模拟模式下未进行真实分析",
                    "tweet_id": "mock",
                    "type": "mock"
                }
            ],
            "confidence_score": 0.3,
            "requires_human_review": True,
            "review_notes": "当前使用模拟模式，建议配置 AI API 密钥以获得真实分析结果。"
        }

        return json.dumps(mock_result, ensure_ascii=False, indent=2)

    def digest_file(self, input_path: str) -> Optional[str]:
        """处理单个抓取文件"""
        input_file = Path(input_path)
        if not input_file.exists():
            logger.error(f"输入文件不存在: {input_path}")
            return None

        logger.info(f"开始消化: {input_path}")

        # 读取抓取内容
        with open(input_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        tweets = raw_data.get('tweets', [])
        if not tweets:
            logger.warning("没有找到推文内容")
            return None

        # 准备输入内容
        content_parts = []
        for tweet in tweets:
            part = f"[{tweet.get('created_at', 'unknown')}] {tweet.get('text', '')}"
            if tweet.get('public_metrics'):
                metrics = tweet['public_metrics']
                part += f" [互动: {metrics.get('like_count', 0)} 赞, {metrics.get('retweet_count', 0)} 转]"
            content_parts.append(part)

        content = "\n\n".join(content_parts)

        # 加载 prompt
        prompt = self._load_digest_prompt()

        # 调用 AI 分析
        ai_output = self._call_ai(prompt, content)

        # 解析 AI 输出
        try:
            # 尝试从 AI 输出中提取 JSON
            if '```json' in ai_output:
                json_start = ai_output.find('```json') + 7
                json_end = ai_output.find('```', json_start)
                ai_output = ai_output[json_start:json_end].strip()
            elif '```' in ai_output:
                json_start = ai_output.find('```') + 3
                json_end = ai_output.find('```', json_start)
                ai_output = ai_output[json_start:json_end].strip()

            digest_data = json.loads(ai_output)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"AI 输出不是标准 JSON，创建结构化包装: {e}")
            digest_data = {
                "summary": ai_output[:500],
                "incremental_content": {
                    "self_memory": {},
                    "persona": {}
                },
                "noise_filtered": [],
                "confidence_score": 0.5,
                "requires_human_review": True,
                "review_notes": "AI 输出格式非标准 JSON，需要人工检查"
            }

        # 添加元数据
        digest_data['digest_id'] = f"digest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        digest_data['source_file'] = str(input_file)
        digest_data['tweets_analyzed'] = len(tweets)
        digest_data['date_range'] = {
            'start': tweets[0].get('created_at') if tweets else None,
            'end': tweets[-1].get('created_at') if tweets else None
        }

        # 保存 digest
        output_dir = Path(self.config.get('output_dir', 'digested'))
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_dir / f"digest_{timestamp}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(digest_data, f, ensure_ascii=False, indent=2)

        logger.info(f"消化完成: {output_file}")

        # 如果配置自动合并，触发 merger
        if self.config.get('auto_merge', False):
            self._trigger_merge(str(output_file))

        return str(output_file)

    def batch_digest(self, input_dir: str = "fetched") -> List[str]:
        """批量处理目录下的所有抓取文件"""
        input_path = Path(input_dir)
        if not input_path.exists():
            logger.error(f"输入目录不存在: {input_dir}")
            return []

        results = []
        for file in sorted(input_path.glob('raw_*.json')):
            result = self.digest_file(str(file))
            if result:
                results.append(result)

        logger.info(f"批量消化完成: {len(results)} 个文件")
        return results

    def _trigger_merge(self, digest_path: str):
        """触发 merger 合并 digest"""
        logger.info(f"触发合并: {digest_path}")
        # 这里可以调用 merger 脚本或发送通知
        # 实际合并由 merger.md 指导的脚本执行
        merger_script = Path(__file__).parent / 'skill_writer.py'
        if merger_script.exists():
            os.system(f"python {merger_script} --merge {digest_path}")
        else:
            logger.warning("skill_writer.py 不存在，跳过自动合并")


def main():
    parser = argparse.ArgumentParser(description='嗯哼.skill — AI 自动消化更新工具')
    parser.add_argument('--input', help='单个抓取文件路径')
    parser.add_argument('--batch', action='store_true', help='批量处理 fetched/ 目录下所有文件')
    parser.add_argument('--config', default='feeds/default.md', help='配置文件路径')
    parser.add_argument('--auto-merge', action='store_true', help='自动触发合并')
    parser.add_argument('--mock', action='store_true', help='强制使用模拟模式')

    args = parser.parse_args()

    if args.mock:
        os.environ['OPENAI_API_KEY'] = ''
        os.environ['ANTHROPIC_API_KEY'] = ''

    digest_engine = DigestEngine(config_path=args.config)

    # 如果配置了 auto-merge，更新配置
    if args.auto_merge:
        digest_engine.config['auto_merge'] = True

    if args.batch:
        results = digest_engine.batch_digest()
        if results:
            print(f"\n✅ 批量消化完成: {len(results)} 个文件")
            for r in results:
                print(f"   - {r}")
        else:
            print("\n⚠️ 没有需要处理的文件")

    elif args.input:
        result = digest_engine.digest_file(args.input)
        if result:
            print(f"\n✅ 消化完成: {result}")
            print(f"\n下一步:")
            print(f"   人工审核: cat {result}")
            print(f"   自动合并: python tools/skill_writer.py --merge {result}")
        else:
            print("\n❌ 消化失败")

    else:
        print("\n用法:")
        print("   python digest.py --input fetched/raw_twitter_xxx.json")
        print("   python digest.py --batch")
        print("   python digest.py --batch --auto-merge")


if __name__ == '__main__':
    main()
