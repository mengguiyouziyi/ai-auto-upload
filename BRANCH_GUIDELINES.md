# 🌿 分支管理指南

## 📋 分支策略

本项目采用 **Git Flow** 轻量版分支管理策略：

### 🏗️ 主要分支

#### `master` (生产分支)
- **用途**: 生产环境代码，始终保持稳定可运行状态
- **来源**: 仅接受来自 `develop` 分支的合并
- **保护**: 设置为GitHub默认分支，禁止直接推送
- **状态**: ✅ 当前包含完整的AI媒体平台功能

#### `develop` (开发分支)
- **用途**: 集成开发功能，最新的开发代码
- **来源**: 所有功能分支最终合并到此
- **状态**: ✅ 最新的开发版本

#### `002-image-1` (历史分支)
- **用途**: 保留历史版本，作为参考
- **状态**: 🔄 已被master分支替代，可考虑删除

### 🚀 功能分支命名规范

```
feature/功能名称     # 新功能开发
bugfix/问题描述      # Bug修复
hotfix/紧急修复      # 生产环境紧急修复
release/版本号      # 发布准备
```

## 🔄 工作流程

### 1. 新功能开发
```bash
# 从develop创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/新功能名称

# 开发完成后
git add .
git commit -m "feat: 添加新功能"
git push origin feature/新功能名称

# 创建Pull Request到develop分支
```

### 2. Bug修复
```bash
# 从develop创建修复分支
git checkout develop
git checkout -b bugfix/问题描述

# 修复完成后
git add .
git commit -m "fix: 修复问题描述"
git push origin bugfix/问题描述

# 创建Pull Request到develop分支
```

### 3. 发布到生产
```bash
# 将develop合并到master
git checkout master
git pull origin master
git merge develop --no-ff
git push origin master

# 创建发布标签
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

## 📊 当前分支状态

| 分支 | 用途 | 状态 | 最后更新 |
|------|------|------|----------|
| `master` | 🏭 生产环境 | ✅ 稳定 | 最新 |
| `develop` | 🔧 开发环境 | ✅ 活跃 | 最新 |
| `002-image-1` | 📚 历史版本 | 🔄 过时 | 可归档 |

## 🛡️ 分支保护规则

### `master` 分支保护
- ✅ 禁止直接推送
- ✅ 需要Pull Request审查
- ✅ 需要CI/CD通过
- ✅ 设置为GitHub默认分支

### `develop` 分支保护
- ⚠️ 建议通过Pull Request合并
- ⚠️ 确保测试通过

## 🏷️ 标签管理

### 版本标签规范
```
v主版本号.次版本号.修订号
v1.0.0  # 重大版本更新
v1.1.0  # 新功能发布
v1.1.1  # Bug修复版本
```

### 创建标签
```bash
# 创建轻量标签
git tag v1.0.0

# 创建带注释的标签
git tag -a v1.0.0 -m "Release version 1.0.0"

# 推送标签
git push origin v1.0.0
```

## 🔧 Git配置

### 全局配置
```bash
git config --global user.name "你的名字"
git config --global user.email "你的邮箱"
```

### 本地配置
```bash
git config user.name "你的名字"
git config user.email "你的邮箱"
```

## 📝 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
feat: 新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建工具或辅助工具的变动
```

### 示例
```bash
feat: 添加AI视频生成功能
fix: 修复抖音发布接口超时问题
docs: 更新部署文档
refactor: 重构用户认证模块
```

## 🚨 注意事项

1. **永远不要直接在master分支开发**
2. **功能分支名称要描述清楚**
3. **提交信息要符合规范**
4. **推送前先拉取最新代码**
5. **及时删除已合并的分支**

## 🔍 分支查看命令

```bash
# 查看所有分支
git branch -a

# 查看分支最后提交
git branch -v

# 查看分支合并图
git log --oneline --graph --decorate --all

# 查看远程分支
git remote show origin
```

---

📖 更多信息请参考 [Pro Git Book](https://git-scm.com/book)