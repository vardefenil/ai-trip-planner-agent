'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { PackageCard } from '@/components/PackageCard';
import { BookingSummaryView } from '@/components/BookingSummaryView';
import { PipelineProgress } from '@/components/PipelineProgress';
import { sendChat, streamTripPlan } from '@/lib/api';
import type {
  ChatMessage,
  TripPackage,
  BookingSummary,
  PipelineStage,
  ParsedTrip,
  BudgetAllocation,
  SSEEvent,
} from '@/types/travel';

const INITIAL_STAGES: PipelineStage[] = [
  { id: 'parsing', label: 'Parsing Request', icon: '🔍', status: 'idle' },
  { id: 'searching', label: 'Searching Options', icon: '🌐', status: 'idle' },
  { id: 'ranking', label: 'Building Itinerary', icon: '🎯', status: 'idle' },
  { id: 'presenting', label: 'Preparing Packages', icon: '📦', status: 'idle' },
  { id: 'booking', label: 'Booking Summary', icon: '🎉', status: 'idle' },
];

const SUGGESTION_PROMPTS = [
  '🏖️ Plan a 5-day Goa trip for 2, budget ₹35,000',
  '🏔️ 7-day Manali adventure for 1 person, ₹25,000',
  '🌴 Kerala backwaters trip, 6 days, ₹40,000 for couple',
  '🏰 Rajasthan heritage tour, 8 days, ₹60,000',
  '🏝️ Andaman Islands 5 days for 2, ₹55,000',
  '🌄 Ladakh trip, 10 days, ₹80,000 for 2',
];

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: `Namaste! 🙏 I am **Yatra AI**, your personal Indian travel planning assistant.\n\nTell me where you would like to go, your budget, and how many days — and I will build you **5 custom trip packages** with hotels, transport, and day-by-day itineraries.\n\nYou can also ask me anything about travel in India! 🌏`,
      timestamp: new Date(),
      type: 'text',
    },
  ]);

  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [stages, setStages] = useState<PipelineStage[]>(INITIAL_STAGES);
  const [isPlanningMode, setIsPlanningMode] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const stopStreamRef = useRef<(() => void) | null>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const addMessage = useCallback((msg: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    setMessages((prev) => [
      ...prev,
      { ...msg, id: uuidv4(), timestamp: new Date() },
    ]);
  }, []);

  const updateStage = useCallback((stageId: string, status: PipelineStage['status'], message?: string) => {
    setStages((prev) =>
      prev.map((s) => (s.id === stageId ? { ...s, status, message } : s))
    );
  }, []);

  const resetStages = useCallback(() => {
    setStages(INITIAL_STAGES.map((s) => ({ ...s, status: 'idle' })));
  }, []);

  const handleSSEEvent = useCallback((event: SSEEvent) => {
    const { type, stage, message, data } = event;

    if (type === 'start') {
      setIsPlanningMode(true);
      addMessage({
        role: 'assistant',
        content: 'Starting your trip planning pipeline...',
        type: 'text',
      });
    }

    if (type === 'stage_start' && stage) {
      updateStage(stage, 'running', message);
    }

    if (type === 'stage_done' && stage) {
      updateStage(stage, 'done');

      if (stage === 'parsing' && data) {
        const parsedTrip = (data as { parsed_trip?: ParsedTrip; budget_allocation?: BudgetAllocation }).parsed_trip;
        const budgetAlloc = (data as { parsed_trip?: ParsedTrip; budget_allocation?: BudgetAllocation }).budget_allocation;
        if (parsedTrip && budgetAlloc) {
          addMessage({
            role: 'assistant',
            content: `Got it! Planning your trip to **${parsedTrip.destination}**\n\nBudget Breakdown:\n- Stay: Rs.${budgetAlloc.stay.toLocaleString('en-IN')}\n- Transport: Rs.${budgetAlloc.transport.toLocaleString('en-IN')}\n- Food: Rs.${budgetAlloc.food.toLocaleString('en-IN')}\n- Rentals: Rs.${budgetAlloc.local_rental.toLocaleString('en-IN')}`,
            type: 'text',
          });
        }
      }

      if (stage === 'searching' && data) {
        const d = data as { stays_count?: number; transports_count?: number; rentals_count?: number };
        addMessage({
          role: 'assistant',
          content: `Search complete! Found ${d.stays_count || 0} stays, ${d.transports_count || 0} transport options, ${d.rentals_count || 0} rentals.`,
          type: 'text',
        });
      }
    }

    if (type === 'complete' && event.full_state) {
      const fullState = event.full_state as Record<string, unknown>;

      const packages = (fullState.presented_packages || fullState.ranked_packages) as TripPackage[] || [];
      const bookingSummary = fullState.booking_summary as BookingSummary | null;

      if (packages.length > 0) {
        addMessage({
          role: 'assistant',
          content: `Here are your ${packages.length} personalised trip packages! Click any package to expand, or tap View Booking Details for links.`,
          type: 'packages',
          packages,
          bookingSummary: bookingSummary || undefined,
        });
      }

      setIsPlanningMode(false);
      setIsLoading(false);
      if (event.session_id) setSessionId(event.session_id);
    }

    if (type === 'error') {
      addMessage({
        role: 'assistant',
        content: `Something went wrong: ${message || 'Unknown error'}. Please try again.`,
        type: 'text',
      });
      setIsPlanningMode(false);
      setIsLoading(false);
      resetStages();
    }
  }, [addMessage, updateStage, resetStages]);

  const handleSend = useCallback(async () => {
    const query = input.trim();
    if (!query || isLoading) return;

    setInput('');
    setIsLoading(true);

    addMessage({ role: 'user', content: query, type: 'text' });

    const history = messages
      .filter((m) => m.type === 'text')
      .map((m) => ({ role: m.role === 'user' ? 'user' : 'model', content: m.content }));

    try {
      const chatResponse = await sendChat(query, sessionId, history);
      if (chatResponse.session_id) setSessionId(chatResponse.session_id);

      if (chatResponse.is_trip_request) {
        addMessage({
          role: 'assistant',
          content: chatResponse.response,
          type: 'text',
        });

        const planQuery = chatResponse.suggested_query || query;
        resetStages();

        stopStreamRef.current = streamTripPlan(
          planQuery,
          chatResponse.session_id,
          (e) => handleSSEEvent(e as unknown as SSEEvent),
          (err) => {
            addMessage({ role: 'assistant', content: `Error: ${err}`, type: 'text' });
            setIsLoading(false);
            setIsPlanningMode(false);
          },
          () => setIsLoading(false)
        );
      } else {
        addMessage({
          role: 'assistant',
          content: chatResponse.response,
          type: 'text',
        });
        setIsLoading(false);
      }
    } catch {
      addMessage({
        role: 'assistant',
        content: 'Could not connect to the server. Make sure the backend is running on port 8000.',
        type: 'text',
      });
      setIsLoading(false);
    }
  }, [input, isLoading, messages, sessionId, addMessage, resetStages, handleSSEEvent]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestion = (suggestion: string) => {
    setInput(suggestion);
    inputRef.current?.focus();
  };

  const handleBookPackage = useCallback((pkg: TripPackage) => {
    const packagesMsg = messages.find((m) => m.type === 'packages');
    if (packagesMsg?.bookingSummary) {
      addMessage({
        role: 'assistant',
        content: '',
        type: 'booking',
        bookingSummary: { ...packagesMsg.bookingSummary, selected_package: pkg },
      });
    }
  }, [messages, addMessage]);

  return (
    <div className="chat-root">
      <aside className="sidebar">
        <div className="sidebar-logo">
          <span className="logo-emoji">🌏</span>
          <div>
            <div className="logo-title">Yatra AI</div>
            <div className="logo-sub">India Travel Planner</div>
          </div>
        </div>
        <div className="sidebar-divider" />

        {(isPlanningMode || stages.some((s) => s.status !== 'idle')) && (
          <div className="sidebar-pipeline">
            <div className="sidebar-section-title">Planning Pipeline</div>
            <PipelineProgress stages={stages} />
          </div>
        )}

        {!isPlanningMode && (
          <>
            <div className="sidebar-section-title">Quick Start</div>
            <div className="suggestions-list">
              {SUGGESTION_PROMPTS.map((s) => (
                <button key={s} className="suggestion-btn" onClick={() => handleSuggestion(s)}>
                  {s}
                </button>
              ))}
            </div>
          </>
        )}

        <div className="sidebar-footer">
          <div className="powered-by">Powered by Google Gemini</div>
          <div className="powered-sub">LangGraph · FastAPI · Next.js</div>
        </div>
      </aside>

      <main className="chat-main">
        <header className="chat-header">
          <div className="header-left">
            <span className="header-emoji">✈️</span>
            <div>
              <h1 className="header-title">AI Travel Planner</h1>
              <div className="header-sub">India&apos;s smartest trip planning assistant</div>
            </div>
          </div>
          <div className="header-status">
            <span className={`status-dot ${isLoading ? 'active' : ''}`} />
            <span className="status-text">{isLoading ? 'Planning...' : 'Ready'}</span>
          </div>
        </header>

        <div className="messages-container">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} onBookPackage={handleBookPackage} />
          ))}

          {isLoading && (
            <div className="typing-indicator">
              <div className="typing-avatar">🤖</div>
              <div className="typing-dots">
                <span /><span /><span />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <div className="input-wrapper">
            <textarea
              ref={inputRef}
              className="chat-input"
              placeholder="Ask about India travel or describe your dream trip... (e.g. Plan a 5-day Goa trip for Rs.30,000)"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={isLoading}
            />
            <button
              className={`send-btn ${isLoading ? 'loading' : ''}`}
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
            >
              {isLoading ? <span className="send-spinner">⟳</span> : <span>↑</span>}
            </button>
          </div>
          <div className="input-hint">
            Press Enter to send · Shift+Enter for new line
          </div>
        </div>
      </main>
    </div>
  );
}

