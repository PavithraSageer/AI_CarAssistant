import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { FileText, Trash2, Plus, RefreshCw } from 'lucide-react'
import { contractsApi } from '../api'
import FairnessScore from '../components/ui/FairnessScore'
import Spinner from '../components/ui/Spinner'
import toast from 'react-hot-toast'

export default function ContractsPage() {
  const qc = useQueryClient()
  const { data, isLoading, refetch } = useQuery({ queryKey: ['contracts'], queryFn: contractsApi.list })
  const deleteMutation = useMutation({
    mutationFn: contractsApi.delete,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['contracts'] }); toast.success('Deleted') },
  })

  const contracts = data?.contracts ?? []

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Contracts</h1>
          <p className="text-slate-500 text-sm mt-0.5">{contracts.length} contract{contracts.length !== 1 ? 's' : ''}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => refetch()} className="btn-secondary">
            <RefreshCw size={16} />
            Refresh
          </button>
          <Link to="/contracts/upload" className="btn-primary">
            <Plus size={16} />
            Upload Contract
          </Link>
        </div>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-20"><Spinner /></div>
      ) : contracts.length === 0 ? (
        <div className="card text-center py-20">
          <FileText size={48} className="mx-auto mb-4 text-slate-300" />
          <h3 className="font-semibold text-slate-700 mb-1">No contracts yet</h3>
          <p className="text-slate-400 text-sm mb-4">Upload your first lease or loan contract to get started</p>
          <Link to="/contracts/upload" className="btn-primary mx-auto">
            <Plus size={16} /> Upload Contract
          </Link>
        </div>
      ) : (
        <div className="card divide-y divide-slate-100">
          {contracts.map((c) => (
            <div key={c.id} className="flex items-center justify-between px-5 py-4 hover:bg-slate-50 transition-colors">
              <Link to={`/contracts/${c.id}`} className="flex items-center gap-4 flex-1 min-w-0">
                <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
                  <FileText size={18} className="text-slate-500" />
                </div>
                <div className="min-w-0">
                  <p className="font-medium text-slate-900 truncate">{c.dealer_offer_name || `Contract #${c.id}`}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-slate-400">
                      {c.contract_type?.toUpperCase() ?? 'UNKNOWN'} • {new Date(c.created_at).toLocaleDateString()}
                    </span>
                    <span className={`badge-${c.doc_status === 'extracted' ? 'green' : c.doc_status === 'failed' ? 'red' : 'yellow'}`}>
                      {c.doc_status}
                    </span>
                    {c.red_flag_level === 'high' && <span className="badge-red">⚠ Red Flags</span>}
                  </div>
                </div>
              </Link>
              <div className="flex items-center gap-4 ml-4">
                {c.fairness_score !== undefined && c.fairness_score !== null && (
                  <FairnessScore score={c.fairness_score} size="sm" />
                )}
                <button
                  onClick={() => { if (confirm('Delete this contract?')) deleteMutation.mutate(c.id) }}
                  className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}