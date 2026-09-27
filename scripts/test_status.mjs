import { test } from 'node:test';
import assert from 'node:assert/strict';
import { statusSummary } from '../assets/status.mjs';

test('reports the public service state without assuming availability', () => {
  for (const state of ['operational', 'degraded', 'downtime', 'maintenance']) {
    assert.equal(statusSummary({ data: { attributes: { aggregate_state: state } } }).state, state);
  }
  for (const payload of [null, {}, { data: {} }, { data: { attributes: { aggregate_state: 'new_state' } } }]) {
    assert.equal(statusSummary(payload).state, 'unknown');
    assert.doesNotMatch(statusSummary(payload).label, /operational/i);
  }
});
