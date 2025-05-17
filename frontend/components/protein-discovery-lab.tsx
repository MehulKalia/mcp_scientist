"use client";

import { useState } from "react";
import { useToast } from "@/hooks/use-toast";
import Header from "@/components/header";
import ChatInterface from "@/components/chat-interface";
import ProteinViewer from "@/components/protein-viewer";
import DiscoverySummary from "@/components/discovery-summary";

export default function ProteinDiscoveryLab() {
  const [showViewer, setShowViewer] = useState(true);
  const [discoveryComplete, setDiscoveryComplete] = useState(false);
  const [currentProtein, setCurrentProtein] = useState<{
    name: string;
    description: string;
    efficiency: number;
  } | null>(null);
  const [pdbData, setPdbData] = useState<string | null>(null);
  const { toast } = useToast();

  // Handle discovery completion
  const handleDiscoveryComplete = (protein: {
    name: string;
    description: string;
    efficiency: number;
  }) => {
    setCurrentProtein(protein);
    setDiscoveryComplete(true);
  };

  // Handle new candidate notification
  const handleCandidateFound = () => {
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
    });
  };

  // Handle PDB data updates
  const handlePdbUpdate = (pdbContent: string) => {
    console.log("Received PDB data update");
    setPdbData(pdbContent);
  };

  return (
    <div className="flex min-h-screen w-full flex-col bg-white">
      <Header />

      <main className="flex flex-1 overflow-hidden">
        {/* Chat interface - takes 60% of the width */}
        <div className="w-3/5 border-r border-neutral-200">
          <ChatInterface
            onCandidateFound={handleCandidateFound}
            onDiscoveryComplete={handleDiscoveryComplete}
            onPdbUpdate={handlePdbUpdate}
          />
        </div>

        {/* Visualization panel - takes 40% of the width */}
        <div className="w-2/5">
          {discoveryComplete ? (
            <DiscoverySummary protein={currentProtein} />
          ) : (
            <ProteinViewer pdbContent={pdbData || undefined} />
          )}
        </div>
      </main>
    </div>
  );
}
