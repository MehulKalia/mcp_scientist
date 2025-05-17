import { Dna, BarChart2, FileText } from "lucide-react";

interface DesignResultsProps {
  sequence: string;
  bindingScore: number;
  rationale: string;
}

export const DesignResults: React.FC<DesignResultsProps> = ({
  sequence,
  bindingScore,
  rationale,
}) => {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 mb-4">
      <h3 className="text-xl font-semibold mb-4">Design Results</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Sequence and Score */}
        <div className="space-y-4">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <Dna className="h-5 w-5 text-blue-600" />
              <h4 className="font-medium text-blue-800">Best Sequence</h4>
            </div>
            <div className="font-mono text-sm bg-white p-3 rounded border border-blue-100">
              {sequence}
            </div>
          </div>

          <div className="bg-green-50 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <BarChart2 className="h-5 w-5 text-green-600" />
              <h4 className="font-medium text-green-800">Binding Score</h4>
            </div>
            <div className="text-2xl font-semibold text-green-700">
              {bindingScore.toFixed(2)}
            </div>
          </div>
        </div>

        {/* Rationale */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <FileText className="h-5 w-5 text-gray-600" />
            <h4 className="font-medium text-gray-800">Design Rationale</h4>
          </div>
          <div className="prose prose-sm max-w-none">
            {rationale.split("\n").map((paragraph, index) => (
              <p key={index} className="text-gray-700 mb-2">
                {paragraph}
              </p>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
