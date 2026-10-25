import React, { useState, useEffect } from 'react';
import { Toaster, toast } from 'react-hot-toast';
import { 
  Sparkles, Dna, Activity, Shield, AlertCircle, 
  CheckCircle, Info, Search, Loader2, FileText,
  TrendingDown, TrendingUp, Minus, ExternalLink,
  Zap, BookOpen, Database, Award
} from 'lucide-react';
import { analyzeVariant, healthCheck } from './services/api';
import './styles/App.css';

function App() {
  const [formData, setFormData] = useState({
    chromosome: 'chr17',
    position: '43091994',
    reference_allele: 'G',
    alternate_allele: 'A',
    gene: 'BRCA1',
  });
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [backendStatus, setBackendStatus] = useState('checking');

  useEffect(() => {
    const checkBackend = async () => {
      try {
        const status = await healthCheck();
        if (status) {
          setBackendStatus('online');
          toast.success('✅ Connected to backend');
        } else {
          setBackendStatus('offline');
          toast.error('⚠️ Backend not responding');
        }
      } catch {
        setBackendStatus('offline');
        toast.error('⚠️ Backend server is not running');
      }
    };
    
    checkBackend();
    const interval = setInterval(checkBackend, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (results) setResults(null);
    if (error) setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.chromosome || !formData.position || !formData.reference_allele) {
      toast.error('Please fill in all required fields');
      return;
    }

    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const data = {
        chromosome: formData.chromosome,
        position: parseInt(formData.position),
        reference_allele: formData.reference_allele,
        alternate_allele: formData.alternate_allele || '',
        gene: formData.gene,
      };

      const result = await analyzeVariant(data);
      console.log('📥 Results from backend:', result);
      setResults(result);
      toast.success('✅ Analysis complete!');
      
    } catch (err) {
      setError(err.message);
      toast.error(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadPreset = (preset) => {
    setFormData({
      chromosome: preset.chromosome,
      position: preset.position,
      reference_allele: preset.ref,
      alternate_allele: preset.alt || '',
      gene: preset.gene,
    });
    setResults(null);
    setError(null);
  };

  const presets = [
    { name: 'BRCA1 C64G', chromosome: 'chr17', position: '43106478', ref: 'A', alt: 'C', gene: 'BRCA1' },
    { name: 'BRCA1 S1040T', chromosome: 'chr17', position: '43092412', ref: 'C', alt: 'G', gene: 'BRCA1' },
    { name: 'BRCA1 R1443G', chromosome: 'chr17', position: '43082434', ref: 'G', alt: 'C', gene: 'BRCA1' },
    { name: 'TP53 R248W', chromosome: 'chr17', position: '7674221', ref: 'G', alt: 'A', gene: 'TP53' },
    { name: 'TP53 L252P', chromosome: 'chr17', position: '7674208', ref: 'A', alt: 'G', gene: 'TP53' },
  ];

  const getClassificationColor = (classification) => {
    if (!classification) return 'text-gray-400 border-gray-500/20 bg-gray-500/10';
    if (classification.includes('Pathogenic')) return 'text-red-400 border-red-500/40 bg-red-500/10';
    if (classification.includes('Benign')) return 'text-green-400 border-green-500/40 bg-green-500/10';
    if (classification.includes('Uncertain')) return 'text-yellow-400 border-yellow-500/40 bg-yellow-500/10';
    return 'text-gray-400 border-gray-500/20 bg-gray-500/10';
  };

  const getClassificationIcon = (classification) => {
    if (!classification) return <Info className="w-5 h-5" />;
    if (classification.includes('Pathogenic')) return <AlertCircle className="w-5 h-5" />;
    if (classification.includes('Benign')) return <CheckCircle className="w-5 h-5" />;
    if (classification.includes('Uncertain')) return <Info className="w-5 h-5" />;
    return <Info className="w-5 h-5" />;
  };

  return (
    <div className="app-container">
      <div className="bg-animation">
        <div className="orb orb-1"></div>
        <div className="orb orb-2"></div>
        <div className="orb orb-3"></div>
      </div>

      <header className="header">
        <div className="container">
          <div className="header-content">
            <div className="header-left">
              <div className="logo-icon">
                <Dna className="w-8 h-8" />
              </div>
              <div>
                <h1>ClinX Clinical</h1>
                <p>Variant Effect Research System</p>
              </div>
            </div>
            <div className="header-right">
              <div className="badge">
                <span className={`status-dot ${backendStatus === 'online' ? 'online' : 'offline'}`} />
                <span>{backendStatus === 'online' ? 'Connected' : 'Offline'}</span>
              </div>
              <div className="badge">
                <Activity className="w-4 h-4" />
                <span>v4.0.0</span>
              </div>
              <div className="badge">
                <Shield className="w-4 h-4" />
                <span>Research use</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="main">
        <div className="container">
          <div className="main-grid">
            {/* Input Panel */}
            <div className="input-panel">
              <div className="panel">
                <div className="panel-header">
                  <h2><Sparkles className="w-5 h-5" /> Variant Input</h2>
                </div>
                <div className="panel-body">
                  <div className="presets">
                    <label>Quick Load Presets</label>
                    <div className="preset-buttons">
                      {presets.map((preset, idx) => (
                        <button
                          key={idx}
                          onClick={() => loadPreset(preset)}
                          className="preset-btn"
                          type="button"
                        >
                          {preset.name}
                        </button>
                      ))}
                    </div>
                  </div>

                  <form onSubmit={handleSubmit} className="form">
                    <div className="form-grid">
                      <div className="form-group">
                        <label>Chromosome</label>
                        <input
                          type="text"
                          name="chromosome"
                          value={formData.chromosome}
                          onChange={handleChange}
                          className="input"
                          placeholder="chr17"
                        />
                      </div>
                      <div className="form-group">
                        <label>Position (hg38)</label>
                        <input
                          type="number"
                          name="position"
                          value={formData.position}
                          onChange={handleChange}
                          className="input"
                          placeholder="43091971"
                        />
                      </div>
                      <div className="form-group">
                        <label>Reference Allele</label>
                        <input
                          type="text"
                          name="reference_allele"
                          value={formData.reference_allele}
                          onChange={handleChange}
                          className="input uppercase"
                          placeholder="AG"
                        />
                      </div>
                      <div className="form-group">
                        <label>Alternate Allele</label>
                        <input
                          type="text"
                          name="alternate_allele"
                          value={formData.alternate_allele}
                          onChange={handleChange}
                          className="input uppercase"
                          placeholder="G or empty"
                        />
                      </div>
                    </div>

                    <div className="form-group">
                      <label>Gene</label>
                      <select
                        name="gene"
                        value={formData.gene}
                        onChange={handleChange}
                        className="input"
                      >
                        <option value="BRCA1">BRCA1</option>
                        <option value="TP53">TP53</option>
                        <option value="BRCA2">BRCA2</option>
                      </select>
                    </div>

                    <button 
                      type="submit" 
                      className="analyze-btn" 
                      disabled={loading || backendStatus === 'offline'}
                    >
                      {loading ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                          <span>Analyzing...</span>
                        </>
                      ) : (
                        <>
                          <Search className="w-5 h-5" />
                          <span>Analyze Variant</span>
                        </>
                      )}
                    </button>

                    {backendStatus === 'offline' && (
                      <div className="error-message">
                        <AlertCircle className="w-4 h-4" />
                        <span>Backend server is not running</span>
                      </div>
                    )}

                    {error && (
                      <div className="error-message">
                        <AlertCircle className="w-4 h-4" />
                        <span>{error}</span>
                      </div>
                    )}
                  </form>
                </div>
              </div>
            </div>

            {/* Results Panel */}
            <div className="results-panel">
              {loading ? (
                <div className="loading-state">
                  <div className="loading-spinner">
                    <div className="spinner-ring"></div>
                    <div className="spinner-ring" style={{ animationDelay: '0.2s' }}></div>
                    <div className="spinner-ring" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                  <p className="loading-text">Analyzing variant with AI models...</p>
                  <p className="loading-subtext">This may take a few seconds</p>
                </div>
              ) : results ? (
                <div className="results-content">
                  {/* Classification Banner - FIXED VISIBILITY */}
                    <div className="classification-banner" style={{ borderColor: '#818cf8' }}>
                    <div className="banner-icon">
                        <Activity className="w-5 h-5" />
                    </div>
                    <div className="banner-content">
                        <h3 style={{ color: '#f1f5f9' }}>{results.experimental_impact?.predicted_impact || 'Experimental impact not scored'}</h3>
                        <p style={{ color: '#e2e8f0' }}>{results.experimental_impact?.summary || 'No experimental model assessment available.'}</p>
                        <p style={{ color: '#94a3b8', marginTop: 8 }}>{results.experimental_impact?.limitation}</p>
                        <div className="banner-meta">
                        <span className="banner-badge" style={{ color: '#94a3b8' }}>
                            Experimental Variant Impact Score · {results.experimental_impact?.method_version || 'unavailable'}
                        </span>
                        {results.disease_association && (
                            <span className="banner-badge" style={{ color: '#94a3b8' }}>
                            {results.disease_association}
                            </span>
                        )}
                        </div>
                    </div>
                    </div>

                  {/* Scores Grid */}
                  <div className="scores-grid">
                    <div className="score-card">
                      <div className="score-header">
                        <TrendingDown className="w-4 h-4 text-blue-400" />
                        <span>DNA Delta</span>
                      </div>
                      <div className="score-value" style={{ 
                        color: results.dna_score.delta_score < -0.5 ? '#ef4444' : 
                               results.dna_score.delta_score < 0 ? '#f59e0b' : '#22c55e'
                      }}>
                        {results.dna_score.delta_score.toFixed(3)}
                      </div>
                      <div className="score-interp">{results.dna_score.interpretation}</div>
                    </div>

                    <div className="score-card">
                      <div className="score-header">
                        <Dna className="w-4 h-4 text-purple-400" />
                        <span>Protein Impact</span>
                      </div>
                      <div className="score-value" style={{ 
                        color: results.protein_analysis.protein_score.impact === 'deleterious' ? '#ef4444' :
                               results.protein_analysis.protein_score.impact === 'probably_damaging' ? '#f59e0b' :
                               '#22c55e'
                      }}>
                        {results.protein_analysis.protein_score.impact || 'unknown'}
                      </div>
                      <div className="score-interp">
                        {results.protein_analysis.protein_score.status === 'scored'
                          ? `Δ${results.protein_analysis.protein_score.delta_score.toFixed(3)}`
                          : `Scoring: ${(results.protein_analysis.protein_score.status || 'not_scored').replaceAll('_', ' ')}`}
                      </div>
                    </div>

                    <div className="score-card">
                      <div className="score-header">
                        <Award className="w-4 h-4 text-yellow-400" />
                        <span>Experimental impact score</span>
                      </div>
                      <div className="score-value" style={{ color: '#e2e8f0', fontSize: 20 }}>
                        {results.experimental_impact?.impact_score != null
                          ? results.experimental_impact.impact_score.toFixed(3) : 'Not scored'}
                      </div>
                      <div className="score-interp">Illustrative weighted score; not a probability</div>
                      <div className="score-interp" style={{ color: '#e2e8f0', fontWeight: 600, marginTop: 8 }}>
                        {results.experimental_impact?.predicted_impact ||
                          (results.experimental_impact?.status === 'unsupported' ? 'Unsupported variant type' : 'Not scored')}
                      </div>
                    </div>
                  </div>

                  {/* Protein Analysis Panel - FIXED COLORS */}
                  <div className="panel">
                    <div className="panel-header">
                      <h3 className="text-white"><Dna className="w-4 h-4" /> Protein Analysis</h3>
                    </div>
                    <div className="panel-body">
                      <div className="protein-grid">
                        {/* Left side - Info */}
                        <div className="protein-info">
                          <div className="info-row">
                            <span className="info-label text-gray-400">Mutation Type</span>
                            <span className="info-value text-white font-semibold">
                              {results.protein_analysis.mutation_type?.toUpperCase() || 'N/A'}
                            </span>
                          </div>
                          <div className="info-row">
                            <span className="info-label text-gray-400">AA Change</span>
                            <span className="info-value text-white">
                              {results.protein_analysis.ref_aa} → {results.protein_analysis.alt_aa}
                              <span className="text-gray-400 text-sm ml-1">
                                at position {results.protein_analysis.aa_position}
                              </span>
                            </span>
                          </div>
                          <div className="info-row">
                            <span className="info-label text-gray-400">Protein Impact</span>
                            <span className={`info-value font-semibold ${
                              results.protein_analysis.protein_score.impact === 'deleterious' ? 'text-red-400' :
                              results.protein_analysis.protein_score.impact === 'probably_damaging' ? 'text-orange-400' :
                              'text-green-400'
                            }`}>
                              {results.protein_analysis.protein_score.impact || 'unknown'}
                              <span className="text-gray-400 text-sm ml-1">
                                {results.protein_analysis.protein_score.status === 'scored'
                                  ? `(Δ${results.protein_analysis.protein_score.delta_score.toFixed(3)})`
                                  : '(No model score)'}
                              </span>
                            </span>
                          </div>
                          <div className="info-row">
                            <span className="info-label text-gray-400">Transcript</span>
                            <span className="info-value text-white font-mono text-sm">
                              {results.transcript.transcript_id}
                            </span>
                          </div>
                          <div className="info-row">
                            <span className="info-label text-gray-400">CDS Position</span>
                            <span className="info-value text-white">
                              {results.transcript.cds_position}
                            </span>
                          </div>
                        </div>

                        {/* Right side - Sequences */}
                        <div className="protein-sequences">
                          <div className="seq-block">
                            <div className="seq-label text-gray-400 text-xs">Reference</div>
                            <div className="seq-content text-gray-300 font-mono text-sm break-all">
                              {results.protein_analysis.ref_fragment || 'N/A'}
                            </div>
                          </div>
                          <div className="seq-block border border-yellow-500/20">
                            <div className="seq-label text-yellow-400 text-xs">Altered</div>
                            <div className="seq-content text-yellow-300 font-mono text-sm break-all">
                              {results.protein_analysis.alt_fragment || 'N/A'}
                            </div>
                          </div>
                          <div className="mt-1 text-xs text-gray-500">
                            <span className="text-yellow-400">[ ]</span> indicates mutated position
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {results.experimental_impact && <div className="panel">
                    <div className="panel-header"><h3>Experimental impact evidence</h3></div>
                    <div className="panel-body">
                      {Object.entries(results.experimental_impact.evidence || {}).map(([key, details]) =>
                        <p key={key} style={{ marginBottom: 8 }}><strong>{key.replaceAll('_', ' ')}</strong>: {details.join('; ')}</p>)}
                      <p>{results.experimental_impact.limitation}</p>
                    </div>
                  </div>}
                  {/* ClinVar */}
                  {results.clinvar && (
                    <div className="panel">
                      <div className="panel-header">
                        <h3 className="text-white"><Database className="w-4 h-4" /> ClinVar Evidence</h3>
                      </div>
                      <div className="panel-body">
                        <p>External ClinVar germline classification, separate from experimental model predictions.</p>
                        <p>Lookup: {results.clinvar.lookup_status?.replaceAll('_', ' ')}{results.clinvar.exact_match ? ' (exact hg38 allele match)' : ''}</p>
                        {results.clinvar.source_url && <p><a href={results.clinvar.source_url} target="_blank" rel="noreferrer">ClinVar variation {results.clinvar.variation_id}</a></p>}
                        {results.clinvar.note && <p>{results.clinvar.note}</p>}
                        {results.clinvar.last_evaluated && <p>Last evaluated: {results.clinvar.last_evaluated}</p>}
                        <div className="clinvar-grid">
                          <div className="info-row">
                            <span className="info-label text-gray-400">Clinical Significance</span>
                            <span className={`info-value ${
                              results.clinvar.significance?.includes('Pathogenic') ? 'text-red-400' :
                              results.clinvar.significance?.includes('Benign') ? 'text-green-400' :
                              'text-yellow-400'
                            }`}>
                              {results.clinvar.significance || 'Not reported'}
                            </span>
                          </div>
                          <div className="info-row">
                            <span className="info-label text-gray-400">Review Status</span>
                            <span className="info-value text-white">
                              {results.clinvar.review_status || 'No review'}
                            </span>
                          </div>
                          {results.clinvar.conditions && results.clinvar.conditions.length > 0 && (
                            <div className="info-row full-width">
                              <span className="info-label text-gray-400">Associated Conditions</span>
                              <span className="info-value text-white">
                                {results.clinvar.conditions.join(', ')}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Disclaimer */}
                  <div className="disclaimer">
                    <AlertCircle className="w-4 h-4 flex-shrink-0 text-gray-500" />
                    <div className="text-gray-400 text-sm">
                      <strong>Disclaimer:</strong> This analysis provides supportive evidence only and is not a 
                      standalone diagnostic conclusion. Clinical correlation with patient phenotype is required. 
                      Results should be reviewed by a qualified clinical geneticist or genetic counselor.
                    </div>
                  </div>
                </div>
              ) : (
                <div className="empty-state">
                  <div className="empty-icon">
                    <Dna className="w-16 h-16" />
                  </div>
                  <h3 className="text-white text-xl font-semibold">Ready for Analysis</h3>
                  <p className="text-gray-400">Enter a variant in the input panel to analyze its clinical significance</p>
                  <div className="empty-tags">
                    <span className="text-gray-400">BRCA1</span>
                    <span className="text-gray-400">TP53</span>
                    <span className="text-gray-400">Predicted impact</span>
                    <span className="text-gray-400">ClinVar</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#1e293b',
            color: '#f1f5f9',
            border: '1px solid #334155',
          },
          success: {
            iconTheme: { primary: '#22c55e', secondary: '#1e293b' },
          },
          error: {
            iconTheme: { primary: '#ef4444', secondary: '#1e293b' },
          },
        }}
      />
    </div>
  );
}

export default App;
