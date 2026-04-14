# she-love-me 仓库本次 Git 操作记录

## 背景

这次操作发生在本地仓库 `F:\projects\she-love-me`。
目标是：
- 修改 `scripts/setup_check.py`
- 提交本次改动
- 将代码推送到自己的 fork
- 准备向上游仓库发 Pull Request

本次 fork 仓库：`https://github.com/Bluestar-34/she-love-me.git`
上游仓库：`https://github.com/863401402/she-love-me`

---

## 一、先查看仓库状态

### 1. 查看当前改动

使用：
```bash
git -c safe.directory=F:/projects/she-love-me status --short
```

作用：
- 快速查看哪些文件被修改
- 确认本次改动范围是否符合预期
- 这里只看到 `scripts/setup_check.py` 被修改

说明：
- 这里额外带了 `-c safe.directory=F:/projects/she-love-me`
- 原因是这个仓库在当前运行环境下触发了 Git 的 `dubious ownership` 保护
- 临时加这个参数，可以告诉 Git：这个目录是可信的

### 2. 查看具体 diff

使用：
```bash
git -c safe.directory=F:/projects/she-love-me diff -- scripts/setup_check.py
```

作用：
- 精确查看某个文件改了什么
- 提交前确认没有误改

本次看到的重点改动：
- 新增 `RUNTIME_DIRS`
- 新增 `ensure_runtime_dirs()`
- 在 `main()` 中执行目录初始化，并将结果写入 `actions`

---

## 二、提交本次改动

### 3. 把文件加入暂存区

使用：
```bash
git -c safe.directory=F:/projects/she-love-me add scripts/setup_check.py
```

作用：
- 告诉 Git：这个文件要进入下一次提交
- `add` 只是进入暂存区，不代表已经提交

### 4. 创建提交

使用：
```bash
git -c safe.directory=F:/projects/she-love-me commit -m "Initialize runtime directories in setup check"
```

作用：
- 把暂存区中的改动打成一个 commit
- 这一步会生成一个提交哈希

本次生成的提交：
```text
492cc68 Initialize runtime directories in setup check
```

注意：
- 一开始并行执行 `add` 和 `commit` 时，`commit` 先执行了，导致失败
- 报错内容大意是：没有已暂存的改动
- 之后改为顺序执行，成功提交

经验：
- `git add` 和 `git commit` 不要并行执行
- 这两个操作有明显先后依赖关系

---

## 三、确认提交结果

### 5. 查看最近一次提交

使用：
```bash
git -c safe.directory=F:/projects/she-love-me log -1 --stat --oneline
```

作用：
- 查看最新一次提交的摘要
- 同时确认本次提交影响了哪些文件、增加了多少行

本次输出重点：
```text
492cc68 Initialize runtime directories in setup check
scripts/setup_check.py | 23 +++++++++++++++++++++++
```

### 6. 再检查工作树是否干净

使用：
```bash
git -c safe.directory=F:/projects/she-love-me status --short
```

作用：
- 确认提交后没有遗漏未提交内容
- 本次结果为空，说明工作树干净

---

## 四、检查并设置远端仓库

### 7. 查看当前 remote

使用：
```bash
git -c safe.directory=F:/projects/she-love-me remote -v
```

最开始看到的是：
```text
origin https://github.com/863401402/she-love-me (fetch)
origin https://github.com/863401402/she-love-me (push)
```

说明：
- 当前本地仓库原本直接指向上游仓库
- 但这次要从自己的 fork 发 PR，更合理的做法是：
  - `origin` 指向自己的 fork
  - `upstream` 指向原仓库

### 8. 把 origin 改成自己的 fork

使用：
```bash
git -c safe.directory=F:/projects/she-love-me remote set-url origin https://github.com/Bluestar-34/she-love-me.git
```

作用：
- 修改 `origin` 的 fetch / push 地址
- 之后 `git push origin ...` 就会推到自己的 fork

### 9. 添加上游仓库 upstream

使用：
```bash
git -c safe.directory=F:/projects/she-love-me remote add upstream https://github.com/863401402/she-love-me
```

作用：
- 保留原仓库地址，方便以后同步上游更新
- 这是 fork 工作流中的常见做法

### 10. 再次确认 remote 配置

使用：
```bash
git -c safe.directory=F:/projects/she-love-me remote -v
```

本次最终配置：
```text
origin   https://github.com/Bluestar-34/she-love-me.git (fetch)
origin   https://github.com/Bluestar-34/she-love-me.git (push)
upstream https://github.com/863401402/she-love-me (fetch)
upstream https://github.com/863401402/she-love-me (push)
```

这是比较标准的 fork 布局。

---

## 五、创建并推送分支

### 11. 创建功能分支

使用：
```bash
git -c safe.directory=F:/projects/she-love-me checkout -b chore/init-runtime-dirs
```

作用：
- 基于当前 `main` 新建一个分支
- 以后 PR 一般从功能分支发，不直接从本地 `main` 发

本次分支名：
```text
chore/init-runtime-dirs
```

