"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { useToast } from "@/hooks/use-toast"
import Header from "@/components/header"
import ProteinViewer from "@/components/protein-viewer"
import DiscoverySummary from "@/components/discovery-summary"
import { Search, Globe, Code, BarChart3, CheckCircle2, Loader2, Send } from "lucide-react"

// Simulation states
type SimulationState = "initial" | "typing" | "processing" | "candidate" | "complete"

export default function ProteinDiscoverySimulation() {
  const [simulationState, setSimulationState] = useState<SimulationState>("initial")
  const [showViewer, setShowViewer] = useState(true)
  const [currentProtein, setCurrentProtein] = useState<{
    name: string
    description: string
    efficiency: number
  } | null>(null)
  const { toast } = useToast()

  // For typing simulation
  const [inputValue, setInputValue] = useState("")
  const [isTyping, setIsTyping] = useState(false)
  const fullQuery = "I need a protein that can bind to the ACE2 receptor with high affinity to block SARS-CoV-2 entry."
  const typingSpeed = 50 // ms per character

  // For chat messages
  const [chatHistory, setChatHistory] = useState<
    {
      role: "user" | "assistant" | "thinking"
      content: string
      icon?: React.ReactNode
      status?: "active" | "complete"
    }[]
  >([
    {
      role: "assistant",
      content: "Welcome to Protein Discovery Lab. I'll help you discover novel proteins for your research. What would you like to discover today?",
    },
  ])

  // Start the simulation
  useEffect(() => {
    // Wait 1 second before starting to type
    const initialDelay = setTimeout(() => {
      setSimulationState("typing")
      setIsTyping(true)
    }, 1000)

    return () => clearTimeout(initialDelay)
  }, [])

  // Handle typing animation
  useEffect(() => {
    if (!isTyping) return

    if (inputValue.length < fullQuery.length) {
      const typingTimer = setTimeout(() => {
        setInputValue(fullQuery.substring(0, inputValue.length + 1))
      }, typingSpeed)
      return () => clearTimeout(typingTimer)
    } else {
      // Finished typing, submit the query
      setIsTyping(false)
      const submitTimer = setTimeout(() => {
        setChatHistory([
          ...chatHistory,
          { role: "user", content: fullQuery },
          {
            role: "assistant",
            content: "I'll analyze your request for a protein that can bind to the ACE2 receptor to block SARS-CoV-2 entry. Let me think through this step by step.",
          },
        ])
        setInputValue("")
        setSimulationState("processing")

        // Add thinking messages with delays
        setTimeout(() => {
          setChatHistory((prev) => [
            ...prev,
            {
              role: "thinking",
              content: "Searching scientific literature for ACE2 receptor binding proteins...",
              icon: <Search className="h-5 w-5 text-blue-500" />,
              status: "active",
            },
          ])

          setTimeout(() => {
            setChatHistory((prev) => {
              const updated = [...prev]
              const thinkingIndex = updated.findIndex(
                (msg) => msg.role === "thinking" && msg.content.includes("Searching scientific")
              )
              if (thinkingIndex !== -1) {
                updated[thinkingIndex] = {
                  ...updated[thinkingIndex],
                  status: "complete",
                }
              }
              return [
                ...updated,
                {
                  role: "thinking",
                  content: "Found 37 papers on ACE2 binding proteins. Analyzing structural similarities...",
                  icon: <Search className="h-5 w-5 text-green-500" />,
                },
              ]
            })

            setTimeout(() => {
              setChatHistory((prev) => [
                ...prev,
                {
                  role: "thinking",
                  content: "Searching internet databases for recent discoveries and preprints...",
                  icon: <Globe className="h-5 w-5 text-blue-500" />,
                  status: "active",
                },
              ])

              setTimeout(() => {
                setChatHistory((prev) => {
                  const updated = [...prev]
                  const thinkingIndex = updated.findIndex(
                    (msg) => msg.role === "thinking" && msg.content.includes("Searching internet")
                  )
                  if (thinkingIndex !== -1) {
                    updated[thinkingIndex] = {
                      ...updated[thinkingIndex],
                      status: "complete",
                    }
                  }
                  return [
                    ...updated,
                    {
                      role: "thinking",
                      content: "Identified 3 promising candidate structures from recent research.",
                      icon: <Globe className="h-5 w-5 text-green-500" />,
                    },
                  ]
                })

                setTimeout(() => {
                  setChatHistory((prev) => [
                    ...prev,
                    {
                      role: "thinking",
                      content: "Testing amino acid sequences for optimal ACE2 binding...",
                      icon: <Code className="h-5 w-5 text-blue-500" />,
                      status: "active",
                    },
                  ])

                  setTimeout(() => {
                    setChatHistory((prev) => {
                      const updated = [...prev]
                      const thinkingIndex = updated.findIndex(
                        (msg) => msg.role === "thinking" && msg.content.includes("Testing amino acid")
                      )
                      if (thinkingIndex !== -1) {
                        updated[thinkingIndex] = {
                          ...updated[thinkingIndex],
                          status: "complete",
                        }
                      }
                      return [
                        ...updated,
                        {
                          role: "thinking",
                          content:
                            "Modified sequence MYKRWVLLLLFAMVLGSTQGVPFECANLMRLKDD... shows promising binding characteristics.",
                          icon: <Code className="h-5 w-5 text-green-500" />,
                        },
                      ]
                    })

                    // Show candidate notification
                    toast({
                      title: "A new candidate is ready",
                      description: "View Update?",
                      action: (
                        <button
                          onClick={() => setShowViewer(true)}
                          className="rounded bg-primary px-3 py-1 text-primary-foreground hover:bg-primary/90"
                        >
                          View
                        </button>
                      ),
                    })
                    setSimulationState("candidate")

                    setTimeout(() => {
                      setChatHistory((prev) => [
                        ...prev,
                        {
                          role: "thinking",
                          content: "Calculating binding efficiency and stability metrics...",
                          icon: <BarChart3 className="h-5 w-5 text-blue-500" />,
                          status: "active",
                        },
                      ])

                      setTimeout(() => {
                        setChatHistory((prev) => {
                          const updated = [...prev]
                          const thinkingIndex = updated.findIndex(
                            (msg) => msg.role === "thinking" && msg.content.includes("Calculating binding")
                          )
                          if (thinkingIndex !== -1) {
                            updated[thinkingIndex] = {
                              ...updated[thinkingIndex],
                              status: "complete",
                            }
                          }
                          return [
                            ...updated,
                            {
                              role: "thinking",
                              content: "Final protein has 96.3% binding efficiency and excellent stability metrics.",
                              icon: <BarChart3 className="h-5 w-5 text-green-500" />,
                            },
                            {
                              role: "assistant",
                              content:
                                "I've successfully discovered a protein that can bind to the ACE2 receptor with high affinity to block SARS-CoV-2 entry. I'm calling it 'ACE2-RBD Blocking Protein'. Would you like to see the detailed results?",
                            },
                          ]
                        })

                        // Complete the discovery
                        setSimulationState("complete")
                        setCurrentProtein({
                          name: "ACE2-RBD Blocking Protein",
                          description:
                            "A novel protein designed to bind to the ACE2 receptor with high affinity, preventing SARS-CoV-2 spike protein attachment",
                          efficiency: 96.3,
                        })
                      }, 2000)
                    }, 2000)
                  }, 2000)
                }, 2000)
              }, 2000)
            }, 2000)
          }, 1000)
        }, 500)

        return () => clearTimeout(submitTimer)
      }\
    }, [inputValue, isTyping, fullQuery, chatHistory, toast])

  return (
    <div className="flex h-screen w-full flex-col bg-gradient-to-br from-white to-blue-50">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        {/* Chat window on the left */}
        <div className="flex w-1/2 flex-col border-r border-blue-100 bg-white">
          <div className="border-b border-blue-100 p-4">
            <h2 className="text-xl font-semibold text-blue-900">Protein Discovery Chat</h2>
            <p className="text-sm text-blue-600">Ask about protein structures, binding sites, or novel sequences</p>
          </div>

          <div className="flex-1 overflow-auto p-4">
            {chatHistory.map((msg, index) => (
              <div
                key={index}
                className={`mb-4 flex ${msg.role === "user" ? "justify-end" : "justify-start"} ${
                  msg.role === "thinking" ? "pl-8" : ""
                }`}
              >
                <div
                  className={`max-w-[85%] rounded-lg p-3 ${
                    msg.role === "user"
                      ? "bg-blue-600 text-white"
                      : msg.role === "thinking"
                        ? "bg-blue-50/50 text-blue-800"
                        : "bg-blue-50 text-blue-900"
                  } ${msg.role === "thinking" ? "flex items-center gap-2" : ""}`}
                >
                  {msg.icon && <span>{msg.icon}</span>}
                  <span className={msg.role === "thinking" && msg.status === "active" ? "animate-pulse" : ""}>
                    {msg.content}
                  </span>
                  {msg.role === "thinking" && msg.status === "active" && (
                    <Loader2 className="ml-2 h-4 w-4 animate-spin text-blue-500" />
                  )}
                  {msg.role === "thinking" && msg.status === "complete" && (
                    <CheckCircle2 className="ml-2 h-4 w-4 text-green-500" />
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="border-t border-blue-100 p-4">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={inputValue}
                readOnly
                placeholder="Describe the protein properties you're looking for..."
                className="flex-1 rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 text-blue-900 placeholder-blue-400 focus:border-blue-400 focus:outline-none"
              />
              <button
                className={`rounded-lg bg-blue-600 p-3 text-white transition-colors hover:bg-blue-700 ${
                  simulationState !== "typing" ? "opacity-50" : ""
                }`}
              >
                <Send className="h-5 w-5" />
              </button>
            </div>
            {simulationState === "typing" && (
              <div className="mt-2 text-center text-sm text-blue-500">
                <span className="animate-pulse">Simulating user typing...</span>
              </div>
            )}
          </div>
        </div>

        {/* Main content area on the right */}
        <div className="flex w-1/2 flex-col">
          {simulationState === "complete" ? (
            <DiscoverySummary protein={currentProtein} />
          ) : (
            <div className="flex h-full flex-col">
              {showViewer && (
                <div className="flex-1 p-4">
                  <div className="mb-4 flex items-center justify-between">
                    <h2 className="text-lg font-medium text-blue-900">Protein Preview</h2>
                  </div>
                  <div className="h-full">
                    <ProteinViewer isComplete={simulationState === "complete"} simulationState={simulationState} />
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Simulation controls */}
      <div className="fixed bottom-4 left-1/2 -translate-x-1/2 rounded-lg bg-white p-2 shadow-lg">
        <div className="flex items-center gap-2">
          <div className="text-sm font-medium text-blue-900">Simulation: </div>
          <div className="flex gap-1">
            {["initial", "typing", "processing", "candidate", "complete"].map((state) => (
              <button
                key={state}
                onClick={() => setSimulationState(state as SimulationState)}
                className={`rounded px-2 py-1 text-xs ${
                  simulationState === state ? "bg-blue-600 text-white" : "bg-blue-100 text-blue-700 hover:bg-blue-200"
                }`}
              >
                {state.charAt(0).toUpperCase() + state.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )\
}
