"use client";

import { useState, useRef, useEffect } from "react";
import {
  Send,
  Search,
  Globe,
  Code,
  BarChart3,
  CheckCircle2,
  Loader2,
  Trash2,
  Settings,
  Dna,
  FileText,
  BarChart2,
  ChevronDown,
  ChevronRight,
  Copy,
  Check,
} from "lucide-react";
import { PromptMessage } from "./agent/PromptMessage";
import { ResponseMessage } from "./agent/ResponseMessage";
import { IterationHeader } from "./agent/IterationHeader";
import { AgentConfigModal } from "./agent/AgentConfigModal";
import { DesignResults } from "./agent/DesignResults";

interface Message {
  role: "user" | "assistant" | "system" | "error";
  content: string;
  timestamp?: string;
  type?:
    | "status"
    | "prompt"
    | "response"
    | "iteration"
    | "iteration_results"
    | "design_results"
    | "error";
  data?: {
    stage?: string;
    status?: string;
    iteration?: number;
    total_iterations?: number;
    sequence?: string;
    binding_score?: number;
    rationale?: string;
    results?: Array<{
      sequence: string;
      structure: any;
      binding_score: number;
    }>;
    error_type?: string;
    error_details?: string;
  };
  isCollapsed?: boolean;
}

interface ChatInterfaceProps {
  onCandidateFound: () => void;
  onDiscoveryComplete: (protein: {
    name: string;
    description: string;
    efficiency: number;
  }) => void;
  onPdbUpdate: (pdbContent: string, metadata?: Message["data"]) => void;
}

const API_URL = "http://localhost:8000";

