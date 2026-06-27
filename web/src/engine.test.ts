import { describe, it, expect } from 'vitest';
import { evaluatePastureWeeds, evaluateSoybeanWeeds, evaluateCottonInsects, type PastureInput, type SoybeanWeedInput, type CottonInsectInput, type RecommendationResult } from './engine';

describe('Modular Deterministic Engine', () => {

    it('Pasture: Lactating dairy wait rejects product', () => {
        const input: PastureInput = {
            forageType: 'bermuda_maint',
            applicationType: 'POST',
            weedsPresent: ['BHHGR'],
            hasLactatingDairy: true,
            hasLegumesToSave: false,
            isRUPApplicator: true,
            willExportHayOrManure: false
        };
        const results = evaluatePastureWeeds(input);
        const crossbow = results.find((r: RecommendationResult) => r.tradeName === 'Crossbow');
        expect(crossbow).toBeDefined();
        expect(crossbow!.status).toBe('REJECTED');
        expect(crossbow!.rejectReasons.some((rr: any) => rr.gateName === 'Dairy Wait')).toBe(true);
    });

    it('Soybean: Seed trait incompatibility rejects product', () => {
        const input: SoybeanWeedInput = {
            applicationType: 'POST',
            seedTrait: 'enlist',
            daysToHarvest: 100,
            isRUPApplicator: true
        };
        const results = evaluateSoybeanWeeds(input);

        // Engenia requires Xtend trait. User planted Enlist. Should be rejected to save crop from death.
        const engenia = results.find((r: RecommendationResult) => r.tradeName === 'Engenia');
        expect(engenia).toBeDefined();
        expect(engenia!.status).toBe('REJECTED');
        expect(engenia!.rejectReasons.some((rr: any) => rr.gateName === 'Trait Tech')).toBe(true);

        // Enlist One requires Enlist trait. Should be recommended.
        const enlistOne = results.find((r: RecommendationResult) => r.tradeName === 'Enlist One');
        expect(enlistOne!.status).toBe('RECOMMEND');
    });

    it('Cotton: Insect Threshold not met rejects chemical application', () => {
        const input: CottonInsectInput = {
            pestTarget: 'bollworm',
            thresholdMet: false, // NOT MET
            beneficialsPresentToSave: false,
            daysToHarvest: 100,
            isRUPApplicator: true
        };
        const results = evaluateCottonInsects(input);

        // Vantacor should be rejected because we shouldn't spray if threshold isn't met
        const vantacor = results.find((r: RecommendationResult) => r.tradeName === 'VANTACOR');
        expect(vantacor).toBeDefined();
        expect(vantacor!.status).toBe('REJECTED');
        expect(vantacor!.rejectReasons.some((rr: any) => rr.gateName === 'Threshold')).toBe(true);
    });
});
