import type { UserRequirement } from '../types';

export interface RequirementsDrawerProps {
  requirements: UserRequirement[];
  open: boolean;
  onClose: () => void;
}

export function RequirementsDrawer({ requirements, open, onClose }: RequirementsDrawerProps) {
  return (
    <>
      <div
        onClick={onClose}
        className={`absolute inset-0 z-10 transition-colors ${
          open ? 'pointer-events-auto bg-black/25' : 'pointer-events-none bg-transparent'
        }`}
      />
      <div
        className={`absolute inset-y-0 right-0 z-20 w-[360px] overflow-y-auto border-l border-border bg-panel p-[22px] shadow-card transition-transform duration-300 ease-out ${
          open ? 'translate-x-0' : 'translate-x-full'
        }`}
      >
        <div className="text-[16px] font-bold text-text">Technical requirements</div>
        <div className="mb-2 text-[12.5px] text-subtext">
          Plain-language input, translated to specs.
        </div>
        {requirements.length === 0 ? (
          <div className="px-1 py-10 text-center text-[13px] text-subtext">
            No requirements captured yet.
          </div>
        ) : (
          requirements.map((req) => (
            <div
              key={req.label}
              className={`border-b border-border px-1 py-3 ${req.changed ? 'animate-flash' : ''}`}
            >
              <div className="text-[11px] font-bold uppercase tracking-wide text-subtext">
                {req.label}
              </div>
              <div className="mt-0.5 text-[14px] font-semibold text-text">{req.value}</div>
              <div className="mt-1 text-[12px] italic text-subtext">{req.source}</div>
            </div>
          ))
        )}
      </div>
    </>
  );
}
