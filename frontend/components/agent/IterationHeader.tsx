interface IterationHeaderProps {
  currentIteration: number;
  totalIterations: number;
}

export const IterationHeader: React.FC<IterationHeaderProps> = ({
  currentIteration,
  totalIterations,
}) => {
  return (
    <div className="my-6">
      <h3 className="text-lg font-semibold mb-2">
        Starting Iteration {currentIteration} of {totalIterations}
      </h3>
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div
          className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
          style={{ width: `${(currentIteration / totalIterations) * 100}%` }}
        />
      </div>
    </div>
  );
};
