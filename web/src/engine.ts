import herbicidesData from './data/herbicides.json';
import efficacyData from './data/efficacy.json';
import soybeanWeedsData from './data/soybean_weeds.json';
import cottonInsectsData from './data/cotton_insects.json';
import cornWeedsData from './data/corn_weeds.json';
import peanutWeedsData from './data/peanut_weeds.json';
import cottonWeedsData from './data/cotton_weeds.json';

export type GuideType = "pasture_weeds" | "soybean_weeds" | "cotton_weeds" | "corn_weeds" | "peanut_weeds" | "cotton_insects";
export type RowCropGuideType = Extract<GuideType, "soybean_weeds" | "cotton_weeds" | "corn_weeds" | "peanut_weeds">;

export interface HerbicideRecord {
    unique_id: string;
    trade_name: string;
    active_ingredient?: string;
    forage_type: string;
    application_type: string;
    rate_per_acre: string;
    RUP_flag: boolean;
    hay_phi_days?: string | number | null;
    lactating_dairy_days?: string;
    legume_sensitivity?: string;
    off_farm_hay_restricted: boolean;
    off_farm_manure_restricted: boolean;
    comments_structured?: string | null;
    comments?: string | null;
}

export interface EfficacyRecord {
    unique_id: string;
    weed_id: string;
    rating: string;
}

export interface RowCropHerbicideRecord {
    unique_id: string;
    trade_name: string;
    active_ingredient?: string;
    application_type: string;
    seed_trait_required?: string;
    rup_flag: boolean;
    phi_days: number;
    rate_per_acre: string;
    soil_texture_restriction?: string | null;
    plantback_restriction?: string | null;
    comments_structured?: string | null;
    comments?: string | null;
    efficacy?: Record<string, string>;
}

export interface CottonInsectRecord {
    unique_id: string;
    trade_name: string;
    active_ingredient?: string;
    pest_target: string;
    economic_threshold_required: boolean;
    beneficials_safe: boolean;
    phi_days: number;
    rup_flag: boolean;
    rate_per_acre: string;
    comments_structured?: string | null;
    comments?: string | null;
}

export interface PastureInput {
    forageType: string;
    applicationType: string;
    weedsPresent: string[];
    hasLactatingDairy: boolean;
    hasLegumesToSave: boolean;
    isRUPApplicator: boolean;
    willExportHayOrManure: boolean;
}

export interface RowCropWeedInput {
    applicationType: string;
    seedTrait: string;
    soilTexture: 'sand' | 'loam' | 'clay' | 'unknown';
    nextPlannedCrop: string;
    daysToHarvest: number;
    isRUPApplicator: boolean;
    weedsPresent: string[];
}

export interface CottonInsectInput {
    pestTarget: string;
    thresholdMet: boolean;
    beneficialsPresentToSave: boolean;
    daysToHarvest: number;
    isRUPApplicator: boolean;
}

export interface RejectionReason {
    reason: string;
    gateName: string;
}

export interface RecommendationResult {
    uniqueId: string;
    tradeName: string;
    activeIngredient: string;
    phiDays?: number;
    rate: string;
    status: 'RECOMMEND' | 'REJECTED' | 'MANUAL_REVIEW';
    rejectReasons: RejectionReason[];
    warnings: string[];
    efficacyRatings?: Record<string, string>;
    comments?: string;
}

const rowCropDataByGuide: Record<RowCropGuideType, RowCropHerbicideRecord[]> = {
    soybean_weeds: soybeanWeedsData as RowCropHerbicideRecord[],
    cotton_weeds: cottonWeedsData as RowCropHerbicideRecord[],
    corn_weeds: cornWeedsData as RowCropHerbicideRecord[],
    peanut_weeds: peanutWeedsData as RowCropHerbicideRecord[],
};

const sortedUnique = (values: string[]): string[] => Array.from(new Set(values.filter(Boolean))).sort();

export const getRowCropWeedOptions = (guideType: RowCropGuideType): string[] => {
    return sortedUnique(rowCropDataByGuide[guideType].flatMap((herbicide) => Object.keys(herbicide.efficacy || {})));
};

export const getCottonInsectPestOptions = (): string[] => {
    return sortedUnique((cottonInsectsData as CottonInsectRecord[]).map((product) => product.pest_target));
};

