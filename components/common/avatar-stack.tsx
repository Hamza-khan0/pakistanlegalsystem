import { getInitials } from "@/lib/utils";

export function AvatarStack({ names }: { names: string[] }) {
  return (
    <div className="flex items-center">
      {names.map((name, index) => (
        <div
          key={name}
          className="-ml-2 first:ml-0 flex size-9 items-center justify-center rounded-full border border-line bg-panel-highlight text-[11px] font-semibold tracking-[0.16em] text-foreground"
          style={{ zIndex: names.length - index }}
          title={name}
        >
          {getInitials(name)}
        </div>
      ))}
    </div>
  );
}
