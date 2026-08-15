import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useConversation } from '../hooks/useConversation';
import { useCatalog } from '../hooks/useCatalog';
import { useCustomOrder } from '../hooks/useCustomOrder';
import { AppHeader } from '../components/AppHeader';
import { ChatColumn } from '../components/ChatColumn';
import { ResultsGrid } from '../components/ResultsGrid';
import { RequirementsDrawer } from '../components/RequirementsDrawer';
import { VehicleDetailModal } from '../components/VehicleDetailModal';
import { SortControl } from '../components/SortControl';
import { sortCars } from '../utils/sortCars';
import type { BackendSortOption, Car, SortOption } from '../types';

const BACKEND_SORTS: SortOption[] = ['price_asc', 'price_desc', 'alpha'];

export function ChatPage() {
  const { t } = useTranslation();
  const {
    messages,
    requirements,
    cars: narrowedCars,
    hasNarrowed,
    isSending,
    error,
    send,
    restart,
    drawerOpen,
    toggleDrawer,
    closeDrawer,
  } = useConversation();
  // Page-local, ephemeral UI state - not global (Zustand) state, since it
  // never needs to survive a restart or be shared outside this page.
  const [selectedCarId, setSelectedCarId] = useState<string | null>(null);
  const [sortOption, setSortOption] = useState<SortOption>('recommended');
  const { customOrder, setCustomOrder } = useCustomOrder();

  // Price/alpha sorts only go to the backend in browsing mode, where
  // results are paginated - sorting only the page(s) loaded so far would
  // be wrong (see hooks/useCatalog.ts). In narrowed mode the whole
  // shortlist is already loaded, so it sorts client-side instead, below.
  const backendSort =
    !hasNarrowed && BACKEND_SORTS.includes(sortOption) ? (sortOption as BackendSortOption) : undefined;
  const catalog = useCatalog(backendSort);

  // Browsing mode (the full catalog, paginated) until the AI has actually
  // searched at least once - then stay on its narrowed results even
  // through later follow-up-only turns. See conversationStore's
  // `hasNarrowed` for why this isn't just "cars.length > 0" (a real
  // zero-match search must not fall back to the catalog).
  const baseCars = hasNarrowed ? narrowedCars : catalog.cars;
  // In browsing mode, price/alpha are already applied server-side above -
  // re-applying them client-side here would be redundant (though harmless,
  // since it'd just reproduce the same order); 'recommended' keeps that
  // case a pure passthrough. Narrowed mode and 'custom' always sort here.
  const clientSort: SortOption = sortOption === 'custom' ? 'custom' : hasNarrowed ? sortOption : 'recommended';
  const displayedCars = sortCars(baseCars, clientSort, customOrder);
  const hasResults = displayedCars.length > 0;
  const showCatalogError = !hasNarrowed && catalog.error && !hasResults;
  const showCatalogLoading = !hasNarrowed && catalog.isLoading;

  return (
    <div className="relative flex h-screen w-full flex-col overflow-hidden bg-bg text-text">
      <AppHeader
        requirementsCount={requirements.length}
        onRestart={restart}
        onToggleDrawer={toggleDrawer}
      />
      <div className="relative flex min-h-0 flex-1">
        <ChatColumn messages={messages} isSending={isSending} onSend={send} />
        <div className="min-w-0 flex-1 overflow-y-auto px-7 py-6">
          <div className="mb-4.5 flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="text-[19px] font-bold text-text">
                {hasNarrowed
                  ? t('results.title', { count: displayedCars.length })
                  : t('results.browsingTitle', { count: displayedCars.length })}
              </div>
              <div className="mt-0.5 text-[13px] text-subtext">
                {hasNarrowed ? t('results.updated') : t('results.startPrompt')}
              </div>
            </div>
            <SortControl value={sortOption} onChange={setSortOption} />
          </div>
          {error && (
            <div className="mb-4 rounded-control bg-flag-bg px-3.5 py-2.5 text-[13px] text-flag">
              {error === 'ai_not_configured' ? t('chat.aiNotConfigured') : t('chat.genericError')}
            </div>
          )}
          {showCatalogLoading ? (
            <div className="px-5 py-10 text-center text-[13px] text-subtext">
              {t('results.loadingCatalog')}
            </div>
          ) : showCatalogError ? (
            <div className="px-5 py-10 text-center text-[13px] text-subtext">
              {t('results.catalogError')}
            </div>
          ) : (
            <>
              <ResultsGrid
                cars={displayedCars}
                onSelectCar={(car: Car) => setSelectedCarId(car.id)}
                reorderable={sortOption === 'custom'}
                onReorder={setCustomOrder}
              />
              {!hasNarrowed && catalog.hasMore && (
                <div className="mt-4 flex justify-center">
                  <button
                    type="button"
                    onClick={catalog.loadMore}
                    disabled={catalog.isLoadingMore}
                    className="rounded-control border border-border bg-panel-2 px-4 py-2 text-[13px] font-semibold text-text disabled:opacity-50"
                  >
                    {catalog.isLoadingMore ? t('results.loadingMore') : t('results.loadMore')}
                  </button>
                </div>
              )}
            </>
          )}
        </div>
        <RequirementsDrawer requirements={requirements} open={drawerOpen} onClose={closeDrawer} />
      </div>
      {selectedCarId !== null && (
        <VehicleDetailModal
          configurationId={selectedCarId}
          onClose={() => setSelectedCarId(null)}
        />
      )}
    </div>
  );
}
