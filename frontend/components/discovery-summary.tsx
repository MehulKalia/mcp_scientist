import { Download, Share2 } from "lucide-react"

interface ProteinProps {
  name: string
  description: string
  efficiency: number
}

export default function DiscoverySummary({ protein }: { protein: ProteinProps | null }) {
  if (!protein) return null

  return (
    <div className="flex h-full flex-col overflow-auto">
      <div className="border-b border-neutral-200 p-4">
        <h2 className="text-xl font-light text-neutral-800">Discovery Results</h2>
      </div>

      <div className="flex-1 overflow-auto p-6">
        <div className="mb-8 text-center">
          <h3 className="mb-2 text-3xl font-light text-neutral-800">{protein.name}</h3>
          <p className="text-neutral-600">{protein.description}</p>
        </div>

        <div className="mb-8 grid grid-cols-3 gap-4">
          <div className="rounded-lg bg-white p-4 shadow-sm">
            <h4 className="mb-1 text-sm font-medium text-neutral-500">Binding Efficiency</h4>
            <p className="text-2xl font-light text-neutral-800">{protein.efficiency}%</p>
          </div>
          <div className="rounded-lg bg-white p-4 shadow-sm">
            <h4 className="mb-1 text-sm font-medium text-neutral-500">Molecular Weight</h4>
            <p className="text-2xl font-light text-neutral-800">38.7 kDa</p>
          </div>
          <div className="rounded-lg bg-white p-4 shadow-sm">
            <h4 className="mb-1 text-sm font-medium text-neutral-500">Stability Score</h4>
            <p className="text-2xl font-light text-neutral-800">9.2/10</p>
          </div>
        </div>

        <div className="mb-6">
          <h4 className="mb-3 text-sm font-medium text-neutral-600">Amino Acid Sequence</h4>
          <div className="max-h-32 overflow-auto rounded-md bg-white p-3 font-mono text-xs text-neutral-700 shadow-sm">
            MYKRWVLLLLFAMVLGSTQGVPFECANLMRLKDDSVTEIENCSVYNETYNSTFSTFLEKFVPKGCRPCQLENLRFQVNATSSNICVDCSHKDCTKSKSCSCSQDDETCSPKFPECSIICVKQLRENYTLIRGRRCPEEKHKCTVSNKLFPVEMFVFDENFTLKEGAPIKVTIIERNGLQMSILINGRPQNMILPNKTKEFLCVDAVILETSWAVLPVLHRTYNYTIMDGRTKIGSVCTNPSYPHYSPIKFVTVEEFDHGVLVLQVKDGEELPAEFRVLMFNNNRLTGTFFKLVNPDCIIDRLKLFNDVGGYIEYKTFEDSIKNVKGPVSVKIDLKKGKTVNVTLS
          </div>
        </div>

        <div className="mb-6">
          <h4 className="mb-3 text-sm font-medium text-neutral-600">Structure Prediction Confidence</h4>
          <div className="space-y-3">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-neutral-600">Alpha Helix</span>
                <span className="text-xs font-medium text-neutral-800">94%</span>
              </div>
              <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-neutral-200">
                <div className="h-full w-[94%] rounded-full bg-blue-600"></div>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-neutral-600">Beta Sheet</span>
                <span className="text-xs font-medium text-neutral-800">89%</span>
              </div>
              <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-neutral-200">
                <div className="h-full w-[89%] rounded-full bg-blue-600"></div>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-neutral-600">Overall</span>
                <span className="text-xs font-medium text-neutral-800">96%</span>
              </div>
              <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-neutral-200">
                <div className="h-full w-[96%] rounded-full bg-blue-600"></div>
              </div>
            </div>
          </div>
        </div>

        <div className="mb-6">
          <h4 className="mb-2 text-sm font-medium text-neutral-600">Applications</h4>
          <ul className="list-inside list-disc space-y-1 text-sm text-neutral-600">
            <li>SARS-CoV-2 entry inhibition</li>
            <li>ACE2 receptor binding studies</li>
            <li>Antiviral therapeutic development</li>
            <li>Respiratory virus research</li>
          </ul>
        </div>

        <div className="flex justify-center gap-4">
          <button className="flex items-center gap-1 rounded-full border border-neutral-300 bg-white px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-50">
            <Download className="h-4 w-4" />
            <span>Export Data</span>
          </button>
          <button className="flex items-center gap-1 rounded-full bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700">
            <Share2 className="h-4 w-4" />
            <span>Share Results</span>
          </button>
        </div>
      </div>
    </div>
  )
}
