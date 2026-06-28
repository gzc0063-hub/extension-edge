import { describe, it, expect } from 'vitest';
import {
    evaluatePastureWeeds,
    evaluateSoybeanWeeds,
    evaluateCornWeeds,
    evaluateCottonInsects,
    getCottonInsectPestOptions,
    getRowCropWeedOptions,
    type PastureInput,
    type RowCropWeedInput,
    type CottonInsectInput,
    type RecommendationResult
} from './engine';

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
        expect(crossbow!.rejectReasons.some((rr) => rr.gateName === 'Dairy Wait')).toBe(true);
    });

    it('Soybean: Seed trait incompatibility rejects product', () => {
        const input: RowCropWeedInput = {
            applicationType: 'POST',
            seedTrait: 'enlist',
            soilTexture: 'loam',
            nextPlannedCrop: 'corn',
            weedsPresent: ['palmer_amaranth'],
            daysToHarvest: 100,
            isRUPApplicator: true
        };
        const results = evaluateSoybeanWeeds(input);

        // Engenia requires Xtend trait. User planted Enlist. Should be rejected.
        const engenia = results.find((r: RecommendationResult) => r.tradeName === 'Engenia');
        expect(engenia).toBeDefined();
        expect(engenia!.status).toBe('REJECTED');
        expect(engenia!.rejectReasons.some((rr) => rr.gateName === 'Trait Tech')).toBe(true);

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

        const vantacor = results.find((r: RecommendationResult) => r.tradeName === 'VANTACOR');
        expect(vantacor).toBeDefined();
        expect(vantacor!.status).toBe('REJECTED');
        expect(vantacor!.rejectReasons.some((rr) => rr.gateName === 'Threshold')).toBe(true);
    });

    it('exposes weed options from the selected crop dataset', () => {
        expect(getRowCropWeedOptions('soybean_weeds')).toEqual(['crabgrass', 'morningglory', 'palmer_amaranth']);
        expect(getRowCropWeedOptions('peanut_weeds')).toEqual(['florida_beggarweed', 'palmer_amaranth', 'sicklepod']);
    });

    it('exposes cotton insect pest options from the insect dataset', () => {
        expect(getCottonInsectPestOptions()).toEqual(['bollworm']);
    });

    it('Corn: POST morningglory has source-derived options from the guide matrix', () => {
        const input: RowCropWeedInput = {
            applicationType: 'POST',
            seedTrait: 'conventional',
            soilTexture: 'loam',
            nextPlannedCrop: 'Unknown',
            weedsPresent: ['morningglory'],
            daysToHarvest: 100,
            isRUPApplicator: true
        };

        expect(getRowCropWeedOptions('corn_weeds')).toContain('morningglory');
        expect(getRowCropWeedOptions('corn_weeds').length).toBeGreaterThan(25);
        expect(evaluateCornWeeds(input).filter((result) => result.status === 'RECOMMEND').length).toBeGreaterThan(0);
    });
});
