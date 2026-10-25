import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';

const VariantInput = ({ onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    chromosome: 'chr17',
    position: '',
    reference_allele: '',
    alternate_allele: '',
    gene: 'BRCA1',
  });

  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.chromosome) newErrors.chromosome = 'Chromosome is required';
    if (!formData.position) newErrors.position = 'Position is required';
    if (isNaN(formData.position)) newErrors.position = 'Position must be a number';
    if (!formData.reference_allele) newErrors.reference_allele = 'Reference allele is required';
    if (!formData.gene) newErrors.gene = 'Gene is required';
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (validate()) {
      onSubmit({
        ...formData,
        position: parseInt(formData.position),
      });
    }
  };

  const presetVariants = [
    { name: 'BRCA1 C64G', chromosome: 'chr17', position: '43106478', ref: 'A', alt: 'C', gene: 'BRCA1' },
    { name: 'BRCA1 S1040T', chromosome: 'chr17', position: '43092412', ref: 'C', alt: 'G', gene: 'BRCA1' },
    { name: 'BRCA1 R1443G', chromosome: 'chr17', position: '43082434', ref: 'G', alt: 'C', gene: 'BRCA1' },
    { name: 'TP53 R248W', chromosome: 'chr17', position: '7674221', ref: 'G', alt: 'A', gene: 'TP53' },
    { name: 'TP53 L252P', chromosome: 'chr17', position: '7674208', ref: 'A', alt: 'G', gene: 'TP53' },
  ];

  const loadPreset = (preset) => {
    setFormData({
      chromosome: preset.chromosome,
      position: preset.position,
      reference_allele: preset.ref,
      alternate_allele: preset.alt,
      gene: preset.gene,
    });
    setErrors({});
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">Variant Input</h2>
      
      <div className="mb-4">
        <p className="text-xs text-gray-500 mb-2">Quick Load Presets:</p>
        <div className="flex flex-wrap gap-2">
          {presetVariants.map((preset, idx) => (
            <button
              key={idx}
              onClick={() => loadPreset(preset)}
              className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-full text-gray-700 transition-colors"
            >
              {preset.name}
            </button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Chromosome
            </label>
            <input
              type="text"
              name="chromosome"
              value={formData.chromosome}
              onChange={handleChange}
              className={`w-full px-3 py-2 border ${errors.chromosome ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition`}
              placeholder="e.g., chr17"
            />
            {errors.chromosome && (
              <p className="text-xs text-red-500 mt-1">{errors.chromosome}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Position (hg38)
            </label>
            <input
              type="number"
              name="position"
              value={formData.position}
              onChange={handleChange}
              className={`w-full px-3 py-2 border ${errors.position ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition`}
              placeholder="e.g., 43091971"
            />
            {errors.position && (
              <p className="text-xs text-red-500 mt-1">{errors.position}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Reference Allele
            </label>
            <input
              type="text"
              name="reference_allele"
              value={formData.reference_allele}
              onChange={handleChange}
              className={`w-full px-3 py-2 border ${errors.reference_allele ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition uppercase`}
              placeholder="e.g., AG"
            />
            {errors.reference_allele && (
              <p className="text-xs text-red-500 mt-1">{errors.reference_allele}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Alternate Allele
            </label>
            <input
              type="text"
              name="alternate_allele"
              value={formData.alternate_allele}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition uppercase"
              placeholder="e.g., G (or empty for deletion)"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Gene
            </label>
            <select
              name="gene"
              value={formData.gene}
              onChange={handleChange}
              className={`w-full px-3 py-2 border ${errors.gene ? 'border-red-500' : 'border-gray-300'} rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition`}
            >
              <option value="BRCA1">BRCA1</option>
              <option value="TP53">TP53</option>
              <option value="BRCA2">BRCA2</option>
            </select>
            {errors.gene && (
              <p className="text-xs text-red-500 mt-1">{errors.gene}</p>
            )}
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="mt-6 w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-medium py-3 px-4 rounded-lg hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
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
      </form>
    </div>
  );
};

export default VariantInput;
