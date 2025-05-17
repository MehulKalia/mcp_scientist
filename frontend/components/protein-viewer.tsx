"use client";

import { forwardRef, useEffect, useRef, useState } from "react";
import { Loader2, RotateCcw, Info, ZoomIn, ZoomOut } from "lucide-react";
import * as NGL from "ngl";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

// Default PDB string for demonstration (a simple alpha helix)
export const DEFAULT_PDB = `ATOM      1  N   ALA A   1      27.271  24.862   5.000  1.00 20.00
ATOM      2  CA  ALA A   1      26.000  24.000   5.000  1.00 20.00
ATOM      3  C   ALA A   1      25.000  24.000   6.000  1.00 20.00
ATOM      4  O   ALA A   1      25.000  24.000   7.000  1.00 20.00
ATOM      5  CB  ALA A   1      26.000  22.000   5.000  1.00 20.00
ATOM      6  N   ALA A   2      24.000  24.000   6.000  1.00 20.00
ATOM      7  CA  ALA A   2      23.000  24.000   7.000  1.00 20.00
ATOM      8  C   ALA A   2      22.000  24.000   8.000  1.00 20.00
ATOM      9  O   ALA A   2      21.000  24.000   9.000  1.00 20.00
ATOM     10  CB  ALA A   2      23.000  22.000   7.000  1.00 20.00
ATOM     11  N   ALA A   3      22.000  24.000   8.000  1.00 20.00
ATOM     12  CA  ALA A   3      21.000  24.000   9.000  1.00 20.00
ATOM     13  C   ALA A   3      20.000  24.000  10.000  1.00 20.00
ATOM     14  O   ALA A   3      19.000  24.000  11.000  1.00 20.00
ATOM     15  CB  ALA A   3      21.000  22.000   9.000  1.00 20.00
CONECT    1    2
CONECT    2    3
CONECT    3    4
CONECT    2    5
CONECT    6    7
CONECT    7    8
CONECT    8    9
CONECT    7   10
CONECT   11   12
CONECT   12   13
CONECT   13   14
CONECT   12   15
END`;

export interface ProteinViewerApi {
  autoView: () => void;
  viewerControls: {
    zoom: (delta: number) => void;
  };
  changeRepresentation: (style: string) => void;
}

export type NglStage = NGL.Stage;

interface ProteinViewerProps {
  pdbContent?: string;
  onLoad?: () => void;
}

const ProteinViewer = forwardRef<ProteinViewerApi, ProteinViewerProps>(
  ({ pdbContent = DEFAULT_PDB, onLoad }, ref) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const stageRef = useRef<NGL.Stage | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    // Expose methods via ref
    useEffect(() => {
      if (ref && stageRef.current) {
        (ref as React.MutableRefObject<ProteinViewerApi>).current = {
          autoView: () => stageRef.current?.autoView(),
          viewerControls: {
            zoom: (delta: number) =>
              stageRef.current?.viewerControls.zoom(delta),
          },
          changeRepresentation: (style: string) => {
            const components =
              stageRef.current?.getComponentsByName("structure");
            if (components) {
              components.forEach((component) => {
                component.removeAllRepresentations();
                component.addRepresentation(style, {
                  color: "chainid",
                  opacity: 0.8,
                });
              });
            }
          },
        };
      }
    }, [ref]);

    // Effect to initialize NGL Stage on mount
    useEffect(() => {
      console.log("ProteinViewer: Initializing NGL Stage...");
      if (!containerRef.current) {
        console.log(
          "ProteinViewer: Container ref not available. Cannot initialize stage."
        );
        return;
      }

      console.log("ProteinViewer: Container dimensions on init:", {
        width: containerRef.current.clientWidth,
        height: containerRef.current.clientHeight,
      });

      // Initialize NGL Stage
      console.log(
        "ProteinViewer: Container ref available. Creating NGL stage."
      );
      const stage = new NGL.Stage(containerRef.current, {
        backgroundColor: "white",
        quality: "medium",
      });
      stageRef.current = stage;
      stage.handleResize();

      console.log("ProteinViewer: NGL Stage initialized", stage);

      return () => {
        console.log("ProteinViewer: Disposing NGL Stage");
        stage.dispose();
      };
    }, []); // Empty dependency array means this runs once on mount

    // Effect to load PDB content when it changes or stage is ready
    useEffect(() => {
      console.log("ProteinViewer: pdbContent effect triggered.", {
        pdbContent,
      });
      const contentToLoad = pdbContent ?? DEFAULT_PDB; // Ensure content is available

      if (!stageRef.current || !contentToLoad) {
        console.log("ProteinViewer: Stage not ready or no content to load.");
        return;
      }

      console.log("ProteinViewer: Container dimensions before loading:", {
        width: containerRef.current?.clientWidth,
        height: containerRef.current?.clientHeight,
      });

      setIsLoading(true);
      console.log("ProteinViewer: Loading structure into stage...");
      const stage = stageRef.current;

      // Clear existing components
      stage.removeAllComponents();

      // Load new structure
      stage
        // Load the content from a Blob to ensure it's treated as data
        .loadFile(new Blob([contentToLoad], { type: "text/plain" }), {
          ext: "pdb",
        })
        .then((component) => {
          console.log(
            "ProteinViewer: Structure loaded successfully.",
            component
          );
          // Cast the component to StructureComponent and add representation immediately
          const structureComponent = component as NGL.StructureComponent;
          if (!structureComponent) {
            console.log(
              "ProteinViewer: Loaded component is not a StructureComponent."
            );
            return;
          }

          console.log("ProteinViewer: Adding cartoon representation");
          structureComponent.addRepresentation("cartoon", {
            color: "chainid", // Using chainid again for consistency
            opacity: 0.8,
          });

          // Center and zoom to the new structure
          setTimeout(() => {
            stage.autoView();
            console.log("ProteinViewer: autoView called after delay.");
          }, 100);

          setIsLoading(false);
          onLoad?.();
        })
        .catch((error: any) => {
          console.error("ProteinViewer: Error loading structure:", error);
          setIsLoading(false);
        });
    }, [pdbContent, onLoad]); // Dependencies reverted

    return (
      <div className="relative w-full h-full">
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-10">
            <div className="flex flex-col items-center space-y-2">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <span className="text-sm text-muted-foreground">
                Loading structure...
              </span>
            </div>
          </div>
        )}

        <div ref={containerRef} className="w-full h-full" />
      </div>
    );
  }
);

export default ProteinViewer;
