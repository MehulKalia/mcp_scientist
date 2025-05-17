"use client"

import { useState, useEffect } from "react"
import { Search, Globe, Code, BarChart3, CheckCircle2, Loader2 } from "lucide-react"
import { Sidebar, SidebarContent, SidebarHeader, SidebarProvider } from "@/components/ui/sidebar"

const steps = [
  {
    id: "search",
    title: "Searching literature",
    icon: Search,
    delay: 1000,
  },
  {
    id: "internet",
    title: "Searching internet",
    icon: Globe,
    delay: 3000,
  },
  {
    id: "sequences",
    title: "Testing AA sequences",
    icon: Code,
    delay: 6000,
  },
  {
    id: "binding",
    title: "Calculating binding efficiency",
    icon: BarChart3,
    delay: 9000,
  },
]

export default function AgentSidebar({
  isComplete,
  simulationState,
}: {
  isComplete: boolean
  simulationState?: string
}) {
  const [activeSteps, setActiveSteps] = useState<string[]>([])
  const [completedSteps, setCompletedSteps] = useState<string[]>([])

  // Reset steps when simulation state changes
  useEffect(() => {
    if (simulationState === "initial") {
      setActiveSteps([])
      setCompletedSteps([])
    } else if (simulationState === "typing") {
      setActiveSteps([])
      setCompletedSteps([])
    } else if (simulationState === "processing") {
      setActiveSteps(["search"])
      setCompletedSteps([])
    } else if (simulationState === "candidate") {
      setActiveSteps(["binding"])
      setCompletedSteps(["search", "internet", "sequences"])
    } else if (simulationState === "complete") {
      setCompletedSteps(steps.map((step) => step.id))
      setActiveSteps([])
    }
  }, [simulationState])

  // Original step progression logic (only used when simulationState is not provided)
  useEffect(() => {
    if (simulationState) return // Skip if we're using simulation states

    if (isComplete) {
      setCompletedSteps(steps.map((step) => step.id))
      setActiveSteps([])
      return
    }

    steps.forEach((step) => {
      const timer = setTimeout(() => {
        setActiveSteps((prev) => [...prev, step.id])

        // Mark previous step as completed
        if (steps.findIndex((s) => s.id === step.id) > 0) {
          const prevStep = steps[steps.findIndex((s) => s.id === step.id) - 1]
          setCompletedSteps((prev) => [...prev, prevStep.id])
          setActiveSteps((prev) => prev.filter((id) => id !== prevStep.id))
        }
      }, step.delay)

      return () => clearTimeout(timer)
    })
  }, [isComplete, simulationState])

  return (
    <SidebarProvider>
      <Sidebar className="w-64 border-r border-blue-100 bg-white">
        <SidebarHeader className="border-b border-blue-100 p-4">
          <h2 className="text-lg font-semibold text-blue-900">Discovery Pipeline</h2>
        </SidebarHeader>
        <SidebarContent className="p-4">
          <div className="space-y-6">
            {isComplete ? (
              <div className="flex flex-col items-center justify-center py-8 text-center">
                <CheckCircle2 className="mb-2 h-12 w-12 text-green-500" />
                <h3 className="text-lg font-medium text-blue-900">Discovery Complete</h3>
                <p className="mt-1 text-sm text-blue-600">Your protein has been successfully discovered</p>
              </div>
            ) : (
              steps.map((step) => (
                <div key={step.id} className="flex items-center gap-3">
                  <div className="flex h-8 w-8 items-center justify-center">
                    {completedSteps.includes(step.id) ? (
                      <CheckCircle2 className="h-6 w-6 text-green-500" />
                    ) : activeSteps.includes(step.id) ? (
                      <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
                    ) : (
                      <div className="h-6 w-6 rounded-full border-2 border-blue-200" />
                    )}
                  </div>
                  <div className="flex flex-col">
                    <span
                      className={`font-medium ${
                        activeSteps.includes(step.id)
                          ? "text-blue-600"
                          : completedSteps.includes(step.id)
                            ? "text-green-600"
                            : "text-blue-400"
                      }`}
                    >
                      {step.title}
                    </span>
                    {activeSteps.includes(step.id) && <span className="text-xs text-blue-400">Processing...</span>}
                  </div>
                </div>
              ))
            )}
          </div>
        </SidebarContent>
      </Sidebar>
    </SidebarProvider>
  )
}
