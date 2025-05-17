import Link from "next/link";

export default function Header() {
  return (
    <header className="border-b border-neutral-200 bg-white px-4 py-4 md:px-8">
      <div className="mx-auto flex max-w-7xl items-center justify-center">
        <div className="flex items-center gap-2">
          <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z"
              stroke="#4285F4"
              strokeWidth="2"
            />
            <path
              d="M12 16C14.2091 16 16 14.2091 16 12C16 9.79086 14.2091 8 12 8C9.79086 8 8 9.79086 8 12C8 14.2091 9.79086 16 12 16Z"
              fill="#4285F4"
            />
          </svg>
          <span className="text-lg font-medium text-neutral-800">Protogen</span>
        </div>
      </div>
    </header>
  );
}
