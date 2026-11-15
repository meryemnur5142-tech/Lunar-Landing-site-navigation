import assert from 'node:assert/strict';
import {criteria,craters,zonesFor} from './dist/data.js';
import {rankZones,scoreZone,profileFor} from './dist/scoring.js';
assert.equal(criteria.reduce((s,c)=>s+c.weight,0),1);
for(const crater of craters){const zones=zonesFor(crater),ranked=rankZones(zones);assert.equal(ranked.length,4);assert.equal(new Set(ranked.map(z=>z.total)).size,4);for(const z of ranked){assert.ok(Math.hypot(z.x,z.y)<crater.diameter/2);assert.ok(z.total>=0&&z.total<=100);assert.ok(Math.abs(z.total-z.contributions.reduce((s,c)=>s+c.contribution,0))<1e-10);assert.deepEqual(scoreZone(z),scoreZone(z));for(const other of zones)assert.ok(Math.hypot(z.x-other.x,z.y-other.y)<8)}assert.notDeepEqual(profileFor(ranked[0]),profileFor(ranked[1]));assert.equal(ranked[0].id,'A')}
const fixture={roughness:.10,slopeDeg:1.4,rockCover:.12,hazardFree:.96,edgeKm:31.5,referenceClearance:35,stability:91};assert.ok(Math.abs(scoreZone(fixture).total-92.85)<1e-10);assert.throws(()=>scoreZone({...fixture,slopeDeg:NaN}));assert.ok(scoreZone({...fixture,slopeDeg:3}).total<scoreZone(fixture).total);
console.log('PASS: six weights, explicit 92.85 reference, deterministic ranking, four distinct scores, crater containment, cluster proximity, profile changes, invalid inputs, slope sensitivity.');
