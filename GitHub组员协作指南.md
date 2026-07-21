# GitHub 组员协作操作指南

> 适用仓库：`limark-00/200-1`
>
> 标准流程：接受 Collaborator 邀请 → 配置自己的 SSH key → clone → 创建功能分支 → 修改并测试 → commit → push → 创建 Pull Request → 等待仓库所有者审核。

## 开始前必须知道的三条规则

1. **绝不在 `main` 上直接开发或 push**；每项工作都从自己的功能分支开始，并通过 Pull Request 合并。
2. **绝不提交真实敏感信息**，包括 `.env`、PEM/KEY 文件、密码、令牌（token）或任何真实私钥。
3. **不要贸然执行破坏性 Git 命令**。执行前先查看 `git status`；不确定时先询问仓库所有者，不要猜测。

预期：所有成员都在自己的分支协作，`main` 只接收审核后的修改。若已在 `main` 做了修改，先停止操作并联系仓库所有者确认如何处理。

## 第一次使用：安装和配置 Git

每位组员使用自己的 GitHub 账号和自己的 Git 身份信息；不要填写别人的姓名或邮箱。先确认 Git 已安装，再设置身份。

```bash
git --version
git config --global user.name "你的姓名"
git config --global user.email "你的邮箱"
git config --global --list
```

预期：第一条会显示 Git 版本，最后一条能看到刚设置的 `user.name` 和 `user.email`。若提示找不到 `git`，请按自己的操作系统安装 Git 后重新打开终端再执行。

## 第一次使用：配置自己的 SSH key

每位组员必须用自己的 GitHub 账号认证。生成密钥时可在提示处直接按 Enter 使用默认路径；只把 `.pub` 公钥复制到自己 GitHub 的 `Settings → SSH and GPG keys`。`id_ed25519` 是私钥，绝不能分享、截图或提交。

Windows PowerShell：

```powershell
ssh-keygen -t ed25519 -C "你的邮箱"
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub | Set-Clipboard
ssh -T git@github.com
```

macOS：

```bash
ssh-keygen -t ed25519 -C "你的邮箱"
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
pbcopy < ~/.ssh/id_ed25519.pub
ssh -T git@github.com
```

Ubuntu：

```bash
sudo apt update
sudo apt install -y git openssh-client
ssh-keygen -t ed25519 -C "你的邮箱"
cat ~/.ssh/id_ed25519.pub
ssh -T git@github.com
```

预期：将复制或显示出的以 `ssh-ed25519` 开头的**公钥**粘贴到 GitHub 后，`ssh -T git@github.com` 会显示已成功认证到 GitHub 的提示。若认证失败，检查是否添加的是 `.pub` 公钥、当前登录的是自己的 GitHub 账号，再重新执行测试；不要把私钥发给任何人。

## 第一次下载项目

接受仓库的 Collaborator 邀请后，在你准备存放代码的目录执行 clone；这会在本机创建 `200-1` 文件夹。

```bash
git clone git@github.com:limark-00/200-1.git
cd 200-1
git status --short --branch
```

预期：最后一条显示当前分支及工作区状态，且没有报错。若 clone 提示权限不足，先确认已接受邀请并完成 SSH 认证；不要改用别人的账号或密钥。

## 每次开始工作前：拉取最新代码

开始新工作前先回到 `main` 并快进拉取远程最新版本。其他组员 push 后不会自动更新到你的本地文件，每个人都必须主动运行 `git pull`。如果是继续已有功能分支，再把最新 `main` 合入该分支；若是开始新任务，跳过后两条命令，随后按“创建自己的功能分支”章节新建分支。

```bash
git switch main
git pull --ff-only origin main
git switch feature/姓名-功能
git merge main
```

预期：`main` 更新为远程最新代码，或显示 `Already up to date.`；继续任务时，功能分支也会包含最新 `main`。若 `--ff-only` 拒绝拉取或 `git merge main` 出现冲突，先执行 `git status`，保留本地工作并按“常见问题与恢复”处理或询问仓库所有者，切勿强行覆盖。

## 创建自己的功能分支

从已更新的 `main` 创建一条独立分支。把 `姓名-功能` 替换为实际内容，例如 `feature/zhangsan-login-ui`；不要在 `main` 修改。

```bash
git switch -c feature/姓名-功能
git branch --show-current
```

