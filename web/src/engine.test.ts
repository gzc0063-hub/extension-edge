import { describe, it, expect } from 'vitest';
import { runDeterministicEngine, type GrowerInput } from './engine';

describe('Deterministic Engine', () => {

    it('Scenario 1: Lactating dairy wait rejects product', () => {
        const input: GrowerInput = {
            forageType: 'bermuda_maint',
            applicationType: 'POST',
            weedsPresent: ['BHHGR'],
            hasLactatingDairy: true,
            hasLegumesToSave: false,
            isRUPApplicator: true,
            willExportHayOrManure: false,
            willSlaughterWithinWait: false
        };
        const results = runDeterministicEngine(input);

        // Find Crossbow
        const crossbow = results.find(r => r.tradeName === 'Crossbow');
        expect(crossbow).toBeDefined();
        expect(crossbow!.status).toBe('REJECTED');
        expect(crossbow!.rejectReasons.some(rr => rr.gateName === 'Dairy Wait')).toBe(true);
    });

    it('Scenario 2: Legume injury rejects product', () => {
        const input: GrowerInput = {
            forageType: 'bermuda_maint',
            applicationType: 'POST',
            weedsPresent: ['BHHGR'],
            hasLactatingDairy: false,
            hasLegumesToSave: true, // Key flag
            isRUPApplicator: true,
            willExportHayOrManure: false,
            willSlaughterWithinWait: false
        };
        const results = runDeterministicEngine(input);

        // ForeFront HL/GrazonNext HL kills legumes
        const grazon = results.find(r => r.tradeName === 'ForeFront HL/GrazonNext HL');
        expect(grazon).toBeDefined();
        expect(grazon!.status).toBe('REJECTED');
        expect(grazon!.rejectReasons.some(rr => rr.gateName === 'Legume Safety')).toBe(true);
    });

    it('Scenario 3: RUP applicator gate', () => {
        const input: GrowerInput = {
            forageType: 'bermuda_maint',
            applicationType: 'POST',
            weedsPresent: ['BHHGR'],
            hasLactatingDairy: false,
            hasLegumesToSave: false,
            isRUPApplicator: false, // NO RUP license
            willExportHayOrManure: false,
            willSlaughterWithinWait: false
        };
        const results = runDeterministicEngine(input);

        const rupRejects = results.filter(r => r.rejectReasons.some(rr => rr.gateName === 'RUP Applicator'));
        expect(rupRejects.length).toBeGreaterThan(0);
        expect(rupRejects[0].status).toBe('REJECTED');
    });

});
