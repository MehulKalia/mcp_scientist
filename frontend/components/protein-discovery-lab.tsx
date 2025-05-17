"use client";

import { useState, useRef, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";
import Header from "@/components/header";
import ChatInterface from "@/components/chat-interface";
import ProteinViewer from "@/components/protein-viewer";
import DiscoverySummary from "@/components/discovery-summary";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { ScrollArea } from "./ui/scroll-area";
import { Button } from "./ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./ui/tooltip";
import { Info, RotateCcw, Eye, EyeOff, ZoomIn, ZoomOut } from "lucide-react";
import { ProteinViewerApi, DEFAULT_PDB } from "./protein-viewer";

// Define a type for the design history items
// This type should be flexible enough to accept data from the agent
interface DesignHistoryItem {
  id: string;
  pdbContent: string;
  metadata: {
    // Make properties optional and match potential incoming data structure
    name?: string;
    sequence?: string;
    binding_score?: number;
    confidence_score?: number;
    iteration?: number;
    [key: string]: any; // Allow for other properties from agent data
  };
  timestamp: string;
}

export default function ProteinDiscoveryLab() {
  const [showViewer, setShowViewer] = useState(true);
  const [discoveryComplete, setDiscoveryComplete] = useState(false);
  const [currentProtein, setCurrentProtein] = useState<{
    name: string;
    description: string;
    efficiency: number;
  } | null>(null);
  const [pdbData, setPdbData] = useState<string | null>(DEFAULT_PDB);
  const [designHistory, setDesignHistory] = useState<DesignHistoryItem[]>([]);
  const [selectedDesignId, setSelectedDesignId] = useState<string | null>(null);
  const { toast } = useToast();
  const [isProteinInfoVisible, setIsProteinInfoVisible] = useState(true);

  const proteinViewerRef = useRef<ProteinViewerApi | null>(null);

  // Handle discovery completion
  const handleDiscoveryComplete = (protein: {
    name: string;
    description: string;
    efficiency: number;
  }) => {
    setCurrentProtein(protein);
    setDiscoveryComplete(true);
    setShowViewer(false); // Hide viewer when discovery is complete, show summary
  };

  // Handle new candidate notification and show viewer
  const handleCandidateFound = () => {
    setShowViewer(true);
    // Toast notification is now handled by the button in chat
  };

  // Handle PDB data updates and add to history
  const handlePdbUpdate = (pdbContent: string, metadata?: any) => {
    console.log("Received PDB data update", metadata);
    const id = `design-${Date.now()}`;
    const timestamp = new Date().toLocaleTimeString();
    const newItem: DesignHistoryItem = {
      id,
      pdbContent,
      metadata: {
        // Map incoming metadata to DesignHistoryItem structure
        name: metadata?.name || `Design Iteration ${designHistory.length + 1}`, // Use provided name or generate one
        sequence: metadata?.sequence || "N/A",
        binding_score: metadata?.binding_score,
        confidence_score: metadata?.confidence_score,
        iteration: metadata?.iteration,
        ...metadata, // Spread any other incoming properties
      },
      timestamp,
    };
    setDesignHistory((prev) => [...prev, newItem]);
    setPdbData(pdbContent);
    setSelectedDesignId(id); // Automatically select the new design
  };

  // Function to select a design from history to view
  const selectDesignFromHistory = (id: string) => {
    const selected = designHistory.find((item) => item.id === id);
    if (selected) {
      setPdbData(selected.pdbContent);
      setSelectedDesignId(id);
      setShowViewer(true); // Ensure viewer is shown
    }
  };

  // Find the currently displayed protein metadata
  const currentProteinMetadata = selectedDesignId
    ? designHistory.find((item) => item.id === selectedDesignId)?.metadata
    : null;

  return (
    <TooltipProvider>
      <div className="flex min-h-screen w-full bg-white">
        {/* Left Panel: Chat Interface */}
        <div className="w-1/2 border-r border-neutral-200 flex flex-col">
          <ChatInterface
            onCandidateFound={handleCandidateFound}
            onDiscoveryComplete={handleDiscoveryComplete}
            onPdbUpdate={handlePdbUpdate}
          />
        </div>

        {/* Right Panel: Protein Viewer and Info */}
        <div className="w-1/2 flex flex-col">
          {/* Sticky Header for Protein Info */}
          {showViewer && currentProteinMetadata && (
            <Card className="rounded-none border-t-0 border-l-0 border-r-0">
              <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0">
                <CardTitle className="text-xl font-semibold">
                  {currentProteinMetadata.name || "Unnamed Design"}
                </CardTitle>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() =>
                        setIsProteinInfoVisible(!isProteinInfoVisible)
                      }
                    >
                      {isProteinInfoVisible ? (
                        <EyeOff className="h-5 w-5" />
                      ) : (
                        <Eye className="h-5 w-5" />
                      )}
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    {isProteinInfoVisible
                      ? "Hide Protein Info"
                      : "Show Protein Info"}
                  </TooltipContent>
                </Tooltip>
              </CardHeader>
              {isProteinInfoVisible && (
                <CardContent className="text-sm text-muted-foreground">
                  {currentProteinMetadata.sequence && (
                    <p>
                      Sequence:{" "}
                      <code className="relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm font-semibold">
                        {currentProteinMetadata.sequence}
                      </code>
                    </p>
                  )}
                  {currentProteinMetadata.binding_score !== undefined && (
                    <p>
                      Binding Score:{" "}
                      <span className="font-semibold text-green-600">
                        {currentProteinMetadata.binding_score.toFixed(2)}
                      </span>
                    </p>
                  )}
                  {currentProteinMetadata.confidence_score !== undefined && (
                    <p>
                      Confidence Score:{" "}
                      <span className="font-semibold text-blue-600">
                        {currentProteinMetadata.confidence_score.toFixed(2)}
                      </span>
                    </p>
                  )}
                  {currentProteinMetadata.iteration !== undefined && (
                    <p>
                      Iteration:{" "}
                      <span className="font-semibold">
                        {currentProteinMetadata.iteration}
                      </span>
                    </p>
                  )}
                </CardContent>
              )}
            </Card>
          )}

          {/* Protein Viewer */}
          <div className="flex-1 relative">
            {showViewer ? (
              <ProteinViewer
                ref={proteinViewerRef}
                pdbContent={pdbData || DEFAULT_PDB}
              />
            ) : discoveryComplete && currentProtein ? (
              <DiscoverySummary protein={currentProtein} />
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                Start a protein discovery task in the chat.
              </div>
            )}
            {/* 3D Viewer Controls Overlay */}
            {showViewer && (
              <div className="absolute bottom-4 left-4 z-10 flex space-x-2">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="icon"
                      className="shadow-sm"
                      onClick={() => {
                        proteinViewerRef.current?.autoView();
                      }}
                    >
                      <RotateCcw className="h-5 w-5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Reset View</TooltipContent>
                </Tooltip>
                {/* Add Zoom and Style controls here later */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="icon"
                      className="shadow-sm"
                      onClick={() => {
                        proteinViewerRef.current?.viewerControls.zoom(10);
                      }}
                    >
                      <ZoomIn className="h-5 w-5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Zoom In</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="icon"
                      className="shadow-sm"
                      onClick={() => {
                        proteinViewerRef.current?.viewerControls.zoom(-10);
                      }}
                    >
                      <ZoomOut className="h-5 w-5" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Zoom Out</TooltipContent>
                </Tooltip>

                {/* Representation Controls */}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="sm"
                      className="shadow-sm"
                      onClick={() => {
                        (
                          proteinViewerRef.current as ProteinViewerApi
                        )?.changeRepresentation("cartoon");
                      }}
                    >
                      Cartoon
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Show Cartoon Representation</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="sm"
                      className="shadow-sm"
                      onClick={() => {
                        (
                          proteinViewerRef.current as ProteinViewerApi
                        )?.changeRepresentation("surface");
                      }}
                    >
                      Surface
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Show Surface Representation</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant="outline"
                      size="sm"
                      className="shadow-sm"
                      onClick={() => {
                        (
                          proteinViewerRef.current as ProteinViewerApi
                        )?.changeRepresentation("ball+stick");
                      }}
                    >
                      Ball+Stick
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    Show Ball and Stick Representation
                  </TooltipContent>
                </Tooltip>
              </div>
            )}
          </div>

          {/* Design History Timeline */}
          {showViewer && (
            <div className="h-32 border-t border-neutral-200 p-4">
              <h3 className="text-lg font-semibold mb-2">Design History</h3>
              <ScrollArea className="h-20 w-full pb-4">
                <div className="flex space-x-4">
                  {designHistory.map((item) => (
                    <Button
                      key={item.id}
                      variant={
                        selectedDesignId === item.id ? "default" : "outline"
                      }
                      onClick={() => selectDesignFromHistory(item.id)}
                      className="flex-none w-32 h-20 flex flex-col items-center justify-center text-sm text-center p-2"
                    >
                      <span className="font-semibold truncate w-full">
                        {item.metadata.name || "Unnamed"}
                      </span>
                      {item.metadata.binding_score !== undefined && (
                        <span className="text-xs text-muted-foreground truncate w-full">
                          Score: {item.metadata.binding_score.toFixed(2)}
                        </span>
                      )}
                      {item.metadata.iteration !== undefined && (
                        <span className="text-xs text-muted-foreground">
                          Iteration: {item.metadata.iteration}
                        </span>
                      )}
                      <span className="text-xs text-muted-foreground">
                        {item.timestamp}
                      </span>
                    </Button>
                  ))}
                  {designHistory.length === 0 && (
                    <div className="w-full h-full flex items-center justify-center text-muted-foreground text-sm">
                      No design history yet.
                    </div>
                  )}
                </div>
              </ScrollArea>
            </div>
          )}
        </div>
      </div>
    </TooltipProvider>
  );
}