export const evaluatePastureWeeds = (input: PastureInput): RecommendationResult[] => {
    return (herbicidesData as HerbicideRecord[]).map((herbicide) => {
        let status: RecommendationResult['status'] = 'RECOMMEND';
        const rejectReasons: RejectionReason[] = [];
        const warnings: string[] = [];

        if (herbicide.forage_type !== input.forageType) {
            status = 'REJECTED';
            rejectReasons.push({ reason: `Not labeled for ${input.forageType}`, gateName: 'Forage Type' });
        }
        if (herbicide.application_type !== input.applicationType) {
            status = 'REJECTED';
            rejectReasons.push({ reason: `Not for ${input.applicationType} application`, gateName: 'Application Timing' });
        }
        if (herbicide.RUP_flag === true && !input.isRUPApplicator) {
            status = 'REJECTED';
            rejectReasons.push({ reason: `Requires RUP license`, gateName: 'RUP Applicator' });
        }
        if (input.hasLactatingDairy) {
            if (herbicide.lactating_dairy_days?.toLowerCase() === 'unknown') {
                if (status !== 'REJECTED') status = 'MANUAL_REVIEW';
                rejectReasons.push({ reason: `Unknown dairy wait`, gateName: 'Dairy Unknown' });
            } else if (herbicide.lactating_dairy_days !== '0' && herbicide.lactating_dairy_days?.toLowerCase() !== 'none') {
                 status = 'REJECTED';
                 rejectReasons.push({ reason: `Has dairy wait period`, gateName: 'Dairy Wait' });
            }
        }
        if (input.hasLegumesToSave) {
            const legSens = herbicide.legume_sensitivity?.toLowerCase();
            if (legSens === 'kills' || legSens === 'injures' || legSens === 'injures_recovers') {
                status = 'REJECTED';
                rejectReasons.push({ reason: `Harms legumes`, gateName: 'Legume Safety' });
            } else if (legSens === 'unknown') {
                if (status !== 'REJECTED') status = 'MANUAL_REVIEW';
                rejectReasons.push({ reason: `Unknown legume safety`, gateName: 'Legume Unknown' });
            }
        }
        if (input.willExportHayOrManure) {
            if (herbicide.off_farm_hay_restricted === true || herbicide.off_farm_manure_restricted === true) {
                status = 'REJECTED';
                rejectReasons.push({ reason: `Export restricted`, gateName: 'Export Restrictions' });
            }
        }

        const efficacyRatings: Record<string, string> = {};
        let hasControl = false;

        for (const weed of input.weedsPresent) {
            const efficacyRecord = (efficacyData as EfficacyRecord[]).find((e) => e.unique_id === herbicide.unique_id && e.weed_id === weed);
            if (efficacyRecord) {
                efficacyRatings[weed] = efficacyRecord.rating;
                if (efficacyRecord.rating === 'P' || efficacyRecord.rating === 'N') {
                     warnings.push(`Poor/No control for ${weed}`);
                } else {
                     hasControl = true;
                }
            } else {
                warnings.push(`No efficacy data for ${weed}`);
            }
        }

        if (input.weedsPresent.length > 0 && !hasControl) {
             status = 'REJECTED';
             rejectReasons.push({ reason: `Does not adequately control any of the selected weeds.`, gateName: 'Efficacy Gate' });
        }

        return {
            uniqueId: herbicide.unique_id,
            tradeName: herbicide.trade_name,
            activeIngredient: herbicide.active_ingredient || 'Not listed',
            phiDays: herbicide.hay_phi_days ? parseInt(String(herbicide.hay_phi_days)) : undefined,
            rate: herbicide.rate_per_acre,
            status,
            rejectReasons,
            warnings,
            efficacyRatings,
            comments: herbicide.comments_structured || herbicide.comments || undefined
        };
    });
};

