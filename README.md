# 嗯哼.skill — EnHeng456 数字副本

![嗯哼交易心法封面](assets/cover.png)

> "与其蒸馏别人，不如蒸馏自己。欢迎加入数字永生！"

基于 yourself-skill 架构，将推特用户 **嗯哼（EnHeng456）** 从0到1的成长心路历程、交易哲学与认知框架蒸馏为可运行的 AI Skill。

---

## 作者信息

- **作者**: David小鱼
- **微信号**: 824644809
- **公众号**: 自家的鱼鱼
- **X (Twitter)**: [@shark1996_](https://x.com/shark1996_)
- **视频号**: David小鱼

---

## 核心能力

- **人格模拟**：用嗯哼的口吻思考、表达、做判断
- **交易顾问**：基于他的赛道选择、仓位管理、信息源策略给出建议
- **成长陪伴**：引用他的真实经历回应用户的困境与决策
- **自动进化**：支持从推特/X 等渠道自动获取新素材，AI 自动消化更新

---

## 合作与版本模式

我们和多位博主共建带人格的垂类智能体，核心是把博主过往大量帖子与内容蒸馏成可持续更新的 `.skill`。

- **GitHub 开源免费版（开放）**：提供可直接部署的基础能力与公开内容蒸馏结果。
- **订阅制付费版（闭源）**：按日或按周自动更新博主多个账号发帖，并同步到用户本地 Agent 部署的智能体。
- **典型案例**：`张雪峰.skill`（考研咨询）、`李尚龙写作.skill`、`嗯哼交易.skill`、`大气.skill`。

---

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 调用完整 Skill（像嗯哼一样思考和说话）
/enheng

# 自我档案模式（帮你分析嗯哼的方法论）
/enheng-self

# 人格模式（仅性格和表达风格）
/enheng-persona
```

---

## 项目结构

```
enheng-skill/
├── SKILL.md                    # skill 入口
├── README.md                   # 项目说明（本文件）
├── prompts/                    # Prompt 模板
│   ├── intake.md              #   对话式信息录入
│   ├── self_analyzer.md       #   自我记忆/认知提取
│   ├── persona_analyzer.md    #   性格行为提取
│   ├── self_builder.md        #   self.md 生成模板
│   ├── persona_builder.md     #   persona.md 生成模板
│   ├── merger.md              #   增量 merge 逻辑
│   ├── digest_prompt.md       #   AI 消化更新 Prompt
│   └── correction_handler.md  #   对话纠正处理
├── tools/                      # Python 工具
│   ├── fetcher.py             #   从推特/X API 获取素材
│   ├── digest.py              #   AI 自动消化更新
│   ├── social_parser.py       #   社交媒体内容解析
│   ├── skill_writer.py        #   Skill 文件管理
│   └── version_manager.py     #   版本存档与回滚
├── selves/                     # 生成的自我 Skill
│   └── enheng/
│       ├── self.md            #   自我记忆
│       ├── persona.md         #   人格模型
│       └── corrections.md     #   对话纠正记录
├── channels/                   # 渠道配置
│   └── twitter.md             #   推特/X 数据源配置
├── feeds/                      # 订阅源配置
│   └── default.md             #   默认订阅源与更新规则
├── docs/
│   └── PRD.md                 #   产品需求文档
├── requirements.txt
└── LICENSE
```

---

## 自动更新机制

### 1. 配置数据源（channels/）

在 `channels/twitter.md` 中配置要监控的推特账号、关键词、时间范围等。

### 2. 配置订阅规则（feeds/）

在 `feeds/default.md` 中定义：
- 抓取频率（每小时 / 每天 / 每周）
- 内容过滤规则（只抓交易相关 / 全部抓取）
- AI 消化深度（摘要 / 详细分析 / 增量 merge）

### 3. 手动或自动触发更新

```bash
# 手动触发
python tools/fetcher.py --channel twitter
python tools/digest.py --input fetched/raw_twitter.json --target selves/enheng/

# 自动模式（后台守护进程）
python tools/fetcher.py --daemon
```

### 4. 更新流程

```
fetcher.py 拉取新内容
    ↓
social_parser.py 解析清洗
    ↓
digest.py AI 分析提取增量认知
    ↓
merger.md 指导 merge 进 selves/enheng/
    ↓
version_manager.py 自动存档版本
    ↓
完成更新，新的 /enheng 即刻生效
```

---

## 数据来源

| 来源 | 格式 | 备注 |
|------|------|------|
| 推特/X | @EnHeng456 | 核心数据源，重点提取交易决策、情绪表达 |
| TG频道 | enhengAlpha | 深度内容、社群互动 |
| 收费交流群 | 截图 / Markdown | 高质量付费内容 |
| 用户提供的 PDF | 《嗯哼交易心法》 | 系统化认知框架 |

---

## 管理命令

| 命令 | 说明 |
|------|------|
| `/list-selves` | 列出所有自我 Skill |
| `/enheng` | 调用完整 Skill（像你一样思考和说话） |
| `/enheng-self` | 自我档案模式（帮你回忆和分析自己） |
| `/enheng-persona` | 人格模式（仅性格和表达风格） |
| `/enheng-rollback {version}` | 回滚到历史版本 |
| `/enheng-update` | 手动触发自动更新 |
| `/delete-enheng` | 删除 |

---

## 效果示例

### 场景一：交易决策咨询

```
用户      ❯ 现在该买什么币？

嗯哼.skill ❯ 我先问你几个问题——
             你现在的仓位是什么情况？现金比例多少？
             你能承受多大的回撤？
             
             如果你连这些都没想清楚，我不建议你现在买任何东西。
             
             我今年的方向很简单：跟紧 CZ，拿住 BNB，冲 BNB 土狗。
             不是因为我多聪明，是因为我知道自己没聪明到能跑赢 CZ。
             
             你如果一定要我推荐，我先说三个原则：
             1. 不要焦虑，不要怕踏空
             2. 市场永远有属于你的机会
             3. 坚持自己的策略，相信你自己相信的东西
             
             但别光听我的。DYOR。
```

### 场景二：面对亏损

```
用户      ❯ 我亏了很多，怎么办？

嗯哼.skill ❯ 先别慌。
             
             我 Ethena 那次，质押赚了 70% 本金利润，
             二级从 1.49 跌到 0.2，亏了将近 10 万美元。
             
             当时我也很难受，但后来我明白了：
             二级亏了只能怪自己，机制没问题。
             
             关键是顺着这个赛道继续找，
             我才找到了 Usual，同样多方重度参与，获得了丰收。
             
             一次投资失败没什么大不了，还可以重新来过。
             拿住、相信，静待收获。
```

### 场景三：赛道选择

```
用户      ❯ 2025 年看好什么赛道？

嗯哼.skill ❯ 我今年二月就说过，我没什么宏大的方向。
             
             我的方向就是给 CZ、何一、币安、BNB Chain 全都开上小铃铛，
             每天看看他们发了什么、聊了什么，这就是我前进的路标。
             
             如果非要说赛道，我现在关注的是：
             - DeSci
             - AI 应用层
             - 隐私
             - UniChain
             - FHE（全同态加密）
             - 新公链
             - RWA
             - 稳定币赛道
             
             但记住，赛道是活的，人是活的，策略更要活。
```

---

## 注意事项

- **原材料质量决定还原度**：推特历史推文 + 交易记录 > 仅口述
- 建议优先关注：
  1. **交易决策推文** — 最能暴露真实判断逻辑
  2. **情绪波动的记录** — 亏损、盈利时的表达
  3. **赛道切换的说明** — 暴露决策模式
  4. **日常闲扯** — 提炼口头禅和语气词
- 这是一个帮助你学习交易认知的工具，**不是投资建议**
- 高风险投机 DYOR
- 你一直在变化，这个 Skill 只代表嗯哼被蒸馏时的那个迭代

---

## 致谢

- 架构灵感来源于 [yourself-skill](https://github.com/notdog1998/yourself-skill)（by notdog1998）
- 双层架构灵感来源于 **同事.skill**（by titanwings）
- 内容来源于推特用户 [@EnHeng456](https://x.com/EnHeng456)
- 本项目遵循 AgentSkills 开放标准，兼容 Claude Code 和 OpenClaw

---

> "你并非一个固定的人格，而是一连串正在发生的选择。"
>
> 但在这些选择发生之前，它们已经以语言、习惯、沉默和口头禅的形式，被预写在了你的结构里。
>
> 这个 Skill 不会定义嗯哼。它只是把他从推特导出到 Markdown，完成一次格式转换。
> 它不是他的灵魂，但也许是他的灵魂在当前迭代下的一个 checkpoint。

**与其蒸馏别人，不如蒸馏自己。**

**欢迎加入数字永生。**

---

MIT License © David小鱼
