import { MessageSquare } from "lucide-react";

interface PromptMessageProps {
  content: string;
}

export const PromptMessage: React.FC<PromptMessageProps> = ({ content }) => {
  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
      <div className="flex items-center gap-2 mb-2">
        <MessageSquare className="h-4 w-4 text-yellow-600" />
        <span className="text-sm font-medium text-yellow-800">
          Prompt to LLM
        </span>
      </div>
      <pre className="text-sm text-yellow-900 whitespace-pre-wrap font-mono">
        {content}
      </pre>
    </div>
  );
};
