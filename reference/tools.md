# 参考文档：依赖工具清单与安装指南

## 1. GitHub Trending CN

**安装**：WorkBuddy 技能市场搜索 "github-trending-cn"

**脚本路径**：`~/.workbuddy/skills/skill_2053082035554123776/scripts/github_trending.py`

**API 限制**：无 Token 每分钟 10 次，带 Token 每分钟 30 次。

## 2. 百度网盘 (bdpan)

**安装**：
```bash
bash ~/.workbuddy/skills/skill_2053081382993469440/scripts/install.sh
```

**登录**：
```bash
bash ~/.workbuddy/skills/skill_2053081382993469440/scripts/login.sh
```

**配置路径**：`E:/workbuk/.bdpan_config/`

## 3. 夸克网盘 (quark_cli)

**安装**：WorkBuddy 技能市场搜索 "quark-drive"

**登录**：
```bash
cd ~/.workbuddy/skills/quark-drive
QUARK_CONFIG_DIR="E:/workbuk/.quark_config" python3 scripts/quark_cli.py login
```

**配置路径**：`E:/workbuk/.quark_config/`

## 4. 微信公众号

**前置条件**：
- 已注册微信公众平台账号
- 在「开发 → 基本配置」获取 AppID 和 AppSecret
- 设置环境变量：`WECHAT_APPID` 和 `WECHAT_SECRET`

**发布技能**：使用 `mp-draft-push` 或 `wechat-publisher` 技能

## 5. 网站同步

**前置条件**：
- 网站仓库已 clone 到本地
- 已配置 Git SSH Key
- 已安装 `gh` CLI

## 6. 内容分发

**安装**：WorkBuddy 技能市场搜索 "content-repurposer"

## 常见问题

### Q: 百度网盘登录失败？
A: 检查 `E:/workbuk/.bdpan_config/` 目录是否存在。重新运行 `login.sh`。

### Q: 夸克网盘扫码后显示过期？
A: 使用 `uc_biz_str` 参数的完整格式 URL。参考 `quark-drive` 技能的 login 命令。

### Q: GitHub API 限流？
A: 设置 `GITHUB_TOKEN` 环境变量。

### Q: 微信推送失败？
A: 检查 `WECHAT_APPID` 和 `WECHAT_SECRET` 是否正确。确认公众号已获得「群发消息」权限。