interface MessageBubbleProps {
  message: ChatMessage;
  onBookPackage: (pkg: TripPackage) => void;
}

function MessageBubble({ message, onBookPackage }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  const [, setSelectedPkg] = useState<number | null>(null);

  if (message.type === 'booking' && message.bookingSummary) {
    return (
      <div className="message-row assistant">
        <div className="msg-avatar">🤖</div>
        <div className="msg-content-wide">
          <BookingSummaryView summary={message.bookingSummary} />
        </div>
      </div>
    );
  }

  if (message.type === 'packages' && message.packages) {
    return (
      <div className="message-row assistant">
        <div className="msg-avatar">🤖</div>
        <div className="msg-content-wide">
          <div className="msg-bubble assistant">
            <MarkdownText text={message.content} />
          </div>
          <div className="packages-grid">
            {message.packages.map((pkg) => (
              <PackageCard
                key={pkg.package_id}
                pkg={pkg}
                onSelect={(p) => setSelectedPkg(p.package_id)}
                onBook={onBookPackage}
              />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`message-row ${isUser ? 'user' : 'assistant'}`}>
      {!isUser && <div className="msg-avatar">🤖</div>}
      <div className={`msg-bubble ${isUser ? 'user' : 'assistant'}`}>
        <MarkdownText text={message.content} />
        <div className="msg-time">
          {message.timestamp.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
        </div>
      </div>
      {isUser && <div className="msg-avatar user-avatar">👤</div>}
    </div>
  );
}

function MarkdownText({ text }: { text: string }) {
  const rendered = text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br/>');
  return <span dangerouslySetInnerHTML={{ __html: rendered }} />;
}