export default function ChatInterface({
  onCandidateFound,
  onDiscoveryComplete,
  onPdbUpdate,
}: ChatInterfaceProps) {
  const [inputValue, setInputValue] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [agentConfig, setAgentConfig] = useState({ maxIterations: 3 });
  const [chatHistory, setChatHistory] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Welcome to ProteinFold. I'll help you discover novel proteins for your research. What would you like to discover today?",
    },
  ]);
  const [currentRequestId, setCurrentRequestId] = useState<string | null>(null);
  const [collapsedMessages, setCollapsedMessages] = useState<{
    [key: number]: boolean;
  }>({});
  const wsRef = useRef<WebSocket | null>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const [copiedMessageIndex, setCopiedMessageIndex] = useState<number | null>(
    null
  );

  // Scroll to bottom when chat updates
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }
  }, [chatHistory]);

  // Cleanup WebSocket connection
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const clearChat = () => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setChatHistory([
      {
        role: "assistant",
        content:
          "Welcome to ProteinFold. I'll help you discover novel proteins for your research. What would you like to discover today?",
      },
    ]);
    setCurrentRequestId(null);
    setIsProcessing(false);
    setInputValue("");

    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = 0;
    }
  };

  function parseAgentOutput(
    content: string,
    type?: string,
    data?: any
  ): Message {
    if (type === "status") {
      return {
        role: "system",
        content: content,
        type: "status",
        data: data,
      };
    }

    if (type === "prompt") {
      return {
        role: "system",
        content: "",
        type: "status",
        data: { stage: "processing" },
      };
    }

    if (type === "response") {
      return {
        role: "system",
        content: "",
        type: "status",
        data: { stage: "processing" },
      };
    }

    if (type === "iteration") {
      return {
        role: "system",
        content: `🔄 ${content}`,
        type: "iteration",
        data: data,
      };
    }

    if (type === "iteration_results") {
      return {
        role: "assistant",
        content: `📊 Iteration ${data.iteration} Results`,
        type: "iteration_results",
        data: { ...data, status: "completed" },
        isCollapsed: true,
      };
    }

    if (type === "design_results") {
      return {
        role: "assistant",
        content: `🎯 Design Results`,
        type: "design_results",
        data: { ...data, status: "completed" },
      };
    }

    if (type === "error") {
      return {
        role: "system",
        content: `❌ Error: ${content}`,
        type: "error",
        data: data,
      };
    }

    // Default case for backward compatibility
    return { role: "assistant", content: content };
  }

  const copyToClipboard = async (text: string, index: number) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedMessageIndex(index);
      setTimeout(() => setCopiedMessageIndex(null), 2000);
    } catch (err) {
      console.error("Failed to copy text: ", err);
    }
  };

  const formatTimestamp = () => {
    return new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isProcessing) return;

    const newMessage: Message = {
      role: "user",
      content: inputValue,
      timestamp: formatTimestamp(),
    };

    setChatHistory((prev) => [...prev, newMessage]);
    setInputValue("");
    setIsProcessing(true);

    try {
      const response = await fetch(`${API_URL}/api/chat/request`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          task: inputValue,
          config: agentConfig,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const requestId = data.requestId;
      setCurrentRequestId(requestId);

      const ws = new WebSocket(
        `ws://localhost:8000/api/chat/stream/${requestId}`
      );
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("WebSocket connection established");
      };

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        const parsedMessage = parseAgentOutput(
          message.content,
          message.type,
          message.data
        );
        setChatHistory((prev) => [...prev, parsedMessage]);

        if (parsedMessage.type === "design_results") {
          onCandidateFound();
          if (message.pdbContent) {
            onPdbUpdate(message.pdbContent, parsedMessage.data);
          }
        } else if (message.pdbContent) {
          onPdbUpdate(message.pdbContent);
        }
      };

      ws.onclose = () => {
        setIsProcessing(false);
        wsRef.current = null;
        setCurrentRequestId(null);
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        setChatHistory((prev) => [
          ...prev,
          {
            role: "error",
            content: "Connection error. Please try again.",
          },
        ]);
        setIsProcessing(false);
        wsRef.current = null;
        setCurrentRequestId(null);
      };
    } catch (error) {
      console.error("Error:", error);
      setChatHistory((prev) => [
        ...prev,
        {
          role: "error",
          content:
            "Failed to connect to the server. Please make sure the API server is running.",
        },
      ]);
      setIsProcessing(false);
    }
  };

  const handleConfigSave = async (config: { maxIterations: number }) => {
    try {
      const response = await fetch(`${API_URL}/api/chat/configure`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setAgentConfig(config);
    } catch (error) {
      console.error("Error updating agent configuration:", error);
      setChatHistory((prev) => [
        ...prev,
        {
          role: "error",
          content: "Failed to update agent configuration.",
        },
      ]);
    }
  };

  const handleStopAgent = async () => {
    if (!currentRequestId) return;

    try {
      const response = await fetch(
        `${API_URL}/api/chat/stop/${currentRequestId}`,
        {
          method: "POST",
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setChatHistory((prev) => [
        ...prev,
        {
          role: "system",
          content: "Agent process stopped by user request.",
        },
      ]);
      setIsProcessing(false);
    } catch (error) {
      console.error("Error stopping agent:", error);
      setChatHistory((prev) => [
        ...prev,
        {
          role: "error",
          content: "Failed to stop agent process.",
        },
      ]);
    }
  };

  const toggleCollapsed = (index: number) => {
    setCollapsedMessages((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  const renderMessage = (message: Message, index: number) => {
    const isCodeBlock = message.content.includes("```");
    const showCopyButton = isCodeBlock || message.data?.sequence;

    return (
      <div
        key={index}
        className={`flex flex-col space-y-2 p-4 ${
          message.role === "user" ? "bg-muted/50" : ""
        }`}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-2">
            {message.role === "user" ? (
              <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground">
                U
              </div>
            ) : message.role === "assistant" ? (
              <div className="h-8 w-8 rounded-full bg-secondary flex items-center justify-center text-secondary-foreground">
                A
              </div>
            ) : null}
            <div className="flex flex-col">
              <span className="font-medium">
                {message.role === "user" ? "You" : "Assistant"}
              </span>
              {message.timestamp && (
                <span className="text-xs text-muted-foreground">
                  {message.timestamp}
                </span>
              )}
            </div>
          </div>
          {showCopyButton && (
            <button
              onClick={() => copyToClipboard(message.content, index)}
              className="p-2 hover:bg-muted rounded-md transition-colors"
              title="Copy to clipboard"
            >
              {copiedMessageIndex === index ? (
                <Check className="h-4 w-4 text-green-500" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </button>
          )}
        </div>
        <div className="pl-10">
          {message.type === "status" && (
            <div className="flex items-center space-x-2 text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>{message.content}</span>
            </div>
          )}
          {message.type === "iteration" && (
            <div className="flex items-center space-x-2">
              <div className="h-4 w-4 rounded-full bg-blue-500 animate-pulse" />
              <span>{message.content}</span>
            </div>
          )}
          {message.type === "design_results" && message.data?.sequence && (
            <div className="flex flex-col space-y-2 bg-white border rounded-lg shadow-sm p-4">
              <div className="flex items-center space-x-2">
                <Dna className="h-5 w-5 text-blue-500" />
                <span className="font-medium text-lg">Design Results</span>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <div>
                    <span className="font-medium">Best Sequence: </span>
                    <code className="bg-gray-100 px-2 py-1 rounded text-sm">
                      {message.data.sequence}
                    </code>
                  </div>
                  {message.data.binding_score !== undefined && (
                    <div>
                      <span className="font-medium">Binding Score: </span>
                      <span className="text-green-600 font-mono">
                        {message.data.binding_score.toFixed(2)}
                      </span>
                    </div>
                  )}
                  {message.data.iteration && (
                    <div>
                      <span className="font-medium">Iteration: </span>
                      <span>{message.data.iteration}</span>
                    </div>
                  )}
                </div>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <FileText className="h-4 w-4 text-gray-500" />
                    <span className="font-medium">Rationale:</span>
                  </div>
                  <div className="text-sm text-gray-600 whitespace-pre-wrap bg-gray-50 p-2 rounded">
                    {message.data.rationale}
                  </div>
                </div>
              </div>
              <button
                onClick={onCandidateFound}
                className="mt-4 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 animate-pulse"
              >
                Inspect Latest Design
              </button>
            </div>
          )}
          {message.type === "iteration_results" && message.data?.results && (
            <div className="flex flex-col space-y-2 bg-white border rounded-lg shadow-sm p-4">
              <button
                onClick={() => toggleCollapsed(index)}
                className="flex items-center space-x-2 text-left hover:bg-gray-50 p-2 rounded-lg -m-2"
              >
                {collapsedMessages[index] ? (
                  <ChevronRight className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
                <BarChart2 className="h-5 w-5 text-purple-500" />
                <span className="font-medium">{message.content}</span>
                {isProcessing && (
                  <Loader2 className="h-4 w-4 animate-spin ml-2 text-purple-500" />
                )}
              </button>

              {!collapsedMessages[index] && message.data.results && (
                <div className="pl-7 mt-2">
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Sequence
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Binding Score
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {message.data.results.map((result, idx) => (
                          <tr key={idx}>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <code className="bg-gray-100 px-2 py-1 rounded">
                                {`Sequence ${idx + 1}`}
                              </code>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-green-600">
                              {result.binding_score.toFixed(2)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
          {!message.type && (
            <div className="prose prose-sm max-w-none">{message.content}</div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-neutral-200 p-4 sticky top-0 bg-white z-10">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-neutral-800">Protogen</h2>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsConfigOpen(true)}
              className="rounded-lg bg-gray-50 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100"
              title="Configure agent"
            >
              <div className="flex items-center gap-2">
                <Settings className="h-4 w-4" />
                <span>Configure</span>
              </div>
            </button>
            <button
              onClick={clearChat}
              className="rounded-lg bg-red-50 px-3 py-1.5 text-sm text-red-600 hover:bg-red-100"
              title="Clear chat and reset connection"
            >
              <div className="flex items-center gap-2">
                <Trash2 className="h-4 w-4" />
                <span>Clear Chat</span>
              </div>
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto p-4" ref={chatContainerRef}>
        {chatHistory.map((msg, index) => (
          <div key={index} className="mb-4">
            {renderMessage(msg, index)}
          </div>
        ))}
      </div>

      <div className="border-t border-neutral-200 p-4 sticky bottom-0 bg-white">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Enter your protein design task..."
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {isProcessing ? (
            <button
              type="button"
              onClick={handleStopAgent}
              className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
            >
              Stop
            </button>
          ) : (
            <button
              type="submit"
              disabled={!inputValue.trim()}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
            >
              <Send className="h-5 w-5" />
            </button>
          )}
        </form>
      </div>

      <AgentConfigModal
        isOpen={isConfigOpen}
        onClose={() => setIsConfigOpen(false)}
        onSave={handleConfigSave}
        currentConfig={agentConfig}
      />
    </div>
  );
}