预期：第二条显示 `feature/姓名-功能`。若显示 `main` 或创建失败，停止修改并检查当前目录和 `git status`，必要时询问仓库所有者。

## 修改后检查代码

完成修改并在本地运行项目或相关测试后，先核对变更范围，确保只包含本次任务。

```bash
git status
git diff
```

预期：`git status` 列出待处理文件，`git diff` 显示尚未暂存的具体改动。若发现无关文件、敏感信息或不认识的改动，不要提交；先移除或联系产生该改动的成员确认。

## 提交本次修改

只暂存本次任务需要的文件，不要使用会把所有文件一并加入的操作。暂存后再次检查，再用清晰的中文或英文说明创建提交。

```bash
git add 具体文件路径
git diff --cached
git commit -m "描述本次修改"
```

预期：`git diff --cached` 只显示预期内容，提交成功后会显示新提交编号。若暂存了错误文件，可先执行 `git restore --staged 文件路径` 再检查；若提交被检查工具拒绝，按提示修复后重新提交。

## 上传自己的功能分支

首次上传当前功能分支时使用下面命令。上传功能分支不会修改 `main`；同一分支后续提交只需执行 `git push`。

```bash
git push -u origin feature/姓名-功能
```

预期：终端显示分支已推送并设置上游分支。若提示认证或权限错误，检查 SSH 认证和 Collaborator 邀请；若被拒绝，不要尝试 push 到 `main`，先联系仓库所有者。

## 在 GitHub 创建 Pull Request

push 成功后立即在 GitHub 网页创建 PR：

1. 打开仓库页面。
2. 点击 `Compare & pull request`。
3. 确认 base branch 是 `main`，compare branch 是自己的功能分支。
4. 写清楚改了什么、为什么修改，以及如何测试。
5. 创建 Pull Request，然后等待 `@limark-00` 审核。
6. 未经所有者批准不要点击 merge。

预期：PR 页面显示从你的功能分支合并到 `main`，并处于等待审核状态。若 base 或 compare 选错，先在网页改正再创建；若不确定是否可以合并，保持 PR 打开并等待所有者回复。

## 根据审核意见继续修改

收到审核意见后，在原功能分支修正并重新 push；无需新建 PR，已有 Pull Request 会在 push 后自动更新。

```bash
git switch feature/姓名-功能
git status
git add 具体文件路径
git commit -m "根据审核意见修改"
git push
```

预期：push 成功后，原 PR 会自动出现新的提交。若发现当前不在目标分支或有未预期改动，先停止并查看 `git status`，确认后再继续。

## 合并后同步并清理分支

PR 被合并后，在本地同步 `main`，再删除已完成的功能分支及其远程分支。代码更新后，正在运行的 Python 进程不会自动加载新文件，必须重启该进程。

```bash
git switch main
git pull --ff-only origin main
git branch -d feature/姓名-功能
git push origin --delete feature/姓名-功能
```

预期：本地 `main` 包含合并后的代码，功能分支被删除。若 `git branch -d` 拒绝删除，先确认 PR 已合并且分支没有未合并工作；不确定时保留分支并询问仓库所有者。若远程删除提示 `remote ref does not exist`，确认 PR 已合并后可安全忽略：GitHub 可能已自动删除远程分支。

## 巴法云私钥和本地配置

巴法云私钥仅在自己的本地终端临时设置；每位组员使用自己的凭据，绝不写进代码、文档、提交记录或 `.env` 文件。Windows PowerShell 可这样运行：

```powershell
cd smart-home-console
$env:BEMFA_UID="你自己的巴法云私钥"
python app.py
```

macOS 和 Ubuntu 可这样运行：

```bash
cd smart-home-console
export BEMFA_UID="你自己的巴法云私钥"
python3 app.py
```

完成上方任一平台命令后，当前已位于 `smart-home-console` 目录；提交前直接在该当前目录检查暂存区和忽略规则：

```bash
git status
git diff --cached
git check-ignore -v .env
```

预期：敏感文件不出现在待提交或暂存列表中，`.env` 若已被忽略会显示匹配它的规则。若真实私钥曾进入任何提交，即使后来删掉文件，也要立即轮换该私钥并通知仓库所有者处理历史风险。

## 常见问题与恢复

