# Task 1.1: Monorepo 初始化

## 背景
我们需要将 nano-code 项目转换为 monorepo 结构，以支持 TypeScript CLI 和 Python Core 并存。

## 目标
创建 monorepo 根目录结构，配置 pnpm workspace 和 TypeScript。

## 任务步骤

### 1. 创建根目录配置文件

**package.json** (monorepo 根):
```json
{
  "name": "nano-code",
  "version": "0.1.0",
  "private": true,
  "description": "A mini coding agent built with LangGraph",
  "scripts": {
    "build": "pnpm -r build",
    "test": "pnpm -r test",
    "lint": "pnpm -r lint"
  },
  "devDependencies": {
    "typescript": "^5.3.0"
  },
  "packageManager": "pnpm@9.0.0",
  "engines": {
    "node": ">=20.0.0"
  }
}
```

**pnpm-workspace.yaml**:
```yaml
packages:
  - 'packages/*'
```

**tsconfig.base.json**:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  }
}
```

### 2. 创建 packages/cli 目录结构

```
packages/cli/
├── package.json
├── tsconfig.json
└── src/
    └── index.ts
```

**packages/cli/package.json**:
```json
{
  "name": "@nano-code/cli",
  "version": "0.1.0",
  "description": "Nano Code CLI",
  "type": "module",
  "bin": {
    "nano-code": "./dist/index.js"
  },
  "scripts": {
    "build": "tsc",
    "dev": "tsc --watch",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "ink": "^4.4.1",
    "react": "^18.2.0"
  },
  "devDependencies": {
    "@types/node": "^20.11.0",
    "@types/react": "^18.2.0",
    "typescript": "^5.3.0"
  }
}
```

**packages/cli/tsconfig.json**:
```json
{
  "extends": "../../tsconfig.base.json",
  "compilerOptions": {
    "outDir": "./dist",
    "rootDir": "./src"
  },
  "include": ["src/**/*"]
}
```

**packages/cli/src/index.ts**:
```typescript
#!/usr/bin/env node
console.log('Nano Code CLI - Coming soon...');
```

### 3. 更新 .gitignore

添加:
```
# Node
node_modules/
dist/
*.tsbuildinfo

# pnpm
.pnpm-store/
```

## 验证步骤

1. 安装依赖:
```bash
pnpm install
```

2. 构建 CLI:
```bash
pnpm --filter @nano-code/cli build
```

3. 运行 CLI:
```bash
node packages/cli/dist/index.js
# 应该输出: Nano Code CLI - Coming soon...
```

## 注意事项

1. 不要修改 `src/` 目录下的任何 Python 文件
2. 保持 `pyproject.toml` 不变
3. 只在根目录和 `packages/` 目录下工作

## 预期产出

- 根目录下的 3 个配置文件
- `packages/cli/` 目录结构
- 可以成功 `pnpm install` 和 `pnpm build`
