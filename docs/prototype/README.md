# TypeScript CLI 快速原型

这个目录包含了 TypeScript CLI 的快速原型代码，用于验证方案可行性。

## 结构

```
prototype/
├── ts-cli/           # TypeScript CLI 原型
│   ├── package.json
│   ├── tsconfig.json
│   └── src/
│       ├── index.ts
│       ├── app.tsx
│       └── components/
│
├── py-server/        # Python Server 原型
│   ├── server.py
│   └── requirements.txt
│
└── test-protocol/    # 协议测试
    └── test.ts
```

## 快速开始

### 1. 安装 TypeScript CLI 依赖

```bash
cd ts-cli
pnpm install
pnpm dev
```

### 2. 启动 Python Server

```bash
cd py-server
pip install -r requirements.txt
python server.py
```

### 3. 测试协议

```bash
cd test-protocol
ts-node test.ts
```
