import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useConversation } from '../hooks/useConversation';
import { useCatalog } from '../hooks/useCatalog';
import { AppHeader } from '../components/AppHeader';
import { ChatColumn } from '../components/ChatColumn';
import { ResultsGrid } from '../components/ResultsGrid';
import { RequirementsDrawer } from '../components/RequirementsDrawer';
import { VehicleDetailModal } from '../components/VehicleDetailModal';
import type { Car } from '../types';

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
  const catalog = useCatalog();
  // Page-local, ephemeral UI state - not global (Zustand) state, since it
  // never needs to survive a restart or be shared outside this page.
  const [selectedCarId, setSelectedCarId] = useState<string | null>(null);

  // Browsing mode (the full catalog, paginated) until the AI has actually
  // searched at least once - then stay on its narrowed results even
  // through later follow-up-only turns. See conversationStore's
  // `hasNarrowed` for why this isn't just "cars.length > 0" (a real
  // zero-match search must not fall back to the catalog).
  const displayedCars = hasNarrowed ? narrowedCars : catalog.cars;
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
          <div className="mb-4.5">
            <div className="text-[19px] font-bold text-text">
              {hasNarrowed
                ? t('results.title', { count: displayedCars.length })
                : t('results.browsingTitle', { count: displayedCars.length })}
            </div>
            <div className="mt-0.5 text-[13px] text-subtext">
              {hasNarrowed ? t('results.updated') : t('results.startPrompt')}
            </div>
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
