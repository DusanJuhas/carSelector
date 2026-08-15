import { useTranslation } from 'react-i18next';
import { useConversation } from '../hooks/useConversation';
import { AppHeader } from '../components/AppHeader';
import { ChatColumn } from '../components/ChatColumn';
import { ResultsGrid } from '../components/ResultsGrid';
import { RequirementsDrawer } from '../components/RequirementsDrawer';

export function ChatPage() {
  const { t } = useTranslation();
  const {
    messages,
    nextSuggestion,
    requirements,
    cars,
    stageName,
    advance,
    restart,
    drawerOpen,
    toggleDrawer,
    closeDrawer,
  } = useConversation();

  const hasResults = cars.length > 0;

  return (
    <div className="relative flex h-screen w-full flex-col overflow-hidden bg-bg text-text">
      <AppHeader
        requirementsCount={requirements.length}
        onRestart={restart}
        onToggleDrawer={toggleDrawer}
      />
      <div className="relative flex min-h-0 flex-1">
        <ChatColumn
          messages={messages}
          nextSuggestion={nextSuggestion}
          onSelectSuggestion={advance}
        />
        <div className="min-w-0 flex-1 overflow-y-auto px-7 py-6">
          <div className="mb-4.5">
            <div className="text-[19px] font-bold text-text">
              {hasResults ? t('results.title', { count: cars.length }) : t('results.titleEmpty')}
            </div>
            <div className="mt-0.5 text-[13px] text-subtext">
              {hasResults
                ? t('results.updatedAfter', { stage: stageName })
                : t('results.startPrompt')}
            </div>
          </div>
          <ResultsGrid cars={cars} />
        </div>
        <RequirementsDrawer requirements={requirements} open={drawerOpen} onClose={closeDrawer} />
      </div>
    </div>
  );
}
