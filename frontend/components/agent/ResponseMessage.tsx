import { Bot, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

interface ResponseMessageProps {
  content: string;
  isCollapsible?: boolean;
}

export const ResponseMessage: React.FC<ResponseMessageProps> = ({
  content,
  isCollapsible = true,
}) => {
  const [isExpanded, setIsExpanded] = useState(!isCollapsible);

  return (
    <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-green-600" />
          <span className="text-sm font-medium text-green-800">
            LLM Response
          </span>
        </div>
        {isCollapsible && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-green-600 hover:text-green-700"
          >
            {isExpanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>
        )}
      </div>
      <div
        className={`text-sm text-green-900 ${
          !isExpanded && isCollapsible ? "line-clamp-3" : ""
        }`}
      >
        {content}
      </div>
    </div>
  );
};
