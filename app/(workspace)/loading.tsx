export default function WorkspaceLoading() {
  return (
    <div className="space-y-6">
      <div className="h-24 animate-pulse rounded-[30px] border border-line bg-white/[0.03]" />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div
            key={index}
            className="h-36 animate-pulse rounded-[28px] border border-line bg-white/[0.03]"
          />
        ))}
      </div>
      <div className="h-[420px] animate-pulse rounded-[30px] border border-line bg-white/[0.03]" />
    </div>
  );
}
