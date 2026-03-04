import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { BarChart2, Trophy, ArrowRight } from 'lucide-react'
import { contractsApi, priceApi } from '../api'
import { CompareResult } from '../types'
import toast from 'react-hot-toast'
import Spinner from '../components/ui/Spinner'

export default function ComparePage() {
  const [primary, setPrimary] = useState<number | null>(null)
  const [compared, setCompared] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<CompareResult | null>(null)

  const { data } = useQuery({ queryKey: ['contracts'], queryFn: contractsApi.list })
  const extractedContracts = (data?.contracts ?? []).filter((c) => c.doc_status === 'extracted')

  const compare = async () => {
    if (!primary || !compared) return
    if (primary === compared) { toast.error('Select two different contracts'); return }
    setLoading(true)
    try {
      const res = await priceApi.compare(primary, compared)
      setResult(res)
    } catch {
      toast.error('Comparison failed — ensure both contracts are fully extracted')
    } finally {
      setLoading(false)
    }
  }

  const fmt = (v?: number | null) => v != null ? `$${v.toLocaleString()}` : '—'

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-900 mb-2">Compare Deals</h1>
      <p className="text-slate-500 mb-8">Side-by-side AI comparison of two contracts to find the better deal.</p>

      {extractedContracts.length < 2 ? (
        <div className="card p-10 text-center">
          <BarChart2 size={48} className="mx-auto mb-3 text-slate-200" />
          <p className="font-semibold text-slate-600">You need at least 2 analyzed contracts to compare</p>
          <p className="text-sm text-slate-400 mt-1">Upload and wait for extraction to complete on both contracts.</p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Primary Contract</label>
              <select className="input" value={primary ?? ''} onChange={(e) => setPrimary(Number(e.target.value))}>
                <option value="">Select contract...</option>
                {extractedContracts.map((c) => (
                  <option key={c.id} value={c.id}>{c.dealer_offer_name || `Contract #${c.id}`}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Compared Contract</label>
              <select className="input" value={compared ?? ''} onChange={(e) => setCompared(Number(e.target.value))}>
                <option value="">Select contract...</option>
                {extractedContracts.filter((c) => c.id !== primary).map((c) => (
                  <option key={c.id} value={c.id}>{c.dealer_offer_name || `Contract #${c.id}`}</option>
                ))}
              </select>
            </div>
          </div>

          <button onClick={compare} disabled={!primary || !compared || loading} className="btn-primary mb-8">
            {loading ? <><Spinner className="text-white" /> Comparing...</> : <><BarChart2 size={16} /> Compare Deals</>}
          </button>

          {result && (
            <div className="space-y-6">
              {/* Winner banner */}
              <div className={`card p-6 text-center border-2 ${result.winner === 'deal1' ? 'border-green-400 bg-green-50' : result.winner === 'deal2' ? 'border-blue-400 bg-blue-50' : 'border-yellow-300 bg-yellow-50'}`}>
                <Trophy size={28} className="mx-auto mb-2 text-yellow-500" />
                <h2 className="text-xl font-bold text-slate-900">
                  {result.winner === 'tie' ? "It's a Tie!" : result.winner === 'deal1' ? '🏆 Primary Contract Wins' : '🏆 Compared Contract Wins'}
                </h2>
              </div>

              {/* Side-by-side */}
              <div className="grid grid-cols-3 gap-4">
                <div className="card p-5">
                  <h3 className="font-semibold text-slate-700 mb-3 text-center">Primary</h3>
                  {[
                    ['Monthly', fmt(result.primary.monthly_payment)],
                    ['APR', result.primary.apr_percent ? `${result.primary.apr_percent}%` : '—'],
                    ['Term', result.primary.term_months ? `${result.primary.term_months}mo` : '—'],
                    ['Down', fmt(result.primary.down_payment)],
                    ['Mileage', result.primary.mileage_allowance_yr ? `${result.primary.mileage_allowance_yr.toLocaleString()}/yr` : '—'],
                  ].map(([label, value]) => (
                    <div key={label} className="flex justify-between py-2 border-b border-slate-100 text-sm">
                      <span className="text-slate-500">{label}</span>
                      <span className="font-medium">{value}</span>
                    </div>
                  ))}
                </div>

                <div className="flex items-center justify-center">
                  <ArrowRight size={32} className="text-slate-300" />
                </div>

                <div className="card p-5">
                  <h3 className="font-semibold text-slate-700 mb-3 text-center">Compared</h3>
                  {[
                    ['Monthly', fmt(result.compared.monthly_payment)],
                    ['APR', result.compared.apr_percent ? `${result.compared.apr_percent}%` : '—'],
                    ['Term', result.compared.term_months ? `${result.compared.term_months}mo` : '—'],
                    ['Down', fmt(result.compared.down_payment)],
                    ['Mileage', result.compared.mileage_allowance_yr ? `${result.compared.mileage_allowance_yr.toLocaleString()}/yr` : '—'],
                  ].map(([label, value]) => (
                    <div key={label} className="flex justify-between py-2 border-b border-slate-100 text-sm">
                      <span className="text-slate-500">{label}</span>
                      <span className="font-medium">{value}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Analysis */}
              <div className="card p-6">
                <h3 className="font-semibold text-slate-900 mb-3">AI Analysis</h3>
                <p className="text-sm text-slate-700 leading-relaxed">{result.analysis}</p>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}