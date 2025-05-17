"use client";

import { useEffect, useRef, useState } from "react";
import { RotateCcw, Pause, Play } from "lucide-react";
import dynamic from "next/dynamic";

interface ProteinViewerProps {
  pdbUrl?: string;
  pdbContent?: string;
}

export default function ProteinViewer({
  pdbUrl,
  pdbContent,
}: ProteinViewerProps) {
  console.log("ProteinViewer render - props:", { pdbUrl, pdbContent });

  const [rotating, setRotating] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);
  const stageRef = useRef<any>(null);

  useEffect(() => {
    console.log("ProteinViewer useEffect - initializing NGL");
    const container = containerRef.current;
    if (!container) {
      console.log("Container ref is null, skipping initialization");
      return;
    }

    // Dynamically import NGL
    import("ngl")
      .then((NGL) => {
        console.log("NGL imported successfully");

        // Initialize NGL Stage
        const stage = new NGL.Stage(container, {
          backgroundColor: "white",
          quality: "medium",
        });
        console.log("NGL Stage created");

        // Store stage reference
        stageRef.current = stage;

        // Load PDB file
        if (pdbUrl) {
          console.log("Loading PDB from URL:", pdbUrl);
          stage.loadFile(pdbUrl, { defaultRepresentation: true });
        } else if (pdbContent) {
          console.log("Loading PDB from content");
          stage.loadFile(new Blob([pdbContent], { type: "text/plain" }), {
            ext: "pdb",
            defaultRepresentation: true,
          });
        } else {
          console.log("No PDB provided, loading default protein");
          stage.loadFile("rcsb://1crn", { defaultRepresentation: true });
        }

        // Set up auto-rotation
        stage.autoView();
        console.log("Stage setup complete");

        return () => {
          console.log("Cleaning up NGL Stage");
          stage.dispose();
        };
      })
      .catch((error) => {
        console.error("Error loading NGL:", error);
      });
  }, [pdbUrl, pdbContent]);

  useEffect(() => {
    console.log("Rotation effect - rotating:", rotating);
    if (!stageRef.current) {
      console.log("No stage reference available");
      return;
    }

    // Handle rotation state
    if (rotating) {
      console.log("Enabling auto-rotation");
      stageRef.current.autoView();
    }
  }, [rotating]);

  const handleReset = () => {
    console.log("Reset view clicked");
    if (stageRef.current) {
      stageRef.current.autoView();
    }
  };

  return (
    <div className="flex h-full flex-col">
      <div className="border-b border-neutral-200 p-4">
        <h2 className="text-xl font-light text-neutral-800">
          Protein Structure
        </h2>
      </div>

      <div className="relative flex-1">
        <div className="absolute right-4 top-4 z-10 flex gap-2">
          <button
            onClick={() => {
              console.log("Rotation toggle clicked");
              setRotating(!rotating);
            }}
            className="rounded-full bg-white p-2 text-neutral-600 shadow-sm hover:bg-neutral-50"
            title={rotating ? "Pause rotation" : "Start rotation"}
          >
            {rotating ? (
              <Pause className="h-4 w-4" />
            ) : (
              <Play className="h-4 w-4" />
            )}
          </button>
          <button
            onClick={handleReset}
            className="rounded-full bg-white p-2 text-neutral-600 shadow-sm hover:bg-neutral-50"
            title="Reset view"
          >
            <RotateCcw className="h-4 w-4" />
          </button>
        </div>

        <div ref={containerRef} className="h-full w-full" />

        <div className="absolute bottom-4 left-4 right-4 rounded-lg bg-white p-3 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-medium text-neutral-800">
                Protein Visualization
              </h3>
              <p className="text-xs text-neutral-500">
                Drag to rotate • Scroll to zoom
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
