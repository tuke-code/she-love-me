# 笔记 01：项目入口与 Agent 架构

## 1. 模块定位

- **所属层级**
  - Agent 接入层
- **本节目标**
  - 理解 Agent 如何通过仓库结构识别项目能力
  - 理解 `AGENTS.md` 与 `openai.yaml` 的职责
  - 建立“入口层 → 流程层 → 脚本层”的总体认知

## 2. 本节涉及的关键文件

- **`AGENTS.md`**

  - 仓库级规则文件
  - 告诉 Agent 这个仓库的核心能力、Skill 入口和工作约束
- **`.agents/skills/she-love-me/agents/openai.yaml`**

  - 技能级元数据配置
  - 用于补充显示名、简介、默认提示词和调用策略

## 3. `AGENTS.md` 的作用

### 核心职责

- **定义仓库用途**

  - 这个仓库用于分析微信/QQ 聊天记录并生成 HTML 报告
- **指定 Skill 入口**

  - 通用入口：
    - `.agents/skills/she-love-me/SKILL.md`
  - Claude/OpenClaw 镜像入口：
    - `.claude/skills/she-love-me/SKILL.md`
- **给 Codex 提供行为约束**

  - 优先使用 `she-love-me`
  - 工作目录保持在仓库根目录
  - 敏感和生成数据放在：
    - `vendor/`
    - `data/`
    - `reports/`
  - 可通过 `$she-love-me` 显式调用

### 本质理解

`AGENTS.md` 不是业务代码，而是：

- **给 Agent 的仓库说明书**
- **仓库级能力声明**
- **工作流入口提示**

## 4. `openai.yaml` 的作用

文件内容核心包括：

- `display_name`
- `short_description`
- `brand_color`
- `default_prompt`
- `allow_implicit_invocation`

### 核心职责

- **定义 Skill 展示信息**

  - 技能名称
  - 技能简介
  - 品牌色
- **定义默认触发提示**

  - 告诉工具在调用这个技能时，应该如何 framing 任务
- **定义调用策略**

  - 是否允许隐式调用

### 本质理解

`openai.yaml` 不是执行逻辑，而是：

- **技能级元数据配置**
- **调用体验配置**
- **能力发现辅助配置**

## 5. Codex 为什么能识别这个项目能力

Codex 之所以能通过仓库结构识别这个项目，不是因为它“猜到了”仓库用途，而是因为仓库里提供了一套结构化、约定化的 Agent 入口信息。

### 识别依据

- **`AGENTS.md`**

  - 告诉 Codex 这个仓库有哪些技能、该优先用什么
- **`SKILL.md`**

  - 告诉 Codex 这个技能的完整执行流程
- **`openai.yaml`**

  - 告诉 Codex 风格工具这个技能如何展示、如何触发、如何做默认提示

### 结论

Codex 识别到的不是某个 Python 文件，而是：

- **一个完整工作流能力包**

## 6. `openai.yaml` 可能被哪些工具识别

更准确地说，不是“模型直接识别”，而是：

- **支持 OpenAI / Codex 风格 Agent 规范的工具链**
  - 会读取这类文件

### 主要面向

- **Codex / OpenAI 风格 Agent 工具**

### 不应假设一定会识别的对象

- **普通 Python 运行环境**
- **裸模型本身**
- **所有 IDE**
- **所有 AI 工具**

### 结论

`openai.yaml` 主要是：

- **给 OpenAI/Codex 风格 Agent 生态用的元数据文件**

## 7. `openai.yaml` 被识别后的具体表现

### `display_name`

- **表现**
  - 技能在列表或界面中显示为：
    - `她爱我吗？恋情分析室`

### `short_description`

- **表现**
  - 工具可能展示一段简短说明，帮助理解技能用途

### `default_prompt`

- **表现**
  - 影响工具如何默认理解并启动这个技能
  - 帮助 Agent 按正确流程理解任务，而不是随意执行脚本

### `allow_implicit_invocation: true`

- **表现**
  - 用户即使不显式输入 `$she-love-me`
  - 只要表达相关意图，工具也可能自动匹配该技能

## 8. 本节最重要的架构理解

这一节最关键的不是记住字段名，而是建立下面这个认知：

```text
用户请求
  ↓
Agent 读取 AGENTS.md
  ↓
知道仓库里有 she-love-me 这个能力
  ↓
通过 openai.yaml 获取展示信息和默认调用提示
  ↓
进入 SKILL.md 定义的完整流程
  ↓
再调用 scripts/*.py 执行具体工作
```

## 9. 本节学到的设计思想

- **把仓库级规则与技能级元数据分开**
- **把能力声明与执行逻辑分开**
- **把入口层与脚本层分开**
- **让 Agent 先理解任务，再执行任务**
- **通过约定目录和文件结构提高自动识别能力**

## 10. 我目前的理解总结

- `AGENTS.md` 负责定义仓库级能力与规则
- `openai.yaml` 负责定义技能级展示与调用体验
- `SKILL.md` 才是工作流的真正流程定义
- 这个项目的入口不是 `main.py`，而是 **Agent 入口文件 + Skill 文件**
- 这是一个 **Agent 工作流项目**，不是普通脚本集合

## 11. 目前仍可继续思考的问题

- **为什么 `AGENTS.md` 和 `SKILL.md` 不能合并成一个文件？**
- **为什么要同时维护 `.agents/skills/` 和 `.claude/skills/`？**
- **隐式调用在复杂场景下会不会误触发？**
- **如果以后支持更多 Agent 平台，目录结构会如何扩展？**

## 12. 一句话总结

> 这一节的核心结论是：这个项目之所以能被 Codex 识别，不是因为某个脚本暴露了能力，而是因为仓库通过 `AGENTS.md`、`SKILL.md` 和 `openai.yaml` 提供了一套结构化的 Agent 入口与技能描述。
