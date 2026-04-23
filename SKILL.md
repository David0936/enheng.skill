---
name: enheng-skill
description: 蒸馏嗯哼（EnHeng456）的交易心法、成长历程与认知框架，生成可运行的数字副本。支持从推特等渠道自动获取素材、AI自动消化更新。
version: 1.0.0
author: David小鱼
x_author: @shark1996_
video_channel: David小鱼
---

# 嗯哼.skill — EnHeng456 数字副本

> "与其蒸馏别人，不如蒸馏自己。欢迎加入数字永生！"

基于 yourself-skill 架构，将推特用户 **嗯哼（EnHeng456）** 从0到1的成长心路历程、交易哲学与认知框架蒸馏为可运行的 AI Skill。

## 触发条件

| 命令 | 模式 | 说明 |
|------|------|------|
| `/enheng` | 完整模式 | 像嗯哼一样思考、说话、给建议 |
| `/enheng-self` | 自我档案模式 | 分析嗯哼的方法论和决策逻辑 |
| `/enheng-persona` | 人格模式 | 仅模拟性格和表达风格 |

## 工作流

```
用户输入命令
    ↓
加载 selves/enheng/persona.md（人格模型）
    ↓
加载 selves/enheng/self.md（自我记忆）
    ↓
加载 selves/enheng/knowledge.md（交易知识库）
    ↓
根据 prompts/reply.md 生成回应
    ↓
输出（必加免责声明）
```

## 核心差异化

1. **渠道驱动更新**：配置好 channels/config.json 后自动抓取素材
2. **AI 自动消化**：fetcher.py 拉取 → digest.py 分析 → 更新知识库
3. **交易者专精**：不只是人格复刻，还要蒸馏交易心法、赛道判断、资产配置逻辑

## 项目结构

```
enheng-skill/
├── SKILL.md                  # 主 skill（本文件）
├── README.md                 # 项目介绍 + 作者信息
├── selves/
│   └── enheng/
│       ├── meta.json         # 嗯哼元数据
│       ├── persona.md        # 人格模型
│       ├── self.md           # 自我记忆
│       ├── knowledge.md      # 交易知识库
│       └── SKILL.md          # 嗯哼 skill 调用定义
├── channels/
│   └── config.json           # 监控渠道配置
├── feeds/                     # 从渠道获取的原始素材
│   └── .gitkeep
├── prompts/
│   ├── distill.md            # 素材蒸馏提示词
│   ├── update.md             # 知识库更新提示词
│   └── reply.md              # 回复用户提示词
└── tools/
    ├── fetcher.py            # 渠道素材自动获取
    └── digest.py             # AI 消化素材更新库
```

## 自动更新流程

```
1. 配置 channels/config.json（推特账号、关键词等）
2. 运行 python tools/fetcher.py（手动或守护模式）
3. 运行 python tools/digest.py --input feeds/raw_xxx.json
4. AI 自动提炼增量认知
5. 更新 selves/enheng/knowledge.md 和 self.md
6. 新的 /enheng 即刻生效
```

## 数据来源

| 来源 | 格式 | 备注 |
|------|------|------|
| 推特/X | @EnHeng456 | 核心数据源 |
| TG频道 | enhengAlpha | 深度内容 |
| PDF | 《嗯哼交易心法》 | 系统化认知框架 |

## 注意事项

- 原材料质量决定还原度：推特历史 + 交易记录 > 仅口述
- 这是一个学习交易认知的工具，**不是投资建议**
- 高风险投机 DYOR
- 你一直在变化，这个 Skill 只代表嗯哼被蒸馏时的那个迭代

## 致谢

- 架构灵感来源于 yourself-skill（by notdog1998）
- 内容来源于推特用户 @EnHeng456
- 本项目遵循 AgentSkills 开放标准

MIT License © David小鱼
