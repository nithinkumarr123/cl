import React, { useState } from 'react';
import api from '../services/api';

const codes = ['PVS1', 'PS1', 'PS2', 'PS3', 'PS4', 'PM1', 'PM2', 'PM3', 'PM4', 'PM5', 'PM6',
  'PP1', 'PP2', 'PP3', 'PP4', 'BA1', 'BS1', 'BS2', 'BS3', 'BS4', 'BP1', 'BP2', 'BP3', 'BP4', 'BP5', 'BP7'];
const emptyCriterion = () => ({ code: 'PS3', strength: 'strong', rationale: '', source_url: '', evidence_group: '' });

export default function ACMGReview({ variant, assessment, onAssessed }) {
  const [reviewer, setReviewer] = useState('');
  const [condition, setCondition] = useState('');
  const [version, setVersion] = useState('');
  const [specification, setSpecification] = useState('');
  const [reviewedOn, setReviewedOn] = useState('');
  const [criteria, setCriteria] = useState([]);
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const update = (index, key, value) => setCriteria(rows => rows.map((row, i) => i === index ? { ...row, [key]: value } : row));
  const assess = async () => {
    setBusy(true); setError('');
    try {
      const { data } = await api.post('/acmg/assess', { ...variant, acmg_review: {
        reviewer, condition, reviewed_on: reviewedOn, specification_url: specification,
        specification_version: version, evidence_independence_reviewed: confirmed, criteria,
        inheritance: 'autosomal_dominant', context: 'germline',
      } });
      onAssessed(data);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail.map(item => `${item.loc.join('.')}: ${item.msg}`).join('; ')
        : detail || err.message);
    } finally { setBusy(false); }
  };
  return <div className="panel">
    <div className="panel-header"><h3>ACMG evidence assessment</h3></div>
    <div className="panel-body">
      <p>{assessment.summary}</p>
      <p>Status: {assessment.assessment_status?.replaceAll('_', ' ')}</p>
      {assessment.matched_rules?.map(rule => <p key={rule}>{rule}</p>)}
      {assessment.review && <p>Reviewed by {assessment.review.reviewer} on {assessment.review.reviewed_on} for {assessment.review.condition}.</p>}
      {assessment.applied_criteria?.map(item => <p key={item.code}>
        <strong>{item.code} ({item.strength.replaceAll('_', ' ')})</strong>: {item.rationale}{' '}
        <a href={item.source_url} target="_blank" rel="noreferrer">Evidence source</a>
      </p>)}
      <details style={{ marginTop: 16 }}>
        <summary>Enter reviewed germline evidence</summary>
        <p>This calculator combines supplied evidence using ACMG/AMP 2015 Table 5. It does not curate gene-specific criteria or establish a diagnosis. Enter only criteria whose applicability, strength, and independence have been reviewed. Current model deltas are not validated ACMG criteria.</p>
        <p><a href="https://cspec.genome.network/cspec/ui/svi/summary" target="_blank" rel="noreferrer">BRCA1/TP53 ClinGen specifications</a></p>
        <div className="form-grid" style={{ marginTop: 12 }}>
          <label>Reviewer<input className="input" value={reviewer} onChange={e => setReviewer(e.target.value)} /></label>
          <label>Condition<input className="input" value={condition} onChange={e => setCondition(e.target.value)} /></label>
          <label>Review date<input className="input" type="date" value={reviewedOn} onChange={e => setReviewedOn(e.target.value)} /></label>
          <label>Specification version<input className="input" value={version} onChange={e => setVersion(e.target.value)} /></label>
          <label>Specification URL<input className="input" type="url" value={specification} onChange={e => setSpecification(e.target.value)} /></label>
        </div>
        {criteria.map((item, index) => <fieldset key={index} style={{ marginTop: 16, padding: 12 }}>
          <legend>Criterion {index + 1}</legend>
          <div className="form-grid">
            <label>Code<select className="input" value={item.code} onChange={e => update(index, 'code', e.target.value)}>{codes.map(code => <option key={code}>{code}</option>)}</select></label>
            <label>Assessed strength<select className="input" value={item.strength} onChange={e => update(index, 'strength', e.target.value)}>{['very_strong', 'strong', 'moderate', 'supporting', 'stand_alone'].map(value => <option key={value} value={value}>{value.replaceAll('_', ' ')}</option>)}</select></label>
            <label>Evidence source URL<input className="input" type="url" value={item.source_url} onChange={e => update(index, 'source_url', e.target.value)} /></label>
            <label>Independent evidence group<input className="input" value={item.evidence_group} onChange={e => update(index, 'evidence_group', e.target.value)} placeholder="Unique dataset or observation" /></label>
          </div>
          <label>Rationale<textarea className="input" value={item.rationale} onChange={e => update(index, 'rationale', e.target.value)} /></label>
          <button className="preset-btn" type="button" onClick={() => setCriteria(rows => rows.filter((_, i) => i !== index))}>Remove criterion</button>
        </fieldset>)}
        <button type="button" className="preset-btn" style={{ marginTop: 12 }} onClick={() => setCriteria(rows => [...rows, emptyCriterion()])}>Add criterion</button>
        <label style={{ display: 'block', marginTop: 12 }}><input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} /> I reviewed criterion applicability and strength for this gene and condition, and excluded dependent or duplicate evidence.</label>
        <button type="button" className="analyze-btn" style={{ marginTop: 12 }} disabled={busy || !confirmed || !criteria.length || !reviewer || !condition || !version || !specification || !reviewedOn} onClick={assess}>{busy ? 'Assessing...' : 'Calculate evidence category'}</button>
        {error && <p role="alert" className="error-message">{error}</p>}
      </details>
      {assessment.warnings?.map(warning => <p key={warning} style={{ marginTop: 8, color: '#94a3b8' }}>{warning}</p>)}
    </div>
  </div>;
}
