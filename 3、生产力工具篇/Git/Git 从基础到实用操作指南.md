# Git介绍及常见命令：从基础到实用操作指南

参考：[阮一峰-常用 Git 命令清单](https://www.ruanyifeng.com/blog/2015/12/git-cheat-sheet.html)

在日常开发中，版本控制工具是团队协作与代码管理的核心，而Git作为当前最流行的分布式版本控制系统，凭借其高效、灵活的特性，成为开发者必备技能。本文将从Git的核心概念入手，梳理常用操作命令，帮助新手快速上手。

## 一、Git核心概念：理解四大区域

在使用Git前，需先明确其核心工作流程涉及的四个关键区域，这是理解所有操作的基础：

- **Workspace（工作区）**：即本地电脑中实际编写代码的目录，是开发者直接操作的区域。
- **Index / Stage（暂存区）**：介于工作区与仓库区之间的“过渡区”，用于临时存放待提交的代码变更，可理解为“待提交清单”。
- **Repository（仓库区）**：本地仓库，存储了代码的完整版本历史，包括所有分支和提交记录，位于工作区下的 `.git`隐藏目录中。
- **Remote（远程仓库）**：托管在服务器上的仓库（如GitHub、GitLab），用于团队共享代码，实现多设备、多人协作同步。

Git的核心流程可简化为：**工作区修改 → 暂存区暂存 → 仓库区提交 → 远程仓库同步**。

## 二、Git常用命令：从基础到进阶

以下按“新建仓库→配置→文件操作→提交→分支→标签→远程同步→撤销”的逻辑，整理日常高频命令，所有命令均在终端（或Git Bash）中执行。

### 1. 新建代码库：初始化或克隆项目

无论是从零开始创建项目，还是从远程下载已有项目，都需通过以下命令初始化仓库：

```Bash
# 1. 在当前目录新建Git仓库（生成.git隐藏目录）
$ git init

# 2. 新建指定名称的目录，并初始化Git仓库
$ git init [project-name]  # 例：git init my-first-project

# 3. 从远程仓库下载完整项目（含历史记录）
$ git clone [url]  # 例：git clone https://github.com/username/repo-name.git
```

### 2. 配置Git：设置用户信息与偏好

Git的配置文件分为“全局配置”（所有项目生效）和“项目配置”（仅当前项目生效），核心是设置提交代码时的用户信息（需与远程仓库账号匹配）：

```Bash
# 1. 查看当前Git配置（全局+项目）
$ git config --list

# 2. 编辑配置文件（全局配置加--global，项目配置不加）
$ git config -e [--global]  # 会打开默认编辑器修改配置

# 3. 设置提交者姓名（全局生效）
$ git config --global user.name "[your-name]"  # 例：git config --global user.name "Zhang San"

# 4. 设置提交者邮箱（需与GitHub/GitLab注册邮箱一致）
$ git config --global user.email "[your-email]"  # 例：git config --global user.email "zhangsan@example.com"
```

### 3. 增加/删除文件：管理工作区与暂存区

代码修改后，需将变动文件加入暂存区（或删除暂存区文件），这是提交前的必要步骤：

```Bash
# 1. 添加指定文件到暂存区（可多个文件，空格分隔）
$ git add [file1] [file2] ...  # 例：git add index.html style.css

# 2. 添加指定目录到暂存区（含子目录所有文件）
$ git add [dir]  # 例：git add src/

# 3. 添加当前目录所有文件到暂存区（常用，注意末尾的“.”）
$ git add .

# 4. 分次添加同一文件的多处修改（每次修改需确认）
$ git add -p

# 5. 删除工作区文件，并将“删除操作”加入暂存区
$ git rm [file1] [file2] ...  # 例：git rm old-file.txt

# 6. 停止追踪指定文件（文件保留在工作区，仅从Git管理中移除）
$ git rm --cached [file]  # 例：git rm --cached log.txt（常用于忽略已追踪的日志文件）

# 7. 重命名文件，并将“改名操作”加入暂存区
$ git mv [old-name] [new-name]  # 例：git mv README.md README.en.md
```

### 4. 代码提交：将暂存区变更存入本地仓库

暂存区确认后，需通过“提交”操作将变更永久存入本地仓库，并填写提交说明（便于后续追溯）：

```Bash
# 1. 提交暂存区所有文件，附带提交说明（必填，清晰描述改动）
$ git commit -m "[message]"  # 例：git commit -m "feat: 添加登录页面样式"

# 2. 提交暂存区指定文件（需先git add，再指定文件）
$ git commit [file1] [file2] ... -m "[message]"

# 3. 跳过暂存区，直接提交工作区所有已追踪文件的变更
$ git commit -a  # 等价于“git add . + git commit”（未追踪文件不生效）

# 4. 提交时显示详细的diff对比（查看本次改动具体内容）
$ git commit -v

# 5. 修正上一次提交（覆盖上一次的commit信息或补充文件）
$ git commit --amend -m "[new-message]"  # 例：修正拼写错误时使用
```

### 5. 分支管理：并行开发的核心

分支是Git的强大特性，可实现“并行开发”（如主分支稳定运行，开发分支迭代新功能），常用命令如下：

```Bash
# 1. 查看本地所有分支（当前分支前带“*”）
$ git branch

# 2. 查看所有远程分支（需先git fetch）
$ git branch -r

# 3. 查看本地+远程所有分支
$ git branch -a

# 4. 新建分支（停留在当前分支，需后续切换）
$ git branch [branch-name]  # 例：git branch dev-feature

# 5. 新建分支并立即切换到该分支（常用，一步到位）
$ git checkout -b [branch-name]  # 例：git checkout -b dev-login

# 6. 切换到指定分支（分支需已存在）
$ git checkout [branch-name]  # 例：git checkout main

# 7. 切换到上一个分支（快速在两个分支间切换）
$ git checkout -

# 8. 合并指定分支到当前分支（如将开发分支合并到主分支）
$ git merge [branch-name]  # 例：在main分支执行git merge dev-feature

# 9. 删除本地分支（需先切换到其他分支，分支需已合并）
$ git branch -d [branch-name]  # 强制删除未合并分支用“-D”

# 10. 删除远程分支（需谨慎，删除后不可恢复）
$ git push origin --delete [branch-name]  # 例：git push origin --delete dev-old
```

### 6. 标签管理：标记重要版本

标签（Tag）用于标记重要的版本节点（如发布版本 `v1.0.0`），便于后续回滚或查看：

```Bash
# 1. 查看本地所有标签
$ git tag

# 2. 在当前提交新建标签（常用于发布版本）
$ git tag [tag-name]  # 例：git tag v1.0.0

# 3. 在指定提交新建标签（需先通过git log获取commit ID）
$ git tag [tag-name] [commit-id]  # 例：git tag v0.9.0 a1b2c3d

# 4. 删除本地标签
$ git tag -d [tag-name]  # 例：git tag -d v0.9.0

# 5. 推送指定标签到远程仓库
$ git push origin [tag-name]  # 例：git push origin v1.0.0

# 6. 推送所有本地标签到远程仓库
$ git push origin --tags
```

### 7. 远程同步：与远程仓库交互

多人协作或多设备同步时，需通过以下命令与远程仓库（如GitHub）交互：

```Bash
# 1. 查看所有已配置的远程仓库（显示名称和URL）
$ git remote -v

# 2. 查看指定远程仓库的详细信息（如分支映射）
$ git remote show [remote-name]  # 例：git remote show origin

# 3. 添加新的远程仓库（并命名，常用“origin”作为默认名称）
$ git remote add [shortname] [url]  # 例：git remote add origin https://github.com/username/repo.git

# 4. 从远程仓库下载最新变动（不合并到本地分支，需后续处理）
$ git fetch [remote-name]  # 例：git fetch origin

# 5. 从远程仓库拉取最新变动，并合并到当前本地分支（常用）
$ git pull [remote-name] [branch-name]  # 例：git pull origin main

# 6. 将本地指定分支推送到远程仓库（首次推送需加-u绑定分支）
$ git push [remote-name] [branch-name]  # 例：git push -u origin main（-u仅首次需要）

# 7. 强制推送本地分支到远程（覆盖远程，谨慎使用！适用于修正错误提交）
$ git push [remote-name] --force  # 例：git push origin --force

# 8. 推送所有本地分支到远程仓库
$ git push [remote-name] --all  # 例：git push origin --all
```

### 8. 撤销操作：修正错误或回滚版本

开发中难免出现错误操作（如提交错误文件、代码写错），Git提供多种撤销方式，需根据场景选择：

```Bash
# 1. 恢复暂存区的指定文件到工作区（撤销git add操作）
$ git checkout [file]  # 例：git checkout index.html

# 2. 恢复暂存区所有文件到工作区（撤销所有git add）
$ git checkout .

# 3. 重置暂存区指定文件（与上一次提交一致，工作区不变）
$ git reset [file]  # 例：git reset style.css

# 4. 彻底重置：暂存区+工作区均与上一次提交一致（删除未提交改动，谨慎！）
$ git reset --hard

# 5. 重置当前分支到指定提交（彻底回滚，需先通过git log获取commit ID）
$ git reset --hard [commit-id]  # 例：git reset --hard a1b2c3d

# 6. 暂存未提交的改动（临时保存，切换分支时用）
$ git stash  # 将工作区未提交的改动存入“暂存栈”

# 7. 恢复最近一次stash的改动（并删除stash记录）
$ git stash pop

# 8. 新建提交撤销指定历史提交（安全回滚，保留历史记录，推荐！）
$ git revert [commit-id]  # 例：git revert a1b2c3d（会生成新的commit抵消旧改动）
```

## 三、总结：日常操作核心流程

掌握上述命令后，日常开发的Git操作可归纳为以下核心流程：

1. **克隆/初始化仓库**：首次操作时，用 `git clone`下载远程项目，或 `git init`新建本地项目。
2. **修改与暂存**：编写代码后，用 `git add .`将所有变动加入暂存区。
3. **提交到本地仓库**：用 `git commit -m "说明"`将暂存区变更存入本地仓库。
4. **同步远程**：推送本地改动用 `git push origin 分支名`，拉取远程更新用 `git pull origin 分支名`。
5. **分支与标签**：开发新功能用 `git checkout -b 分支名`，发布版本用 `git tag 版本号`并推送标签。

Git的命令虽多，但日常高频使用的仅20-30个，熟练后可通过“组合命令”（如 `git fetch && git reset --hard origin/main`强制同步远程）提升效率。记住：分布式版本控制的核心是“追踪变更、便于协作”，多实践才能真正掌握！
