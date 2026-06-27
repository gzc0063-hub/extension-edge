import { useState } from 'react';
import { runDeterministicEngine, type GrowerInput, type RecommendationResult, type ForageType, type ApplicationType } from './engine';
import { AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import efficacyData from './data/efficacy.json';

const ALL_WEEDS = Array.from(new Set(efficacyData.map((e: any) => e.weed_id))).sort();

function App() {
  const [input, setInput] = useState<GrowerInput>({
    forageType: 'bermuda_maint',
    applicationType: 'POST',
    weedsPresent: [],
    hasLactatingDairy: false,
    hasLegumesToSave: false,
    isRUPApplicator: true,
    willExportHayOrManure: false,
    willSlaughterWithinWait: false
  });

  const [results, setResults] = useState<RecommendationResult[]>([]);

  const toggleWeed = (weed: string) => {
    setInput(prev => ({
      ...prev,
      weedsPresent: prev.weedsPresent.includes(weed)
        ? prev.weedsPresent.filter(w => w !== weed)
        : [...prev.weedsPresent, weed]
    }));
  };

  const handleRun = () => {
    const res = runDeterministicEngine(input);
    setResults(res);
  };

  const recommended = results.filter(r => r.status === 'RECOMMEND');
  const manualReview = results.filter(r => r.status === 'MANUAL_REVIEW');
  const rejected = results.filter(r => r.status === 'REJECTED');

  return (
    <div className="min-h-screen bg-gray-50 p-4 font-sans text-gray-900">
      <div className="max-w-4xl mx-auto space-y-8">

        <header className="bg-green-700 text-white p-6 rounded-lg shadow-md">
          <h1 className="text-3xl font-bold">ACES All-Crop IPM Tool</h1>
          <p className="mt-2 text-green-100">Zero-tolerance deterministic pesticide recommendations.</p>
        </header>

        <section className="bg-white p-6 rounded-lg shadow-md space-y-6">
          <h2 className="text-2xl font-semibold border-b pb-2">1. Field Situation</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium mb-1">Crop / Forage Type</label>
              <select
                className="w-full p-2 border rounded-md"
                value={input.forageType}
                onChange={(e) => setInput({...input, forageType: e.target.value as ForageType})}
              >
                <option value="corn">Corn (Field)</option>
                <option value="cotton">Cotton</option>
                <option value="soybeans">Soybeans</option>
                <option value="peanuts">Peanuts</option>
                <option value="grain_sorghum">Grain Sorghum</option>
                <option disabled>────── Pasture <option value="bermuda_est">Bermudagrass (Establishing)</option> Forage ──────</option>
                <option value="bermuda_est">Bermudagrass (Establishing)</option>
                <option value="bermuda_maint">Bermudagrass (Maintenance)</option>
                <option value="bahiagrass">Bahiagrass</option>
                <option value="fescue">Fescue</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Application Timing</label>
              <select
                className="w-full p-2 border rounded-md"
                value={input.applicationType}
                onChange={(e) => setInput({...input, applicationType: e.target.value as ApplicationType})}
              >
                <option value="PRE">Pre-emergence (PRE)</option>
                <option value="POST">Post-emergence (POST)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Target Pests / Weeds (Select multiple)</label>
            <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto p-2 border rounded-md bg-gray-50">
              {ALL_WEEDS.slice(0, 20).map(weed => (
                <button
                  key={weed}
                  onClick={() => toggleWeed(weed)}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                    input.weedsPresent.includes(weed)
                      ? 'bg-green-600 text-white'
                      : 'bg-white border text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  {weed}
                </button>
              ))}
              <span className="text-xs text-gray-400 p-1">(Showing top 20 for demo)</span>
            </div>
          </div>
        </section>

        <section className="bg-white p-6 rounded-lg shadow-md space-y-4">
          <h2 className="text-2xl font-semibold border-b pb-2">2. Hard Constraints (Zero Tolerance)</h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <label className="flex items-center space-x-3 p-3 border rounded-md hover:bg-gray-50 cursor-pointer">
              <input type="checkbox" className="h-5 w-5" checked={input.isRUPApplicator} onChange={(e) => setInput({...input, isRUPApplicator: e.target.checked})} />
              <span className="font-medium">I have a Restricted Use Pesticide license</span>
            </label>
            <label className="flex items-center space-x-3 p-3 border rounded-md hover:bg-gray-50 cursor-pointer">
              <input type="checkbox" className="h-5 w-5 text-red-600" checked={input.hasLactatingDairy} onChange={(e) => setInput({...input, hasLactatingDairy: e.target.checked})} />
              <span className="font-medium">Lactating dairy animals on field</span>
            </label>
            <label className="flex items-center space-x-3 p-3 border rounded-md hover:bg-gray-50 cursor-pointer">
              <input type="checkbox" className="h-5 w-5 text-red-600" checked={input.hasLegumesToSave} onChange={(e) => setInput({...input, hasLegumesToSave: e.target.checked})} />
              <span className="font-medium">Clover/Legumes present to save</span>
            </label>
            <label className="flex items-center space-x-3 p-3 border rounded-md hover:bg-gray-50 cursor-pointer">
              <input type="checkbox" className="h-5 w-5 text-red-600" checked={input.willExportHayOrManure} onChange={(e) => setInput({...input, willExportHayOrManure: e.target.checked})} />
              <span className="font-medium">Plan to export Hay or Manure off-farm</span>
            </label>
          </div>
        </section>

        <button
          onClick={handleRun}
          disabled={input.weedsPresent.length === 0}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-lg shadow-lg transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed text-lg"
        >
          {input.weedsPresent.length === 0 ? "Select at least one weed" : "Run Deterministic Screen"}
        </button>

        {results.length > 0 && (
          <section className="space-y-6">

            {/* Recommended */}
            <div className="bg-green-50 border-2 border-green-500 rounded-lg p-6">
              <h3 className="text-xl font-bold text-green-800 flex items-center gap-2 mb-4">
                <CheckCircle className="h-6 w-6" />
                Recommended Products ({recommended.length})
              </h3>
              {recommended.length === 0 ? (
                <p className="text-green-700">No products passed all hard gates and efficacy requirements.</p>
              ) : (
                <ul className="space-y-3">
                  {recommended.map(r => (
                    <li key={r.uniqueId} className="bg-white p-4 rounded shadow-sm border border-green-200">
                      <div className="flex justify-between items-center">
                        <span className="font-bold text-lg">{r.tradeName}</span>
                        <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full font-mono text-sm">{r.rate}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Manual Review */}
            {manualReview.length > 0 && (
              <div className="bg-yellow-50 border-2 border-yellow-500 rounded-lg p-6">
                <h3 className="text-xl font-bold text-yellow-800 flex items-center gap-2 mb-4">
                  <AlertTriangle className="h-6 w-6" />
                  Requires Manual Review ({manualReview.length})
                </h3>
                <p className="text-yellow-700 mb-4 text-sm">The guide data is UNKNOWN for one of your constraints.</p>
                <ul className="space-y-3">
                  {manualReview.map(r => (
                    <li key={r.uniqueId} className="bg-white p-3 rounded shadow-sm border border-yellow-200">
                      <span className="font-bold">{r.tradeName}</span>
                      <ul className="text-sm text-yellow-700 mt-1 ml-4 list-disc">
                        {r.rejectReasons.map((reason, i) => <li key={i}>{reason.reason}</li>)}
                      </ul>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Rejected */}
            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
              <h3 className="text-lg font-bold text-red-800 flex items-center gap-2 mb-4">
                <XCircle className="h-5 w-5" />
                Rejected Products ({rejected.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {rejected.slice(0, 10).map(r => (
                  <div key={r.uniqueId} className="bg-white p-3 rounded shadow-sm border border-red-100 text-sm">
                    <span className="font-bold text-gray-800">{r.tradeName}</span>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {r.rejectReasons.slice(0, 2).map((reason, i) => (
                        <span key={i} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                          {reason.gateName}
                        </span>
                      ))}
                      {r.rejectReasons.length > 2 && <span className="text-xs text-gray-500">+{r.rejectReasons.length - 2} more</span>}
                    </div>
                  </div>
                ))}
              </div>
              {rejected.length > 10 && <p className="text-sm text-gray-500 mt-3 text-center">...and {rejected.length - 10} more</p>}
            </div>

          </section>
        )}
      </div>
    </div>
  );
}

export default App;
