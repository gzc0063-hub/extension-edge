import { useState } from 'react';
import {
    evaluatePastureWeeds, evaluateSoybeanWeeds, evaluateCornWeeds, evaluatePeanutWeeds, evaluateCottonWeeds, evaluateCottonInsects,
    getCottonInsectPestOptions, getRowCropWeedOptions,
    type GuideType, type RowCropGuideType, type RecommendationResult, type PastureInput, type RowCropWeedInput, type CottonInsectInput, type EfficacyRecord
} from './engine';
import { CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import efficacyData from './data/efficacy.json';
import { addWeedSelection, filterWeedOptions, MAX_WEED_SELECTIONS, removeWeedSelection, resolveWeedOption } from './weedSelection';

const ALL_PASTURE_WEEDS = Array.from(new Set((efficacyData as EfficacyRecord[]).map((e) => e.weed_id))).sort();
const ROW_CROP_GUIDES: RowCropGuideType[] = ['soybean_weeds', 'corn_weeds', 'cotton_weeds', 'peanut_weeds'];
const COTTON_INSECT_PEST_OPTIONS = getCottonInsectPestOptions();

function isRowCropGuide(guide: GuideType): guide is RowCropGuideType {
  return ROW_CROP_GUIDES.includes(guide as RowCropGuideType);
}

function App() {
  const [guideType, setGuideType] = useState<GuideType>('pasture_weeds');

  const [pastureInput, setPastureInput] = useState<PastureInput>({
    forageType: 'bermuda_maint', applicationType: 'POST', weedsPresent: [], hasLactatingDairy: false, hasLegumesToSave: false, isRUPApplicator: true, willExportHayOrManure: false
  });

  const [rowCropInput, setRowCropInput] = useState<RowCropWeedInput>({
    applicationType: 'POST', seedTrait: 'conventional', soilTexture: 'unknown', nextPlannedCrop: 'Unknown', daysToHarvest: 100, isRUPApplicator: true, weedsPresent: []
  });

  const [cottonInsectInput, setCottonInsectInput] = useState<CottonInsectInput>({
    pestTarget: 'bollworm', thresholdMet: false, beneficialsPresentToSave: false, daysToHarvest: 100, isRUPApplicator: true
  });

  const [results, setResults] = useState<RecommendationResult[]>([]);
  const [pastureWeedQuery, setPastureWeedQuery] = useState('');
  const [rowWeedQuery, setRowWeedQuery] = useState('');

  const handleRun = () => {
    if (guideType === 'pasture_weeds') setResults(evaluatePastureWeeds(pastureInput));
    if (guideType === 'soybean_weeds') setResults(evaluateSoybeanWeeds(rowCropInput));
    if (guideType === 'corn_weeds') setResults(evaluateCornWeeds(rowCropInput));
    if (guideType === 'cotton_weeds') setResults(evaluateCottonWeeds(rowCropInput));
    if (guideType === 'peanut_weeds') setResults(evaluatePeanutWeeds(rowCropInput));
    if (guideType === 'cotton_insects') setResults(evaluateCottonInsects(cottonInsectInput));
  };

  const addPastureWeed = (weed: string) => {
    const resolvedWeed = resolveWeedOption(ALL_PASTURE_WEEDS, weed) || weed;
    setPastureInput(prev => ({
      ...prev,
      weedsPresent: addWeedSelection(prev.weedsPresent, resolvedWeed)
    }));
    setPastureWeedQuery('');
  };

  const removePastureWeed = (weed: string) => {
    setPastureInput(prev => ({
      ...prev,
      weedsPresent: removeWeedSelection(prev.weedsPresent, weed)
    }));
  };

  const addRowCropWeed = (weed: string) => {
    const rowCropWeedOptions = isRowCropGuide(guideType) ? getRowCropWeedOptions(guideType) : [];
    const resolvedWeed = resolveWeedOption(rowCropWeedOptions, weed) || weed;
    setRowCropInput(prev => ({
      ...prev,
      weedsPresent: addWeedSelection(prev.weedsPresent, resolvedWeed)
    }));
    setRowWeedQuery('');
  };

  const removeRowCropWeed = (weed: string) => {
    setRowCropInput(prev => ({
      ...prev,
      weedsPresent: removeWeedSelection(prev.weedsPresent, weed)
    }));
  };

  const recommended = results.filter(r => r.status === 'RECOMMEND');
  const rejected = results.filter(r => r.status === 'REJECTED');

  const isRowCropWeeds = isRowCropGuide(guideType);
  const rowCropWeedOptions = isRowCropWeeds ? getRowCropWeedOptions(guideType) : [];
  const pastureWeedSuggestions = filterWeedOptions(ALL_PASTURE_WEEDS, pastureWeedQuery, pastureInput.weedsPresent);
  const rowWeedSuggestions = filterWeedOptions(rowCropWeedOptions, rowWeedQuery, rowCropInput.weedsPresent);
  const canAddPastureWeed = pastureInput.weedsPresent.length < MAX_WEED_SELECTIONS;
  const canAddRowWeed = rowCropInput.weedsPresent.length < MAX_WEED_SELECTIONS;

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
                  const nextGuide = e.target.value as GuideType;
                  setGuideType(nextGuide);
                  if (isRowCropGuide(nextGuide)) {
                    setRowCropInput(prev => ({ ...prev, weedsPresent: [] }));
                    setRowWeedQuery('');
                  }
                  if (nextGuide === 'pasture_weeds') {
                    setPastureWeedQuery('');
                  }
                  setResults([]);
              }}
            >
              <optgroup label="Pasture & Forage">
                <option value="pasture_weeds">Pasture & Forage Weed Control 2026</option>
              </optgroup>
              <optgroup label="Row Crops (Weed Control)">
                <option value="soybean_weeds">Soybean Weed Control 2025</option>
                <option value="cotton_weeds">Cotton Weed Control 2025</option>
                <option value="corn_weeds">Corn Weed Control 2025</option>
                <option value="peanut_weeds">Peanut Weed Control 2025</option>
              </optgroup>
              <optgroup label="Row Crops (Insect Control)">
                <option value="cotton_insects">Cotton Insect Control 2026</option>
              </optgroup>
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
                <div className="mb-2 flex items-center justify-between gap-3">
                  <label className="block text-sm font-medium">Target Weeds</label>
                  <span className="text-sm text-gray-500">{pastureInput.weedsPresent.length}/{MAX_WEED_SELECTIONS} selected</span>
                </div>
                <div className="space-y-3 rounded-md border bg-gray-50 p-3">
                  <div className="flex flex-col gap-2 sm:flex-row">
                    <input
                      className="min-w-0 flex-1 rounded-md border bg-white p-2"
                      value={pastureWeedQuery}
                      onChange={(e) => setPastureWeedQuery(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          addPastureWeed(pastureWeedQuery);
                        }
                      }}
                      placeholder="Type a weed name, pest, or code"
                      disabled={!canAddPastureWeed}
                    />
                    <button
                      type="button"
                      onClick={() => addPastureWeed(pastureWeedQuery)}
                      disabled={!canAddPastureWeed || pastureWeedQuery.trim().length === 0}
                      className="rounded-md bg-green-700 px-4 py-2 font-semibold text-white transition-colors hover:bg-green-800 disabled:cursor-not-allowed disabled:bg-gray-300 disabled:text-gray-600"
                    >
                      Add weed
                    </button>
                  </div>

                  {pastureInput.weedsPresent.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {pastureInput.weedsPresent.map(weed => (
                        <button key={weed} type="button" onClick={() => removePastureWeed(weed)} className="rounded-full bg-green-700 px-3 py-1 text-sm font-medium text-white transition-colors hover:bg-green-800">
                          {weed} x
                        </button>
                      ))}
                    </div>
                  )}

                  <div className="flex max-h-40 flex-wrap gap-2 overflow-y-auto">
                  {pastureWeedSuggestions.map(weed => (
                    <button key={weed} type="button" onClick={() => addPastureWeed(weed)} disabled={!canAddPastureWeed} className="px-3 py-1 rounded-full text-sm border bg-white text-gray-700 hover:bg-gray-100 disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-400">
                      {weed}
                    </button>
                  ))}
                  {pastureWeedSuggestions.length === 0 && (
                    <span className="text-sm text-gray-500">No matching saved weed names. You can add the typed value.</span>
                  )}
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 mt-4">
                 <label className="flex items-center space-x-2"><input type="checkbox" checked={pastureInput.isRUPApplicator} onChange={e => setPastureInput({...pastureInput, isRUPApplicator: e.target.checked})}/><span>Has RUP License</span></label>
                 <label className="flex items-center space-x-2"><input type="checkbox" checked={pastureInput.hasLactatingDairy} onChange={e => setPastureInput({...pastureInput, hasLactatingDairy: e.target.checked})}/><span className="text-red-600">Dairy on field</span></label>
                 <label className="flex items-center space-x-2"><input type="checkbox" checked={pastureInput.hasLegumesToSave} onChange={e => setPastureInput({...pastureInput, hasLegumesToSave: e.target.checked})}/><span className="text-red-600">Legumes to save</span></label>
              </div>
            </div>
          )}

          {isRowCropWeeds && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                  {(guideType === 'soybean_weeds' || guideType === 'cotton_weeds') && (
                      <div>
                        <label className="block text-sm font-bold text-red-600 mb-1">Planted Seed Trait</label>
                        <select className="w-full p-2 border border-red-300 rounded-md bg-red-50" value={rowCropInput.seedTrait} onChange={e => setRowCropInput({...rowCropInput, seedTrait: e.target.value})}>
                          <option value="conventional">Conventional (No Traits)</option>
                          <option value="roundup_ready">Roundup Ready</option>
                          <option value="xtend">Xtend (Dicamba tolerant)</option>
                          <option value="enlist">Enlist (2,4-D tolerant)</option>
                        </select>
                      </div>
                  )}
                  <div>
                    <label className="block text-sm mb-1">Timing</label>
                    <select className="w-full p-2 border rounded-md" value={rowCropInput.applicationType} onChange={e => setRowCropInput({...rowCropInput, applicationType: e.target.value})}>
                      <option value="BURNDOWN">BURNDOWN</option>
                      <option value="PRE">PRE</option>
                      <option value="POST">POST</option>
                    </select>
                  </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mt-2">
                 <div>
                    <label className="block text-sm mb-1">Soil Texture</label>
                    <select className="w-full p-2 border rounded-md" value={rowCropInput.soilTexture} onChange={e => setRowCropInput({...rowCropInput, soilTexture: e.target.value as RowCropWeedInput['soilTexture']})}>
                      <option value="unknown">Unknown</option>
                      <option value="sand">Coarse (Sand/Loamy Sand)</option>
                      <option value="loam">Medium (Loam/Silt)</option>
                      <option value="clay">Fine (Clay)</option>
                    </select>
                 </div>
                 <div>
                    <label className="block text-sm mb-1">Next Planned Crop</label>
                    <input type="text" className="w-full p-2 border rounded-md" placeholder="e.g., Cotton, Corn, Wheat" value={rowCropInput.nextPlannedCrop} onChange={e => setRowCropInput({...rowCropInput, nextPlannedCrop: e.target.value})} />
                 </div>
              </div>

              <div>
                <div className="mb-2 flex items-center justify-between gap-3">
                  <label className="block text-sm font-medium">Target Weeds</label>
                  <span className="text-sm text-gray-500">{rowCropInput.weedsPresent.length}/{MAX_WEED_SELECTIONS} selected</span>
                </div>
                <div className="space-y-3 rounded-md border bg-gray-50 p-3">
                  <div className="flex flex-col gap-2 sm:flex-row">
                    <input
                      className="min-w-0 flex-1 rounded-md border bg-white p-2"
                      value={rowWeedQuery}
                      onChange={(e) => setRowWeedQuery(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          addRowCropWeed(rowWeedQuery);
                        }
                      }}
                      placeholder="Type a weed name, pest, or code"
                      disabled={!canAddRowWeed}
                    />
                    <button
                      type="button"
                      onClick={() => addRowCropWeed(rowWeedQuery)}
                      disabled={!canAddRowWeed || rowWeedQuery.trim().length === 0}
                      className="rounded-md bg-green-700 px-4 py-2 font-semibold text-white transition-colors hover:bg-green-800 disabled:cursor-not-allowed disabled:bg-gray-300 disabled:text-gray-600"
                    >
                      Add weed
                    </button>
                  </div>

                  {rowCropInput.weedsPresent.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {rowCropInput.weedsPresent.map(weed => (
                        <button key={weed} type="button" onClick={() => removeRowCropWeed(weed)} className="rounded-full bg-green-700 px-3 py-1 text-sm font-medium text-white transition-colors hover:bg-green-800">
                          {weed.replace('_', ' ')} x
                        </button>
                      ))}
                    </div>
                  )}

                <div className="flex flex-wrap gap-2">
                  {rowWeedSuggestions.map(weed => (
                    <button key={weed} type="button" onClick={() => addRowCropWeed(weed)} disabled={!canAddRowWeed} className="px-3 py-1 rounded-full text-sm border bg-white text-gray-700 hover:bg-gray-100 disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-400">
                      {weed.replace('_', ' ')}
                    </button>
                  ))}
                  {rowWeedSuggestions.length === 0 && (
                    <span className="text-sm text-gray-500">No matching saved weed names. You can add the typed value.</span>
                  )}
                </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mt-4 border-t pt-4">
                 <label className="block text-sm mb-1">Days Until Harvest (PHI) <input type="number" className="w-20 ml-2 border rounded p-1" value={rowCropInput.daysToHarvest} onChange={e => setRowCropInput({...rowCropInput, daysToHarvest: Number(e.target.value)})}/></label>
                 <label className="flex items-center space-x-2"><input type="checkbox" checked={rowCropInput.isRUPApplicator} onChange={e => setRowCropInput({...rowCropInput, isRUPApplicator: e.target.checked})}/><span>Has RUP License</span></label>
              </div>
            </div>
          )}

          {guideType === 'cotton_insects' && (
             <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm mb-1">Pest Target</label>
                      <select className="w-full p-2 border rounded-md" value={cottonInsectInput.pestTarget} onChange={e => setCottonInsectInput({...cottonInsectInput, pestTarget: e.target.value})}>
                        {COTTON_INSECT_PEST_OPTIONS.map((pest) => (
                          <option key={pest} value={pest}>{pest.replace(/_/g, ' ')}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-bold text-red-600 mb-1">Scouting Threshold</label>
                      <label className="flex items-center space-x-2 p-2 border border-red-300 rounded-md bg-red-50">
                          <input type="checkbox" checked={cottonInsectInput.thresholdMet} onChange={e => setCottonInsectInput({...cottonInsectInput, thresholdMet: e.target.checked})}/>
                          <span>Economic Threshold Met (e.g. 10 larvae/100 plants)</span>
                      </label>
                    </div>
                </div>
                <div className="grid grid-cols-2 gap-4 mt-4 border-t pt-4">
                   <label className="flex items-center space-x-2"><input type="checkbox" checked={cottonInsectInput.beneficialsPresentToSave} onChange={e => setCottonInsectInput({...cottonInsectInput, beneficialsPresentToSave: e.target.checked})}/><span className="text-green-700">Beneficials present to save</span></label>
                   <label className="block text-sm mb-1">Days Until Harvest <input type="number" className="w-20 ml-2 border rounded p-1" value={cottonInsectInput.daysToHarvest} onChange={e => setCottonInsectInput({...cottonInsectInput, daysToHarvest: Number(e.target.value)})}/></label>
                </div>
             </div>
          )}

        </section>

        <button
          onClick={handleRun}
          disabled={(guideType === 'pasture_weeds' && pastureInput.weedsPresent.length === 0) || (isRowCropWeeds && rowCropInput.weedsPresent.length === 0)}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-lg shadow-lg text-lg disabled:cursor-not-allowed disabled:bg-gray-400"
        >
          {((guideType === 'pasture_weeds' && pastureInput.weedsPresent.length === 0) || (isRowCropWeeds && rowCropInput.weedsPresent.length === 0)) ? 'Add 1 to 5 target weeds' : 'Run Deterministic Screen'}
        </button>

        {results.length > 0 && (
          <section className="space-y-6">
            <div className="bg-green-50 border-2 border-green-500 rounded-lg p-6">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-4 gap-2">
                  <h3 className="text-xl font-bold text-green-800 flex items-center gap-2">
                    <CheckCircle className="h-6 w-6" /> Recommended Products ({recommended.length})
                  </h3>
                  <div className="text-xs font-bold text-red-700 bg-red-100 px-2 py-1 rounded border border-red-200 uppercase tracking-wide">
                     Disclaimer: Always check labels before use
                  </div>
              </div>
              {recommended.length === 0 ? (
                <p className="text-green-700">No products passed all hard gates.</p>
              ) : (
                <ul className="space-y-3">
                  {recommended.map(r => (
                    <li key={r.uniqueId} className="bg-white p-4 rounded shadow-sm border border-green-200">
                      <div className="flex justify-between items-start">
                          <div>
                            <span className="font-bold text-lg">{r.tradeName}</span>
                            <div className="text-sm text-gray-600 mt-1">
                                <span className="font-semibold">Active Ingredient:</span> {r.activeIngredient}
                                {r.phiDays !== undefined && !isNaN(r.phiDays) && (
                                    <span className="ml-4"><span className="font-semibold">PHI:</span> {r.phiDays} days</span>
                                )}
                            </div>
                            {r.comments && (
                                <div className="text-sm text-gray-700 mt-2 bg-gray-50 p-2 rounded border border-gray-100 italic">
                                    "{r.comments}"
                                </div>
                            )}
                            {r.efficacyRatings && Object.keys(r.efficacyRatings).length > 0 && (
                                <div className="mt-2 flex flex-wrap gap-2 text-xs">
                                    <span className="font-bold text-gray-600 self-center">Control:</span>
                                    {Object.entries(r.efficacyRatings).map(([weed, rating]) => {
                                        const ratingColors: Record<string, string> = { 'E': 'bg-green-200 text-green-900', 'G': 'bg-green-100 text-green-800', 'F': 'bg-yellow-100 text-yellow-800', 'P': 'bg-red-100 text-red-800', 'N': 'bg-gray-200 text-gray-800' };
                                        const css = ratingColors[rating] || 'bg-gray-100';
                                        return <span key={weed} className={`px-2 py-0.5 rounded-full ${css}`}>{weed.replace('_', ' ')}: {rating}</span>
                                    })}
                                </div>
                            )}
                          </div>
                          <span className="bg-green-100 text-green-800 px-3 py-1 rounded-full font-mono text-sm border border-green-200 whitespace-nowrap ml-4 shrink-0">
                             Rate: {r.rate} / acre
                          </span>
                      </div>
                      {r.warnings && r.warnings.length > 0 && (
                          <div className="mt-3 text-sm text-amber-700 bg-amber-50 p-2 rounded flex gap-2 border border-amber-100">
                              <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-amber-500"/>
                              <ul className="list-disc pl-4">
                                {r.warnings.map((w, i) => <li key={i}>{w}</li>)}
                              </ul>
                          </div>
                      )}
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
