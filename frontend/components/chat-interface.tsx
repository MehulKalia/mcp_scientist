"use client";

import type React from "react";

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
} from "lucide-react";

type Message = {
  role: "user" | "assistant" | "thinking" | "error";
  content: string;
  icon?: React.ReactNode;
  status?: "active" | "complete";
};

interface ChatInterfaceProps {
  onCandidateFound: () => void;
  onDiscoveryComplete: (protein: {
    name: string;
    description: string;
    efficiency: number;
  }) => void;
  onPdbUpdate: (pdbContent: string) => void;
}

const API_URL = "http://localhost:8000";

export default function ChatInterface({
  onCandidateFound,
  onDiscoveryComplete,
  onPdbUpdate,
}: ChatInterfaceProps) {
  const [inputValue, setInputValue] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [chatHistory, setChatHistory] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Welcome to ProteinFold. I'll help you discover novel proteins for your research. What would you like to discover today?",
    },
  ]);
  const [currentRequestId, setCurrentRequestId] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const chatContainerRef = useRef<HTMLDivElement>(null);

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
    // Close existing WebSocket connection
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Reset state
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

    // Reset scroll position
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = 0;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isProcessing) return;

    const userMessage = inputValue;
    setInputValue("");
    setIsProcessing(true);

    // Add user message to chat
    setChatHistory((prev) => [...prev, { role: "user", content: userMessage }]);

    try {
      // Make initial request to API
      const response = await fetch(`${API_URL}/api/chat/request`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ task: userMessage }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const requestId = data.requestId;
      setCurrentRequestId(requestId);

      // Connect to WebSocket
      const ws = new WebSocket(
        `ws://localhost:8000/api/chat/stream/${requestId}`
      );
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("WebSocket connection established");
      };

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        setChatHistory((prev) => [...prev, message]);

        // Check if this is a candidate found message
        if (message.content.includes("promising candidate")) {
          onCandidateFound();
        }

        // Check if message contains PDB data
        if (message.pdbContent) {
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

  const getIconForMessage = (content: string): React.ReactNode => {
    if (content.includes("Searching scientific")) {
      return <Search className="h-5 w-5 text-blue-500" />;
    } else if (content.includes("Searching internet")) {
      return <Globe className="h-5 w-5 text-blue-500" />;
    } else if (content.includes("Testing amino acid")) {
      return <Code className="h-5 w-5 text-blue-500" />;
    } else if (content.includes("Calculating binding")) {
      return <BarChart3 className="h-5 w-5 text-blue-500" />;
    }
    return null;
  };

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-neutral-200 p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-neutral-800">Protogen</h2>
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

      <div className="flex-1 overflow-auto p-4" ref={chatContainerRef}>
        {chatHistory.map((msg, index) => (
          <div
            key={index}
            className={`mb-4 flex ${
              msg.role === "user" ? "justify-end" : "justify-start"
            } ${msg.role === "thinking" ? "pl-8" : ""}`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                msg.role === "user"
                  ? "bg-blue-500 text-white"
                  : msg.role === "thinking"
                  ? "bg-neutral-100 text-neutral-800"
                  : msg.role === "error"
                  ? "bg-red-100 text-red-800"
                  : "bg-neutral-200 text-neutral-800"
              }`}
            >
              {msg.role === "thinking" && msg.icon && (
                <div className="mb-2 flex items-center gap-2">
                  {msg.icon}
                  <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                </div>
              )}
              <p className="whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="border-t border-neutral-200 p-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Describe the protein you want to discover..."
            className="flex-1 rounded-lg border border-neutral-200 px-4 py-2 focus:border-blue-500 focus:outline-none"
            disabled={isProcessing}
          />
          <button
            type="submit"
            disabled={isProcessing}
            className="rounded-lg bg-blue-500 px-4 py-2 text-white hover:bg-blue-600 disabled:bg-blue-300"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </form>
    </div>
  );
}