export const evaluateRowCropWeeds = (cropData: RowCropHerbicideRecord[], input: RowCropWeedInput): RecommendationResult[] => {
    return cropData.map((herbicide) => {
        let status: RecommendationResult['status'] = 'RECOMMEND';
        const rejectReasons: RejectionReason[] = [];
        const warnings: string[] = [];

        if (herbicide.application_type !== input.applicationType) {
            status = 'REJECTED';
            rejectReasons.push({ reason: `Not for ${input.applicationType}`, gateName: 'Timing' });
        }

        if (herbicide.seed_trait_required && herbicide.seed_trait_required !== 'conventional' && herbicide.seed_trait_required !== 'none') {
            if (!(input.seedTrait === 'xtend' && herbicide.seed_trait_required === 'roundup_ready') &&
                !(input.seedTrait === 'enlist' && herbicide.seed_trait_required === 'roundup_ready')) {
                if (herbicide.seed_trait_required !== input.seedTrait) {
                    status = 'REJECTED';
                    rejectReasons.push({ reason: `KILLS crop. Requires ${herbicide.seed_trait_required} trait.`, gateName: 'Trait Tech' });
                }
            }
        }

        if (herbicide.rup_flag && !input.isRUPApplicator) {
            status = 'REJECTED';
            rejectReasons.push({ reason: `Requires RUP license`, gateName: 'RUP Applicator' });
        }

        if (input.daysToHarvest < herbicide.phi_days) {
            status = 'REJECTED';
            rejectReasons.push({ reason: `PHI is ${herbicide.phi_days} days`, gateName: 'PHI Limit' });
        }

        // Soil Texture Warning Rule
        if (input.applicationType === 'PRE') {
            if (herbicide.soil_texture_restriction) {
                if (input.soilTexture === 'unknown') {
                    warnings.push(`Soil Restrictions Apply: ${herbicide.soil_texture_restriction}`);
                } else if (input.soilTexture === 'sand' && herbicide.soil_texture_restriction.toLowerCase().includes('coarse')) {
                    warnings.push(`HIGH RISK on Sand: ${herbicide.soil_texture_restriction}`);
                }
            }
        }

        // Plantback Rotation Warning Rule
        if (herbicide.plantback_restriction && herbicide.plantback_restriction.toLowerCase() !== 'none') {
            warnings.push(`Plantback Restriction: ${herbicide.plantback_restriction}`);
        }

        // Efficacy
        const efficacyRatings: Record<string, string> = {};
        let hasControl = false;

        for (const weed of input.weedsPresent) {
            if (herbicide.efficacy && herbicide.efficacy[weed]) {
                const rating = herbicide.efficacy[weed];
                efficacyRatings[weed] = rating;
                if (rating === 'P' || rating === 'N') {
                     warnings.push(`Poor/No control for ${weed}`);
                } else {
                     hasControl = true;
                }
            } else {
                warnings.push(`No efficacy data for ${weed}`);
            }
        }

        if (input.weedsPresent.length > 0 && !hasControl) {
             status = 'REJECTED';
             rejectReasons.push({ reason: `Does not adequately control any of the selected weeds.`, gateName: 'Efficacy Gate' });
        }

        return {
            uniqueId: herbicide.unique_id,
            tradeName: herbicide.trade_name,
            activeIngredient: herbicide.active_ingredient || 'Not listed',
            phiDays: herbicide.phi_days,
            rate: herbicide.rate_per_acre,
            status,
            rejectReasons,
            warnings,
            efficacyRatings,
            comments: herbicide.comments_structured || herbicide.comments || undefined
        };
    });
};

export const evaluateCottonInsects = (input: CottonInsectInput): RecommendationResult[] => {
    return (cottonInsectsData as CottonInsectRecord[]).map((product) => {
        let status: RecommendationResult['status'] = 'RECOMMEND';
        const rejectReasons: RejectionReason[] = [];
        const warnings: string[] = [];

        if (product.pest_target !== input.pestTarget) {
            status = 'REJECTED';
            rejectReasons.push({ reason: `Not labeled for ${input.pestTarget}`, gateName: 'Pest Target' });
        }

        if (product.economic_threshold_required && !input.thresholdMet) {
            status = 'REJECTED';
            rejectReasons.push({ reason: `Scouting threshold not met. Do not spray.`, gateName: 'Threshold' });
        }

        if (input.beneficialsPresentToSave && !product.beneficials_safe) {
            status = 'REJECTED';
            rejectReasons.push({ reason: `Harms beneficials`, gateName: 'Beneficials' });
        }

        if (product.rup_flag && !input.isRUPApplicator) {
            status = 'REJECTED';
            rejectReasons.push({ reason: `Requires RUP license`, gateName: 'RUP Applicator' });
        }

        if (input.daysToHarvest < product.phi_days) {
            status = 'REJECTED';
            rejectReasons.push({ reason: `PHI is ${product.phi_days} days`, gateName: 'PHI Limit' });
        }

        return {
            uniqueId: product.unique_id,
            tradeName: product.trade_name,
            activeIngredient: product.active_ingredient || 'Not listed',
            phiDays: product.phi_days,
            rate: product.rate_per_acre,
            status,
            rejectReasons,
            warnings,
            comments: product.comments_structured || product.comments || undefined
        };
    });
};

// Wrapper functions for specific crops
export const evaluateSoybeanWeeds = (input: RowCropWeedInput) => evaluateRowCropWeeds(rowCropDataByGuide.soybean_weeds, input);
export const evaluateCornWeeds = (input: RowCropWeedInput) => evaluateRowCropWeeds(rowCropDataByGuide.corn_weeds, input);
export const evaluatePeanutWeeds = (input: RowCropWeedInput) => evaluateRowCropWeeds(rowCropDataByGuide.peanut_weeds, input);
export const evaluateCottonWeeds = (input: RowCropWeedInput) => evaluateRowCropWeeds(rowCropDataByGuide.cotton_weeds, input);
