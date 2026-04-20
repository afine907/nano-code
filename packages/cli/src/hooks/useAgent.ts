import { useState, useCallback, useEffect, useRef } from "react";
import { AgentClient } from "../client/rpc.js";
import type { StreamEvent, Message, Config } from "../client/types.js";

export interface UseAgentReturn {
  // 状态
  messages: Message[];
  isStreaming: boolean;
  status: "idle" | "thinking" | "executing" | "error";
  currentTool: { name: string; args: Record<string, unknown> } | undefined;
  model: string;
  config: Config | null;
  error: string | undefined;

  // 方法
  sendMessage: (prompt: string) => Promise<void>;
  clearMessages: () => void;
  reconnect: () => Promise<void>;
}

/**
 * Agent Hook
 *
 * 管理与 Python Agent 的通信
 */
export function useAgent(): UseAgentReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [status, setStatus] = useState<"idle" | "thinking" | "executing" | "error">("idle");
  const [currentTool, setCurrentTool] = useState<
    { name: string; args: Record<string, unknown> } | undefined
  >();
  const [model, setModel] = useState("gpt-4o-mini");
  const [config, setConfig] = useState<Config | null>(null);
  const [error, setError] = useState<string | undefined>();

  const clientRef = useRef<AgentClient | null>(null);
  const currentResponseRef = useRef<string>("");

  // 初始化客户端
  useEffect(() => {
    const initClient = async () => {
      try {
        const client = new AgentClient();
        await client.connect();
        clientRef.current = client;

        // 获取配置
        const cfg = await client.getConfig();
        setConfig(cfg);
        setModel(cfg.model);

        // 监听流式事件
        client.on("stream", handleStreamEvent);

        console.log("Agent client connected");
      } catch (err) {
        setError(`Failed to connect: ${err}`);
        setStatus("error");
      }
    };

    initClient();

    return () => {
      clientRef.current?.close();
    };
  }, []);

  // 处理流式事件
  const handleStreamEvent = useCallback((event: StreamEvent) => {
    switch (event.type) {
      case "thinking":
        setStatus("thinking");
        break;

      case "tool_call":
        setStatus("executing");
        if (event.metadata?.toolName) {
          setCurrentTool({
            name: event.metadata.toolName,
            args: event.metadata.toolArgs || {},
          });
        }
        break;

      case "tool_result":
        setCurrentTool(undefined);
        break;

      case "response":
        // 追加响应内容
        currentResponseRef.current += event.content;

        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.role === "assistant") {
            return [...prev.slice(0, -1), { ...last, content: currentResponseRef.current }];
          }
          return [
            ...prev,
            {
              role: "assistant" as const,
              content: event.content,
              timestamp: new Date(),
            },
          ];
        });
        break;

      case "done":
        setIsStreaming(false);
        setStatus("idle");
        setCurrentTool(undefined);
        currentResponseRef.current = "";
        break;

      case "error":
        setIsStreaming(false);
        setStatus("error");
        setError(event.content);
        setCurrentTool(undefined);
        currentResponseRef.current = "";
        break;
    }
  }, []);

  // 发送消息
  const sendMessage = useCallback(
    async (prompt: string) => {
      if (!clientRef.current || isStreaming) {
        return;
      }

      // 添加用户消息
      const userMessage: Message = {
        role: "user",
        content: prompt,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);

      // 重置状态
      setIsStreaming(true);
      setStatus("thinking");
      setError(undefined);
      currentResponseRef.current = "";

      try {
        await clientRef.current.stream(prompt);
      } catch (err) {
        setIsStreaming(false);
        setStatus("error");
        setError(`Failed to send message: ${err}`);
      }
    },
    [isStreaming]
  );

  // 清空消息
  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(undefined);
  }, []);

  // 重新连接
  const reconnect = useCallback(async () => {
    clientRef.current?.close();
    clientRef.current = null;

    try {
      const client = new AgentClient();
      await client.connect();
      clientRef.current = client;
      client.on("stream", handleStreamEvent);

      const cfg = await client.getConfig();
      setConfig(cfg);
      setModel(cfg.model);
      setStatus("idle");
      setError(undefined);
    } catch (err) {
      setError(`Failed to reconnect: ${err}`);
      setStatus("error");
    }
  }, [handleStreamEvent]);

  return {
    messages,
    isStreaming,
    status,
    currentTool,
    model,
    config,
    error,
    sendMessage,
    clearMessages,
    reconnect,
  };
}