合并时若发生冲突，Git 会在文件中标出 `<<<<<<<`、`=======`、`>>>>>>>`：前后两段分别是不同来源的内容。手动保留正确内容并删除这三类标记后，检查程序，再完成合并。

```bash
git status
git add 已解决冲突的文件
git commit
```

预期：提交完成后合并结束。若暂时无法判断应保留哪段内容，先中止合并，不要随意选择。

```bash
git merge --abort
```

预期：工作区回到本次合并前的状态。若该命令失败，保留现场，执行 `git status` 并联系仓库所有者。

要撤销尚未提交的单个文件改动，或把已暂存文件移出暂存区，可使用：

```bash
git restore 文件路径
git restore --staged 文件路径
```

预期：第一条丢弃该文件未暂存的改动，第二条仅取消暂存、不会删除文件改动。若改动可能有用，先复制备份或询问所有者；不要用 `git reset --hard`，它会丢弃未提交工作，不属于新手协作流程。

若一个已经共享的提交有问题，在专用 revert 分支创建反向提交，不改写历史，也绝不直接推送 `main`：

```bash
git switch main
git pull --ff-only origin main
git switch -c revert/描述
git log --oneline
git revert 提交编号
git push -u origin revert/描述
```

预期：会在 `revert/描述` 分支生成撤销目标提交的新提交并推送。随后在 GitHub 为该分支创建 Pull Request，交由仓库所有者审核后再合并。若 revert 出现冲突，按上面的冲突步骤处理或询问仓库所有者。

若只想安全查看旧版本，先从旧提交创建一个检查分支，不要直接改写当前历史：

```bash
git log --oneline
git switch -c restore/检查旧版本 提交编号
```

预期：你会进入 `restore/检查旧版本` 分支查看旧代码。若提交编号无效，重新从 `git log --oneline` 复制完整或足够长的编号。

## 仓库所有者操作

仓库所有者应在 GitHub 依次完成以下维护：

- 通过 `Settings → Collaborators → Add people` 邀请组员。
- 为 `main` 启用规则集，要求 Pull Request、至少 1 个批准，并启用 `Require review from Code Owners`。
- 需要所有者作为代码所有者审核时，添加 `.github/CODEOWNERS`，内容为 `* @limark-00`。CODEOWNERS 只会请求代码所有者审核，本身不会强制仅所有者批准；必须同时由规则集启用必需 PR 审核和 `Require review from Code Owners`。
- 合并前检查修改文件、代码 diff、测试证据和是否包含敏感信息。
- 合并后的修改有问题时，使用 GitHub 的 `Revert` 操作或 `git revert`，避免改写共享历史。

预期：所有 `main` 修改都有 PR、审核记录和可追踪的测试说明。若规则设置或权限配置不确定，先查阅 GitHub 设置页面并暂缓合并。

## 每日命令速查

以下仅保留每日最少命令；遇到异常请回到对应详细章节处理。

拉取最新 `main`（详见[每次开始工作前：拉取最新代码](#每次开始工作前拉取最新代码)）：

```bash
git switch main
git pull --ff-only origin main
```

创建分支（详见[创建自己的功能分支](#创建自己的功能分支)）：

```bash
git switch -c feature/姓名-功能
```

提交修改（详见[提交本次修改](#提交本次修改)）：

```bash
git add 具体文件路径
git commit -m "描述本次修改"
```

上传分支（详见[上传自己的功能分支](#上传自己的功能分支)）：

```bash
git push -u origin feature/姓名-功能
```

合并后同步（详见[合并后同步并清理分支](#合并后同步并清理分支)）：

```bash
git switch main
git pull --ff-only origin main
```

预期：每天从更新后的 `main` 开始，在自己的功能分支提交并 push。若任一命令报错，不要跳过详细检查或改推 `main`，回到链接章节按提示处理。

## 提交前最终检查清单

- [ ] 当前分支不是 `main`，并且名称对应本次任务。
- [ ] 已运行项目或相关测试，并在 PR 中写明测试方式和结果。
- [ ] `git status` 和 `git diff --cached` 只包含本次任务文件。
- [ ] 没有 `.env`、私钥、PEM/KEY、密码、令牌或真实凭据。
- [ ] 已 push 自己的功能分支，已准备好创建或更新 PR 并等待 `@limark-00` 审核。

预期：全部勾选后才提交 PR 审核。若有任何一项无法确认，先不要合并，询问仓库所有者。
