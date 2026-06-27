import { useState } from 'react';
import { evaluatePastureWeeds, evaluateSoybeanWeeds, evaluateCottonInsects, type GuideType, type RecommendationResult, type PastureInput, type SoybeanWeedInput, type CottonInsectInput } from './engine';
import { CheckCircle, XCircle } from 'lucide-react';
import efficacyData from './data/efficacy.json';

const ALL_WEEDS = Array.from(new Set(efficacyData.map((e: any) => e.weed_id))).sort();

function App() {
  const [guideType, setGuideType] = useState<GuideType>('pasture_weeds');

  // --- State for Pasture ---
  const [pastureInput, setPastureInput] = useState<PastureInput>({
    forageType: 'bermuda_maint', applicationType: 'POST', weedsPresent: [], hasLactatingDairy: false, hasLegumesToSave: false, isRUPApplicator: true, willExportHayOrManure: false
  });

  // --- State for Soybeans ---
  const [soybeanInput, setSoybeanInput] = useState<SoybeanWeedInput>({
    applicationType: 'POST', seedTrait: 'enlist', daysToHarvest: 100, isRUPApplicator: true
  });

  // --- State for Cotton Insects ---
  const [cottonInput, setCottonInput] = useState<CottonInsectInput>({
    pestTarget: 'bollworm', thresholdMet: false, beneficialsPresentToSave: false, daysToHarvest: 100, isRUPApplicator: true
  });

  const [results, setResults] = useState<RecommendationResult[]>([]);

  const handleRun = () => {
    if (guideType === 'pasture_weeds') setResults(evaluatePastureWeeds(pastureInput));
    if (guideType === 'soybean_weeds') setResults(evaluateSoybeanWeeds(soybeanInput));
    if (guideType === 'cotton_insects') setResults(evaluateCottonInsects(cottonInput));
  };

  const toggleWeed = (weed: string) => {
    setPastureInput(prev => ({
      ...prev,
      weedsPresent: prev.weedsPresent.includes(weed)
        ? prev.weedsPresent.filter(w => w !== weed)
        : [...prev.weedsPresent, weed]
    }));
  };

  const recommended = results.filter(r => r.status === 'RECOMMEND');
  // const manualReview = results.filter(r => r.status === 'MANUAL_REVIEW');
  const rejected = results.filter(r => r.status === 'REJECTED');

  return (
    <div className="min-h-screen bg-gray-50 p-4 font-sans text-gray-900">
      <div className="max-w-4xl mx-auto space-y-8">

        <header className="bg-green-700 text-white p-6 rounded-lg shadow-md">
          <h1 className="text-3xl font-bold">ACES All-Crop IPM Tool</h1>
          <p className="mt-2 text-green-100">Zero-tolerance deterministic pesticide recommendations.</p>
        </header>

        <section className="bg-white p-6 rounded-lg shadow-md space-y-6">
          <h2 className="text-2xl font-semibold border-b pb-2">1. Select Guide & Situation</h2>

          <div>
            <label className="block text-sm font-medium mb-1">Select IPM Guide</label>
            <select
              className="w-full p-2 border rounded-md font-bold bg-gray-50"
              value={guideType}
              onChange={(e) => {
                  setGuideType(e.target.value as GuideType);
                  setResults([]);
              }}
            >
              <option value="pasture_weeds">Pasture & Forage Weed Control 2026</option>
              <option value="soybean_weeds">Soybean Weed Control 2025</option>
              <option value="cotton_insects">Cotton Insect Control 2026</option>
            </select>
          </div>

          {/* DYNAMIC FORM RENDERER */}

          {guideType === 'pasture_weeds' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm mb-1">Forage Type</label>
                    <select className="w-full p-2 border rounded-md" value={pastureInput.forageType} onChange={e => setPastureInput({...pastureInput, forageType: e.target.value})}>
                      <option value="bermuda_maint">Bermudagrass (Maintenance)</option>
                      <option value="bahiagrass">Bahiagrass</option>
                      <option value="fescue">Fescue</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm mb-1">Timing</label>
                    <select className="w-full p-2 border rounded-md" value={pastureInput.applicationType} onChange={e => setPastureInput({...pastureInput, applicationType: e.target.value})}>
                      <option value="PRE">PRE</option>
                      <option value="POST">POST</option>
                    </select>
                  </div>
              </div>
              <div>
                <label className="block text-sm mb-1">Target Weeds</label>
                <div className="flex flex-wrap gap-2">
                  {ALL_WEEDS.slice(0, 10).map(weed => (
                    <button key={weed} onClick={() => toggleWeed(weed)} className={`px-3 py-1 rounded-full text-sm border ${pastureInput.weedsPresent.includes(weed) ? 'bg-green-600 text-white' : 'bg-white'}`}>
                      {weed}
                    </button>
                  ))}
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 mt-4">
                 <label className="flex items-center space-x-2"><input type="checkbox" checked={pastureInput.isRUPApplicator} onChange={e => setPastureInput({...pastureInput, isRUPApplicator: e.target.checked})}/><span>Has RUP License</span></label>
                 <label className="flex items-center space-x-2"><input type="checkbox" checked={pastureInput.hasLactatingDairy} onChange={e => setPastureInput({...pastureInput, hasLactatingDairy: e.target.checked})}/><span className="text-red-600">Dairy on field</span></label>
                 <label className="flex items-center space-x-2"><input type="checkbox" checked={pastureInput.hasLegumesToSave} onChange={e => setPastureInput({...pastureInput, hasLegumesToSave: e.target.checked})}/><span className="text-red-600">Legumes to save</span></label>
              </div>
            </div>
          )}

          {guideType === 'soybean_weeds' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-bold text-red-600 mb-1">Planted Seed Trait Technology</label>
                    <select className="w-full p-2 border border-red-300 rounded-md bg-red-50" value={soybeanInput.seedTrait} onChange={e => setSoybeanInput({...soybeanInput, seedTrait: e.target.value as any})}>
                      <option value="conventional">Conventional (No Traits)</option>
                      <option value="roundup_ready">Roundup Ready</option>
                      <option value="xtend">Xtend (Dicamba tolerant)</option>
                      <option value="enlist">Enlist E3 (2,4-D tolerant)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm mb-1">Timing</label>
                    <select className="w-full p-2 border rounded-md" value={soybeanInput.applicationType} onChange={e => setSoybeanInput({...soybeanInput, applicationType: e.target.value})}>
                      <option value="PRE">PRE</option>
                      <option value="POST">POST</option>
                    </select>
                  </div>
              </div>
              <div className="grid grid-cols-2 gap-4 mt-4 border-t pt-4">
                 <label className="block text-sm mb-1">Days Until Harvest (PHI) <input type="number" className="w-20 ml-2 border rounded p-1" value={soybeanInput.daysToHarvest} onChange={e => setSoybeanInput({...soybeanInput, daysToHarvest: Number(e.target.value)})}/></label>
                 <label className="flex items-center space-x-2"><input type="checkbox" checked={soybeanInput.isRUPApplicator} onChange={e => setSoybeanInput({...soybeanInput, isRUPApplicator: e.target.checked})}/><span>Has RUP License</span></label>
              </div>
            </div>
          )}

          {guideType === 'cotton_insects' && (
             <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm mb-1">Pest Target</label>
                      <select className="w-full p-2 border rounded-md" value={cottonInput.pestTarget} onChange={e => setCottonInput({...cottonInput, pestTarget: e.target.value})}>
                        <option value="bollworm">Bollworm / Tobacco Budworm</option>
                        <option value="aphids">Cotton Aphids</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-red-600 mb-1">Scouting Threshold</label>
                      <label className="flex items-center space-x-2 p-2 border border-red-300 rounded-md bg-red-50">
                          <input type="checkbox" checked={cottonInput.thresholdMet} onChange={e => setCottonInput({...cottonInput, thresholdMet: e.target.checked})}/>
                          <span>Economic Threshold Met (e.g. 10 larvae/100 plants)</span>
                      </label>
                    </div>
                </div>
                <div className="grid grid-cols-2 gap-4 mt-4 border-t pt-4">
                   <label className="flex items-center space-x-2"><input type="checkbox" checked={cottonInput.beneficialsPresentToSave} onChange={e => setCottonInput({...cottonInput, beneficialsPresentToSave: e.target.checked})}/><span className="text-green-700">Beneficials present to save</span></label>
                   <label className="block text-sm mb-1">Days Until Harvest <input type="number" className="w-20 ml-2 border rounded p-1" value={cottonInput.daysToHarvest} onChange={e => setCottonInput({...cottonInput, daysToHarvest: Number(e.target.value)})}/></label>
                </div>
             </div>
          )}

        </section>

        <button onClick={handleRun} className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-lg shadow-lg text-lg">
          Run Deterministic Screen
        </button>

        {results.length > 0 && (
          <section className="space-y-6">
            <div className="bg-green-50 border-2 border-green-500 rounded-lg p-6">
              <h3 className="text-xl font-bold text-green-800 flex items-center gap-2 mb-4">
                <CheckCircle className="h-6 w-6" /> Recommended Products ({recommended.length})
              </h3>
              {recommended.length === 0 ? (
                <p className="text-green-700">No products passed all hard gates.</p>
              ) : (
                <ul className="space-y-3">
                  {recommended.map(r => (
                    <li key={r.uniqueId} className="bg-white p-4 rounded shadow-sm border border-green-200 flex justify-between">
                      <span className="font-bold text-lg">{r.tradeName}</span>
                      <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full font-mono text-sm">{r.rate}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="bg-red-50 border border-red-200 rounded-lg p-6">
              <h3 className="text-lg font-bold text-red-800 flex items-center gap-2 mb-4">
                <XCircle className="h-5 w-5" /> Rejected Products ({rejected.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {rejected.slice(0, 10).map(r => (
                  <div key={r.uniqueId} className="bg-white p-3 rounded shadow-sm border border-red-100 text-sm">
                    <span className="font-bold text-gray-800">{r.tradeName}</span>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {r.rejectReasons.slice(0, 2).map((reason, i) => (
                        <span key={i} className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                          {reason.gateName}: {reason.reason}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}

export default App;
