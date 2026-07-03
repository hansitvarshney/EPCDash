import { CheckCircle2, AlertTriangle, AlertOctagon } from 'lucide-react';
import { HealthStatus } from '../../lib/api';

const CONFIG: Record<HealthStatus, { label: string; classes: string; Icon: typeof CheckCircle2 }> = {
  ON_TRACK: {
    label: 'On Track',
    classes: 'bg-emerald-950/40 border-emerald-800/60 text-emerald-400',
    Icon: CheckCircle2,
  },
  AT_RISK: {
    label: 'At Risk',
    classes: 'bg-amber-950/40 border-amber-800/60 text-amber-400',
    Icon: AlertTriangle,
  },
  ACTION_REQUIRED: {
    label: 'Action Required',
    classes: 'bg-red-950/40 border-red-800/60 text-red-400',
    Icon: AlertOctagon,
  },
};

export default function HealthBadge({ status }: { status: HealthStatus }) {
  const config = CONFIG[status] ?? CONFIG.ON_TRACK;
  const { Icon } = config;
  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[10px] font-bold uppercase tracking-wider ${config.classes}`}>
      <Icon size={12} strokeWidth={2.5} />
      {config.label}
    </div>
  );
}
