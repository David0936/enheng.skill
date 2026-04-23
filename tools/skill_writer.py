#!/usr/bin/env python3
"""
skill_writer.py — Skill 文件管理工具

功能：
- 创建新的 selves/{slug}/ 目录结构
- 读取/写入 self.md 和 persona.md
- 根据 digest 合并更新
- 管理版本历史

作者: David小鱼
X: @shark1996_
"""

import os
import re
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('enheng-writer')


class SkillWriter:
    """Skill 文件管理器"""

    def __init__(self, base_dir: str = "selves"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

    def create_slug(self, slug: str, config: Dict = None) -> Path:
        """创建新的数字副本目录"""
        slug_dir = self.base_dir / slug
        slug_dir.mkdir(exist_ok=True)

        # 创建必要文件
        files_to_create = [
            'self.md',
            'persona.md',
            'corrections.md',
            'config.json'
        ]

        for filename in files_to_create:
            filepath = slug_dir / filename
            if not filepath.exists():
                filepath.write_text(f"# {filename.replace('.md', '').title()} — {slug}\n\n"
                                    f"> 创建时间: {datetime.now().isoformat()}\n\n"
                                    f"[待填充]\n",
                                    encoding='utf-8')

        # 写入配置
        config_file = slug_dir / 'config.json'
        if config:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

        logger.info(f"创建数字副本: {slug_dir}")
        return slug_dir

    def read_file(self, slug: str, filename: str) -> str:
        """读取文件内容"""
        filepath = self.base_dir / slug / filename
        if filepath.exists():
            return filepath.read_text(encoding='utf-8')
        return ''

    def write_file(self, slug: str, filename: str, content: str) -> Path:
        """写入文件"""
        filepath = self.base_dir / slug / filename
        filepath.write_text(content, encoding='utf-8')
        logger.info(f"写入文件: {filepath}")
        return filepath

    def merge_digest(self, slug: str, digest_path: str) -> bool:
        """根据 digest 合并更新"""
        digest_file = Path(digest_path)
        if not digest_file.exists():
            logger.error(f"Digest 文件不存在: {digest_path}")
            return False

        with open(digest_file, 'r', encoding='utf-8') as f:
            digest = json.load(f)

        incremental = digest.get('incremental_content', {})
        merged_count = 0

        # 合并 self_memory 更新
        self_memory = incremental.get('self_memory', {})
        if self_memory:
            merged_count += self._merge_self_memory(slug, self_memory)

        # 合并 persona 更新
        persona = incremental.get('persona', {})
        if persona:
            merged_count += self._merge_persona(slug, persona)

        # 记录合并日志
        self._log_merge(slug, digest, merged_count)

        logger.info(f"合并完成: {slug}，更新 {merged_count} 处")
        return True

    def _merge_self_memory(self, slug: str, updates: Dict) -> int:
        """合并自我记忆更新"""
        self_md = self.read_file(slug, 'self.md')
        merged = 0

        # 新成长节点
        for event in updates.get('new_timeline_events', []):
            entry = f"\n- {event['date']}: {event['event']} [增量：{datetime.now().strftime('%Y-%m-%d')}，来源：{event.get('source_tweet_id', 'unknown')}]"
            # 插入到成长轨迹章节
            if '## 成长轨迹' in self_md:
                # 在成长轨迹章节末尾追加
                section_end = self_md.find('## ', self_md.find('## 成长轨迹') + 1)
                if section_end == -1:
                    self_md += entry
                else:
                    self_md = self_md[:section_end] + entry + '\n' + self_md[section_end:]
                merged += 1

        # 数据更新
        for data in updates.get('updated_data_points', []):
            # 在关键数据点表格中更新
            old_pattern = f"{data['field']}.*\n"
            new_entry = f"- {data['field']}: {data['new_value']} [{datetime.now().strftime('%Y-%m-%d')}更新，原值：{data.get('old_value', 'unknown')}]\n"
            if re.search(old_pattern, self_md):
                self_md = re.sub(old_pattern, new_entry, self_md)
                merged += 1

        # 新核心价值观
        for value in updates.get('new_core_values', []):
            entry = f"\n- **{value['value']}** [增量：{datetime.now().strftime('%Y-%m-%d')}]{value.get('context', '')}"
            if '## 核心价值观' in self_md:
                section_end = self_md.find('## ', self_md.find('## 核心价值观') + 1)
                if section_end == -1:
                    self_md += entry
                else:
                    self_md = self_md[:section_end] + entry + '\n' + self_md[section_end:]
                merged += 1

        # 赛道变化
        for sector in updates.get('sector_changes', []):
            entry = f"\n- {sector['sector']} [{sector['action']}，{datetime.now().strftime('%Y-%m-%d')}] —— {sector.get('reasoning', '')}"
            if '## 重点赛道' in self_md:
                section_end = self_md.find('## ', self_md.find('### 重点赛道') + 1)
                if section_end == -1:
                    self_md += entry
                else:
                    self_md = self_md[:section_end] + entry + '\n' + self_md[section_end:]
                merged += 1

        # 更新时间戳
        self_md = self._update_timestamp(self_md)

        self.write_file(slug, 'self.md', self_md)
        return merged

    def _merge_persona(self, slug: str, updates: Dict) -> int:
        """合并人格模型更新"""
        persona_md = self.read_file(slug, 'persona.md')
        merged = 0

        # 新口头禅
        for phrase in updates.get('new_catchphrases', []):
            entry = f"| {phrase['phrase']} | {phrase.get('context', '')} | 新 [增量：{datetime.now().strftime('%Y-%m-%d')}] |\n"
            if '### 口头禅与高频表达' in persona_md:
                # 在表格末尾追加
                persona_md += entry
                merged += 1

        # 风格变化
        for shift in updates.get('style_shifts', []):
            entry = (f"\n- **{shift['aspect']}**: 从\"{shift.get('before', '')}\"变为\"{shift.get('after', '')}\" "
                     f"[增量：{datetime.now().strftime('%Y-%m-%d')}，可能原因：{shift.get('possible_reason', 'unknown')}]")
            if '### 风格变化' not in persona_md:
                persona_md += "\n\n### 风格变化\n"
            persona_md += entry + '\n'
            merged += 1

        # 新硬规则
        for rule in updates.get('new_hard_rules', []):
            entry = (f"\n- **{rule['rule']}** —— {rule.get('context', '')} "
                     f"[增量：{datetime.now().strftime('%Y-%m-%d')}]")
            if '## 第一层：硬规则' in persona_md:
                section_end = persona_md.find('## ', persona_md.find('## 第一层：硬规则') + 1)
                if section_end == -1:
                    persona_md += entry
                else:
                    persona_md = persona_md[:section_end] + entry + '\n' + persona_md[section_end:]
                merged += 1

        # 情感模式变化
        for change in updates.get('emotional_pattern_changes', []):
            entry = (f"\n- **{change['trigger']}**: 从\"{change.get('old_response', '')}\"变为\"{change.get('new_response', '')}\" "
                     f"[增量：{datetime.now().strftime('%Y-%m-%d')}]")
            if '## 第四层：情感模式' in persona_md:
                section_end = persona_md.find('## ', persona_md.find('## 第四层：情感模式') + 1)
                if section_end == -1:
                    persona_md += entry
                else:
                    persona_md = persona_md[:section_end] + entry + '\n' + persona_md[section_end:]
                merged += 1

        # 更新时间戳
        persona_md = self._update_timestamp(persona_md)

        self.write_file(slug, 'persona.md', persona_md)
        return merged

    def _update_timestamp(self, content: str) -> str:
        """更新文件中的时间戳"""
        new_timestamp = f"> 最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if '> 最后更新：' in content:
            content = re.sub(r'> 最后更新：.*', new_timestamp, content)
        return content

    def _log_merge(self, slug: str, digest: Dict, merged_count: int):
        """记录合并日志"""
        log_file = self.base_dir / slug / 'merge.log'
        log_entry = (f"[{datetime.now().isoformat()}] "
                     f"Digest: {digest.get('digest_id', 'unknown')}, "
                     f"Tweets: {digest.get('tweets_analyzed', 0)}, "
                     f"Merged: {merged_count}\n")

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Skill 文件管理工具')
    parser.add_argument('--create', help='创建新的数字副本')
    parser.add_argument('--merge', help='合并 digest 文件')
    parser.add_argument('--slug', default='enheng', help='数字副本代号')
    parser.add_argument('--read', help='读取文件 (self.md / persona.md / corrections.md)')

    args = parser.parse_args()

    writer = SkillWriter()

    if args.create:
        config = {'slug': args.create, 'created_at': datetime.now().isoformat()}
        writer.create_slug(args.create, config)
        print(f"✅ 创建完成: selves/{args.create}/")

    elif args.merge:
        success = writer.merge_digest(args.slug, args.merge)
        if success:
            print(f"✅ 合并完成: {args.slug}")
        else:
            print(f"❌ 合并失败")

    elif args.read:
        content = writer.read_file(args.slug, args.read)
        print(content)

    else:
        print("用法:")
        print("   python skill_writer.py --create enheng")
        print("   python skill_writer.py --merge digested/digest_xxx.json --slug enheng")
        print("   python skill_writer.py --read self.md --slug enheng")


if __name__ == '__main__':
    main()
