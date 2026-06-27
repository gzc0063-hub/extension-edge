import herbicidesData from './data/herbicides.json';
import efficacyData from './data/efficacy.json';
import soybeanWeedsData from './data/soybean_weeds.json';
import cottonInsectsData from './data/cotton_insects.json';

export type GuideType = "pasture_weeds" | "soybean_weeds" | "cotton_insects";

// --- PAsture Inputs ---
export interface PastureInput {
    forageType: string;
    applicationType: string;
    weedsPresent: string[];
    hasLactatingDairy: boolean;
    hasLegumesToSave: boolean;
    isRUPApplicator: boolean;
    willExportHayOrManure: boolean;
}

// --- Soybean Weed Inputs ---
export interface SoybeanWeedInput {
    applicationType: string;
    seedTrait: 'conventional' | 'roundup_ready' | 'xtend' | 'enlist';
    daysToHarvest: number;
    isRUPApplicator: boolean;
}

// --- Cotton Insect Inputs ---
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
    rate: string;
    status: 'RECOMMEND' | 'REJECTED' | 'MANUAL_REVIEW';
    rejectReasons: RejectionReason[];
    efficacyRatings?: Record<string, string>;
}

export const evaluatePastureWeeds = (input: PastureInput): RecommendationResult[] => {
    return herbicidesData.map((herbicide: any) => {
        let status: RecommendationResult['status'] = 'RECOMMEND';
        const rejectReasons: RejectionReason[] = [];

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
        for (const weed of input.weedsPresent) {
            const efficacyRecord = efficacyData.find((e: any) => e.unique_id === herbicide.unique_id && e.weed_id === weed);
            if (efficacyRecord) {
                efficacyRatings[weed] = efficacyRecord.rating;
                if (efficacyRecord.rating === 'P' || efficacyRecord.rating === 'N') {
                     status = 'REJECTED';
                     rejectReasons.push({ reason: `Poor/No control for ${weed}`, gateName: 'Efficacy Gate' });
                }
            } else {
                status = 'REJECTED';
                rejectReasons.push({ reason: `No efficacy data for ${weed}`, gateName: 'Efficacy Gate' });
            }
        }

        return {
            uniqueId: herbicide.unique_id,
            tradeName: herbicide.trade_name,
            rate: herbicide.rate_per_acre,
            status,
            rejectReasons,
            efficacyRatings
        };
    });
};

export const evaluateSoybeanWeeds = (input: SoybeanWeedInput): RecommendationResult[] => {
    return soybeanWeedsData.map((herbicide: any) => {
        let status: RecommendationResult['status'] = 'RECOMMEND';
        const rejectReasons: RejectionReason[] = [];

        if (herbicide.application_type !== input.applicationType) {
            status = 'REJECTED';
            rejectReasons.push({ reason: `Not for ${input.applicationType}`, gateName: 'Timing' });
        }

        // Critical Trait Technology Gate
        if (herbicide.seed_trait_required !== 'conventional' && herbicide.seed_trait_required !== input.seedTrait) {
            // For example, if Xtend required, but Enlist planted
            // Exception: Roundup Ready can be sprayed on Xtend or Enlist usually,
            // but for this strict demo, we match exactly or 'conventional' means safe for all traits usually,
            // wait, conventional herbicides are safe on traits, but trait herbicides KILL conventional.
            // Simplified logic for demo:
            if (!(input.seedTrait === 'xtend' && herbicide.seed_trait_required === 'roundup_ready') &&
                !(input.seedTrait === 'enlist' && herbicide.seed_trait_required === 'roundup_ready')) {
                if (herbicide.seed_trait_required !== input.seedTrait) {
                    status = 'REJECTED';
                    rejectReasons.push({ reason: `KILLS crop. Requires ${herbicide.seed_trait_required} trait.`, gateName: 'Trait Tech' });
                }
            }
        }

        if (herbicide.RUP_flag && !input.isRUPApplicator) {
            status = 'REJECTED';
            rejectReasons.push({ reason: `Requires RUP license`, gateName: 'RUP Applicator' });
        }

        if (input.daysToHarvest < herbicide.phi_days) {
            status = 'REJECTED';
            rejectReasons.push({ reason: `PHI is ${herbicide.phi_days} days`, gateName: 'PHI Limit' });
        }

        return {
            uniqueId: herbicide.unique_id,
            tradeName: herbicide.trade_name,
            rate: herbicide.rate_per_acre,
            status,
            rejectReasons
        };
    });
};

export const evaluateCottonInsects = (input: CottonInsectInput): RecommendationResult[] => {
    return cottonInsectsData.map((product: any) => {
        let status: RecommendationResult['status'] = 'RECOMMEND';
        const rejectReasons: RejectionReason[] = [];

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
            rate: product.rate_per_acre,
            status,
            rejectReasons
        };
    });
};
