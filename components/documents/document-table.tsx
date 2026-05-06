import type { CaseDocument } from "@/types";
import { StatusBadge } from "@/components/common/status-badge";
import { formatCompactDate } from "@/lib/utils";

interface DocumentTableProps {
  documents: CaseDocument[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function DocumentTable({
  documents,
  selectedId,
  onSelect,
}: DocumentTableProps) {
  return (
    <div className="overflow-hidden rounded-[28px] border border-line bg-panel">
      <table className="min-w-full divide-y divide-line">
        <thead className="bg-white/[0.02]">
          <tr className="text-left text-xs font-semibold uppercase tracking-[0.22em] text-subtle">
            <th className="px-5 py-4">Document</th>
            <th className="px-5 py-4">Type</th>
            <th className="px-5 py-4">Uploaded</th>
            <th className="px-5 py-4">Status</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {documents.map((document) => {
            const active = document.id === selectedId;

            return (
              <tr
                key={document.id}
                className={active ? "bg-white/[0.05]" : "hover:bg-white/[0.03]"}
              >
                <td className="px-5 py-4">
                  <button
                    className="space-y-2 text-left"
                    onClick={() => onSelect(document.id)}
                    type="button"
                  >
                    <p className="font-medium text-foreground">{document.name}</p>
                    <p className="max-w-lg text-sm text-muted-foreground">
                      {document.summary}
                    </p>
                  </button>
                </td>
                <td className="px-5 py-4 text-sm text-muted-foreground">
                  {document.type}
                </td>
                <td className="px-5 py-4 text-sm text-muted-foreground">
                  {formatCompactDate(document.uploadDate)}
                </td>
                <td className="px-5 py-4">
                  <div className="flex flex-wrap gap-2">
                    <StatusBadge status={document.status} />
                    <StatusBadge status={document.extractionStatus} />
                    <StatusBadge status={document.intelligenceStatus} />
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
