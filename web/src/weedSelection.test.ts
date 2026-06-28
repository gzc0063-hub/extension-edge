import { describe, expect, it } from 'vitest'
import { addWeedSelection, filterWeedOptions, removeWeedSelection, resolveWeedOption } from './weedSelection'

const weedOptions = ['BHHGR', 'crabgrass', 'pigweed', 'Palmer amaranth', 'johnsongrass']

describe('weed selection helpers', () => {
  it('adds typed weeds once and caps selections at five', () => {
    const selected = ['BHHGR', 'crabgrass', 'pigweed', 'Palmer amaranth', 'johnsongrass']

    expect(addWeedSelection(selected, 'sicklepod')).toEqual(selected)
    expect(addWeedSelection(['BHHGR'], 'BHHGR')).toEqual(['BHHGR'])
    expect(addWeedSelection(['BHHGR'], '  sicklepod  ')).toEqual(['BHHGR', 'sicklepod'])
  })

  it('filters weed options from a partial typed query and selected values', () => {
    expect(filterWeedOptions(weedOptions, 'gra', ['BHHGR'])).toEqual(['crabgrass', 'johnsongrass'])
  })

  it('resolves typed labels to stored weed keys', () => {
    expect(resolveWeedOption(['palmer_amaranth', 'morningglory'], 'Palmer amaranth')).toBe('palmer_amaranth')
    expect(resolveWeedOption(['BHHGR'], 'bhhgr')).toBe('BHHGR')
    expect(resolveWeedOption(['crabgrass'], 'unknown weed')).toBeUndefined()
  })

  it('removes selected weeds', () => {
    expect(removeWeedSelection(['BHHGR', 'crabgrass'], 'BHHGR')).toEqual(['crabgrass'])
  })
})
