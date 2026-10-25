import React from 'react';
import { AlertCircle, CheckCircle, Info, Shield, Dna, FileText } from 'lucide-react';
import ScoreCard from './ScoreCard';
import ProteinViewer from './ProteinViewer';

const ResultsDisplay = ({ results }) => {
  if (!results) return null;

  const { 
    variant, 
    dna_score, 
    protein_analysis, 
    acmg, 
    transcript,
    clinvar,
    disease_association 
  } = results;

  const getClassificationColor = (classification) => {
    if (classification?.includes('Pathogenic')) return 'text-red-600 bg-red-50 border-red-200';
    if (classification?.includes('Benign')) return 'text-green-600 bg-green-50 border-green-200';
    return 'text-yellow-600 bg-yellow-50 border-yellow-200';
  };

  const getClassificationIcon = (classification) => {
    if (classification?.includes('Pathogenic')) return <AlertCircle className="w-6 h-6" />;
    if (classification?.includes('Benign')) return <CheckCircle className="w-6 h-6" />;
    return <Info className="w-6 h-6" />;
  };

  return (
    <div className="space-y-6">
      {/* Classification Banner */}
      <div className={`border-2 rounded-xl p-6 ${getClassificationColor(acmg.classification)}`}>
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            {getClassificationIcon(acmg.classification)}
          </div>
          <div className="flex-1">
            <h3 className="text-xl font-bold">{acmg.classification || 'ACMG assessment not performed'}</h3>
            <p className="text-sm opacity-75">{acmg.summary}</p>
            <div className="flex items-center space-x-4 mt-2 text-sm">
              <span className="flex items-center space-x-1">
                <Shield className="w-4 h-4" />
                <span>Evidence: {acmg.assessment_status?.replaceAll('_', ' ')}</span>
              </span>
              {disease_association && (
                <span className="flex items-center space-x-1">
                  <Info className="w-4 h-4" />
                  <span>{disease_association}</span>
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Scores Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <ScoreCard
          title="DNA Delta Score"
          score={dna_score.delta_score}
          interpretation={dna_score.interpretation}
        />
        <ScoreCard
          title="Protein Disruption"
          score={protein_analysis.protein_score.delta_score}
          interpretation={protein_analysis.protein_score.impact}
          maxScore={5}
        />
        <div>ACMG category: {acmg.classification || 'Not assessed'}</div>
      </div>

      {/* ACMG Evidence */}
      {acmg.evidence && Object.keys(acmg.evidence).length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-3">ACMG Evidence</h4>
          <div className="space-y-2">
            {Object.entries(acmg.evidence).map(([key, value]) => (
              <div key={key} className="flex items-start space-x-2 text-sm">
                <span className="font-mono font-bold text-indigo-600">{key}:</span>
                <span className="text-gray-600">{Array.isArray(value) ? value.join(', ') : value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Protein Analysis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="bg-white rounded-lg shadow-sm p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Protein Effect</h4>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-500">Mutation Type</dt>
              <dd className="font-medium">{protein_analysis.mutation_type}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">AA Position</dt>
              <dd className="font-mono">{protein_analysis.aa_position}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">AA Change</dt>
              <dd className="font-mono">
                {protein_analysis.ref_aa} → {protein_analysis.alt_aa}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Impact</dt>
              <dd className={`font-medium ${
                protein_analysis.protein_score.impact === 'deleterious' ? 'text-red-600' :
                protein_analysis.protein_score.impact === 'probably_damaging' ? 'text-orange-600' :
                'text-green-600'
              }`}>
                {protein_analysis.protein_score.impact}
              </dd>
            </div>
          </dl>
        </div>

        {/* Transcript Info */}
        <div className="bg-white rounded-lg shadow-sm p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-3">Transcript Information</h4>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-gray-500">Transcript ID</dt>
              <dd className="font-mono text-xs">{transcript.transcript_id}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">Gene</dt>
              <dd className="font-medium">{transcript.gene_symbol}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">CDS Position</dt>
              <dd className="font-mono">{transcript.cds_position}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-500">AA Position</dt>
              <dd className="font-mono">{transcript.aa_position}</dd>
            </div>
          </dl>
        </div>
      </div>

      {/* Protein Sequences */}
      <ProteinViewer
        refProtein={protein_analysis.ref_fragment}
        altProtein={protein_analysis.alt_fragment}
        refAA={protein_analysis.ref_aa}
        altAA={protein_analysis.alt_aa}
        position={protein_analysis.aa_position}
      />

      {/* ClinVar Info */}
      {clinvar && (
        <div className="bg-white rounded-lg shadow-sm p-4">
          <h4 className="text-sm font-medium text-gray-700 mb-3">ClinVar Evidence</h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-gray-500">Clinical Significance</p>
              <p className={`font-medium ${
                clinvar.significance?.includes('Pathogenic') ? 'text-red-600' :
                clinvar.significance?.includes('Benign') ? 'text-green-600' :
                'text-yellow-600'
              }`}>
                {clinvar.significance || 'Unknown'}
              </p>
            </div>
            <div>
              <p className="text-gray-500">Review Status</p>
              <p className="font-medium">{clinvar.review_status || 'No review'}</p>
            </div>
            {clinvar.conditions && clinvar.conditions.length > 0 && (
              <div className="sm:col-span-2">
                <p className="text-gray-500">Associated Conditions</p>
                <p className="font-medium">{clinvar.conditions.join(', ')}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Variant Details */}
      <div className="bg-gray-50 rounded-lg p-4 text-sm">
        <p className="text-gray-500 mb-1">Variant Details</p>
        <p className="font-mono text-gray-700">
          {variant.chromosome}:g.{variant.position}{variant.reference_allele}&gt;{variant.alternate_allele}
          {variant.gene && ` (${variant.gene})`}
        </p>
      </div>

      {/* Disclaimer */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-xs text-gray-500">
        <p className="flex items-start space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>
            <strong>Disclaimer:</strong> This analysis provides supportive evidence only and is not a standalone 
            diagnostic conclusion. Clinical correlation with patient phenotype is required. Results should be 
            reviewed by a qualified clinical geneticist or genetic counselor.
          </span>
        </p>
      </div>
    </div>
  );
};

export default ResultsDisplay;