命名思路：
- `chore/`：表示杂项维护或工程性调整
- `init-runtime-dirs`：说明本次改动是初始化运行目录

### 12. 推送到自己的 fork

使用：
```bash
git -c safe.directory=F:/projects/she-love-me push -u origin chore/init-runtime-dirs
```

作用：
- 把本地分支推送到远端 fork
- `-u` 会建立跟踪关系
- 之后在这个分支上继续 push / pull 会更方便

推送成功后，GitHub 提示可直接创建 PR：
```text
https://github.com/Bluestar-34/she-love-me/pull/new/chore/init-runtime-dirs
```

---

## 六、本次 PR 的目标关系

本次 Pull Request 应该这样选：

- base repository: `863401402/she-love-me`
- base branch: `main`
- head repository: `Bluestar-34/she-love-me`
- compare branch: `chore/init-runtime-dirs`

这表示：
- 代码来自自己的 fork 分支
- 合并目标是上游仓库的 `main`

---

## 七、这次实际完成的 Git 操作清单

按顺序汇总：

```bash
git -c safe.directory=F:/projects/she-love-me status --short
git -c safe.directory=F:/projects/she-love-me diff -- scripts/setup_check.py
git -c safe.directory=F:/projects/she-love-me add scripts/setup_check.py
git -c safe.directory=F:/projects/she-love-me commit -m "Initialize runtime directories in setup check"
git -c safe.directory=F:/projects/she-love-me log -1 --stat --oneline
git -c safe.directory=F:/projects/she-love-me status --short
git -c safe.directory=F:/projects/she-love-me remote -v
git -c safe.directory=F:/projects/she-love-me remote set-url origin https://github.com/Bluestar-34/she-love-me.git
git -c safe.directory=F:/projects/she-love-me remote add upstream https://github.com/863401402/she-love-me
git -c safe.directory=F:/projects/she-love-me remote -v
git -c safe.directory=F:/projects/she-love-me checkout -b chore/init-runtime-dirs
git -c safe.directory=F:/projects/she-love-me push -u origin chore/init-runtime-dirs
```

---

## 八、这次学到的关键点

### 1. `status`、`diff`、`add`、`commit` 是最基本的一组闭环

可以理解为：
- `status` 看状态
- `diff` 看细节
- `add` 选中要提交的改动
- `commit` 生成提交记录

### 2. fork 工作流建议使用双远端

推荐结构：
- `origin` = 自己的 fork
- `upstream` = 原仓库

这样：
- 推代码时推到自己的仓库
- 同步更新时从上游拉取

### 3. 提交最好基于功能分支

不要长期直接在 `main` 上开发并直接推送。
更稳妥的方式是：
- 本地 `main` 保持相对干净
- 每次改动从 `main` 切一个新分支
- 在分支上提交、推送、发 PR

### 4. 先后有依赖的 Git 操作不要并行

例如：
- `git add`
- `git commit`

这两个必须顺序执行。
否则可能出现：
- `commit` 先跑
- 结果提示没有已暂存内容

### 5. 遇到 dubious ownership 可以临时使用 `safe.directory`

本次环境中，Git 提示仓库所有者与当前执行用户不一致。
解决方式之一是：
```bash
git -c safe.directory=F:/projects/she-love-me <git命令>
```

这是临时告诉 Git：本次命令把这个仓库视为安全目录。

---

## 九、以后可复用的最短流程

如果以后在 fork 仓库里重复类似流程，可以直接参考：

```bash
# 1. 看改动
git status --short
git diff -- <文件>

# 2. 提交改动
git add <文件>
git commit -m "你的提交信息"

# 3. 切分支
git checkout -b <分支名>

# 4. 推到自己的 fork
git push -u origin <分支名>

# 5. 去 GitHub 页面创建 PR
```

如果是第一次配置 fork 远端，再补：

```bash
git remote set-url origin <你的fork地址>
git remote add upstream <原仓库地址>
```

---

## 十、后续同步上游仓库的常用命令

以后如果上游仓库更新了，可以这样同步：

```bash
git fetch upstream
git checkout main
git merge upstream/main
```

如果你还想把同步后的 `main` 推回自己的 fork：

```bash
git push origin main
```

---

## 十一、本次修改对应的业务内容

本次提交并不是纯 Git 练习，而是一次真实代码修改：

文件：
- `scripts/setup_check.py`

改动目标：
- 在启动时自动初始化以下目录：
  - `vendor/`
  - `data/`
  - `reports/`
  - `scripts/tmp/`

这样做的意义：
- 让 `she-love-me` 仓库在干净环境下可以更顺畅地进入 Skill 流程
- 减少首次运行前手工创建目录的步骤
- 让环境检查脚本承担更多“初始化运行环境”的职责

---

## 十二、本次操作结果摘要

- 已完成代码修改
- 已创建本地提交：`492cc68`
- 已将 `origin` 设置为自己的 fork
- 已将原仓库配置为 `upstream`
- 已创建分支：`chore/init-runtime-dirs`
- 已推送到远端 fork
- 已可在 GitHub 页面直接发 PR

---

文档生成时间：2026-04-11
