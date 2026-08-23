'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { PackageCard } from '@/components/PackageCard';
import { BookingSummaryView } from '@/components/BookingSummaryView';
import { PipelineProgress } from '@/components/PipelineProgress';
import { sendChat, streamTripPlan, fetchSessions, fetchSessionMessages, deleteSessionApi } from '@/lib/api';
import type {
  ChatMessage,
  TripPackage,
  BookingSummary,
  PipelineStage,
  ParsedTrip,
  BudgetAllocation,
  SSEEvent,
  SavedSession,
} from '@/types/travel';

const INITIAL_STAGES: PipelineStage[] = [
  { id: 'parsing',    label: 'Parsing Request',     icon: '🔍', status: 'idle' },
  { id: 'searching',  label: 'Searching Options',   icon: '🌐', status: 'idle' },
  { id: 'ranking',    label: 'Building Itinerary',  icon: '🎯', status: 'idle' },
  { id: 'presenting', label: 'Preparing Packages',  icon: '📦', status: 'idle' },
  { id: 'booking',    label: 'Booking Summary',     icon: '🎉', status: 'idle' },
];

const SUGGESTIONS = [
  { icon: '🏔️', text: '7-day Manali adventure for 1 person, ₹25,000' },
  { icon: '🏖️', text: '5-day Goa trip for 2, budget ₹35,000' },
  { icon: '🌴', text: 'Kerala backwaters trip, 6 days, ₹40,000 for couple' },
  { icon: '🏰', text: 'Rajasthan heritage tour, 8 days, ₹60,000' },
  { icon: '🏝️', text: 'Andaman Islands 5 days for 2, ₹55,000' },
  { icon: '🌄', text: 'Ladakh trip, 10 days, ₹80,000 for 2' },
];

const WELCOME_MESSAGE: ChatMessage = {
  id: 'welcome',
  role: 'assistant',
  content: `Namaste! 🙏 I am **Yatra AI**, your luxury Indian travel planner.\n\nTell me your dream destination, budget, and trip length — and I will generate **5 custom packages** with hotels, transport, and day-by-day itineraries.\n\nYou can also ask me anything about travel in India! 🌏`,
  timestamp: new Date(),
  type: 'text',
};

export default function ChatPage() {
  const [messages, setMessages]                 = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [input, setInput]                       = useState('');
  const [isLoading, setIsLoading]               = useState(false);
  const [sessionId, setSessionId]               = useState<string>(() => uuidv4());
  const [stages, setStages]                     = useState<PipelineStage[]>(INITIAL_STAGES);
  const [isPlanningMode, setIsPlanningMode]     = useState(false);
  const [savedSessions, setSavedSessions]       = useState<SavedSession[]>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const inputRef       = useRef<HTMLTextAreaElement>(null);
  const stopStreamRef  = useRef<(() => void) | null>(null);

  // Load saved sessions from PostgreSQL in Docker on mount
  const refreshSessions = useCallback(async () => {
    const list = await fetchSessions();
    setSavedSessions(list);
  }, []);

  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const addMessage = useCallback((msg: Omit<ChatMessage, 'id' | 'timestamp'>) => {
    setMessages((prev) => [...prev, { ...msg, id: uuidv4(), timestamp: new Date() }]);
  }, []);

  const updateStage = useCallback(
    (stageId: string, status: PipelineStage['status'], message?: string) => {
      setStages((prev) =>
        prev.map((s) => (s.id === stageId ? { ...s, status, message } : s))
      );
    },
    []
  );

  const resetStages = useCallback(() => {
    setStages(INITIAL_STAGES.map((s) => ({ ...s, status: 'idle' })));
  }, []);

  // Start new session
  const handleNewSession = () => {
    const newId = uuidv4();
    setSessionId(newId);
    setMessages([WELCOME_MESSAGE]);
    resetStages();
    setIsPlanningMode(false);
    setIsLoading(false);
    if (stopStreamRef.current) stopStreamRef.current();
  };

  // Load existing session
  const handleSelectSession = async (s: SavedSession) => {
    setSessionId(s.id);
    resetStages();
    setIsPlanningMode(false);
    setIsLoading(true);
    const history = await fetchSessionMessages(s.id);
    if (history.length > 0) {
      setMessages(history);
    } else {
      setMessages([WELCOME_MESSAGE]);
    }
    setIsLoading(false);
  };

  // Delete a session
  const handleDeleteSession = async (e: React.MouseEvent, sid: string) => {
    e.stopPropagation();
    await deleteSessionApi(sid);
    if (sessionId === sid) {
      handleNewSession();
    }
    refreshSessions();
  };

  const handleSSEEvent = useCallback(
    (event: SSEEvent) => {
      const { type, stage, message, data } = event;

      if (type === 'start') {
        setIsPlanningMode(true);
        addMessage({ role: 'assistant', content: 'Starting your trip planning pipeline...', type: 'text' });
      }

      if (type === 'stage_start' && stage) updateStage(stage, 'running', message);

      if (type === 'stage_done' && stage) {
        updateStage(stage, 'done');

        if (stage === 'parsing' && data) {
          const parsedTrip  = (data as { parsed_trip?: ParsedTrip; budget_allocation?: BudgetAllocation }).parsed_trip;
          const budgetAlloc = (data as { parsed_trip?: ParsedTrip; budget_allocation?: BudgetAllocation }).budget_allocation;
          if (parsedTrip && budgetAlloc) {
            addMessage({
              role: 'assistant',
              content: `Got it! Planning your trip to **${parsedTrip.destination}**\n\nBudget Breakdown:\n- Stay: ₹${budgetAlloc.stay.toLocaleString('en-IN')}\n- Transport: ₹${budgetAlloc.transport.toLocaleString('en-IN')}\n- Food: ₹${budgetAlloc.food.toLocaleString('en-IN')}\n- Rentals: ₹${budgetAlloc.local_rental.toLocaleString('en-IN')}`,
              type: 'text',
            });
          }
        }

        if (stage === 'searching' && data) {
          const d = data as { stays_count?: number; transports_count?: number; rentals_count?: number };
          addMessage({
            role: 'assistant',
            content: `Search complete! Found ${d.stays_count ?? 0} stays, ${d.transports_count ?? 0} transport options, ${d.rentals_count ?? 0} rentals.`,
            type: 'text',
          });
        }
      }

      if (type === 'complete' && event.full_state) {
        const fullState = event.full_state as Record<string, unknown>;
        const packages  = ((fullState.presented_packages ?? fullState.ranked_packages) as TripPackage[]) ?? [];
        const bookingSummary = fullState.booking_summary as BookingSummary | null;

        if (packages.length > 0) {
          addMessage({
            role: 'assistant',
            content: `Here are your ${packages.length} personalised trip packages! Scroll through the cards below and use the photo arrows to explore each place.`,
            type: 'packages',
            packages,
            bookingSummary: bookingSummary ?? undefined,
          });
        }

        setIsPlanningMode(false);
        setIsLoading(false);
        if (event.session_id) setSessionId(event.session_id);
        refreshSessions();
      }

      if (type === 'error') {
        addMessage({
          role: 'assistant',
          content: `Something went wrong: ${message ?? 'Unknown error'}. Please try again.`,
          type: 'text',
        });
        setIsPlanningMode(false);
        setIsLoading(false);
        resetStages();
      }
    },
    [addMessage, updateStage, resetStages, refreshSessions]
  );

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
      refreshSessions();

      if (chatResponse.is_trip_request) {
        addMessage({ role: 'assistant', content: chatResponse.response, type: 'text' });
        const planQuery = chatResponse.suggested_query ?? query;
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
          () => {
            setIsLoading(false);
            refreshSessions();
          }
        );
      } else {
        addMessage({ role: 'assistant', content: chatResponse.response, type: 'text' });
        setIsLoading(false);
      }
    } catch {
      addMessage({
        role: 'assistant',
        content: 'Could not connect to the server. Make sure the backend is running.',
        type: 'text',
      });
      setIsLoading(false);
    }
  }, [input, isLoading, messages, sessionId, addMessage, resetStages, handleSSEEvent, refreshSessions]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const handleSuggestion = (text: string) => {
    setInput(text);
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
      {/* ── Sidebar ─────────────────────────────────────────── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-icon-wrap">🌏</div>
          <div>
            <div className="logo-title">Yatra AI</div>
            <div className="logo-sub">Luxury India Travel</div>
          </div>
        </div>

        {/* New Trip Button */}
        <button className="new-session-btn" onClick={handleNewSession}>
          <span className="btn-plus">✨</span>
          <span>New Trip Plan</span>
        </button>

        <div className="sidebar-divider" />

        {/* Saved Sessions in Docker DB */}
        {savedSessions.length > 0 && (
          <div className="sidebar-sessions-section">
            <div className="sidebar-section-title">Saved Trips & Chats</div>
            <div className="sessions-list">
              {savedSessions.map((s) => (
                <div
                  key={s.id}
                  className={`session-item ${s.id === sessionId ? 'active' : ''}`}
                  onClick={() => handleSelectSession(s)}
                >
                  <span className="session-icon">🗺️</span>
                  <span className="session-title">{s.title}</span>
                  <button
                    className="session-del-btn"
                    onClick={(e) => handleDeleteSession(e, s.id)}
                    title="Delete Conversation"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Pipeline or Quick Start */}
        {(isPlanningMode || stages.some((s) => s.status !== 'idle')) ? (
          <div className="sidebar-pipeline">
            <div className="sidebar-section-title">Live Planning Pipeline</div>
            <PipelineProgress stages={stages} />
          </div>
        ) : (
          <>
            <div className="sidebar-section-title">Popular Trips</div>
            <div className="suggestions-list">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s.text}
                  className="suggestion-btn"
                  onClick={() => handleSuggestion(s.text)}
                >
                  <span className="sugg-icon">{s.icon}</span>
                  <span>{s.text}</span>
                </button>
              ))}
            </div>
          </>
        )}

        <div className="sidebar-footer">
          <div className="docker-badge">
            <span className="docker-dot" /> PostgreSQL in Docker Active
          </div>
          <div className="powered-by">LangGraph · Gemini · Next.js</div>
        </div>
      </aside>

      {/* ── Main Chat ───────────────────────────────────────── */}
      <main className="chat-main">
        {/* Header */}
        <header className="chat-header">
          <div className="header-left">
            <div className="header-icon-wrap">✈️</div>
            <div>
              <h1 className="header-title">Yatra AI Travel Planner</h1>
              <div className="header-sub">Personalised 5-package itineraries with real stays & transport</div>
            </div>
          </div>
          <div className="header-status">
            <span className={`status-dot ${isLoading ? 'active' : ''}`} />
            <span className="status-text">{isLoading ? 'AI Agent Planning...' : 'Agent Ready'}</span>
          </div>
        </header>

        {/* Messages */}
        <div className="messages-container" ref={messagesContainerRef}>
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} onBookPackage={handleBookPackage} />
          ))}

          {isLoading && (
            <div className="typing-indicator">
              <div className="msg-avatar">🤖</div>
              <div className="typing-dots">
                <span /><span /><span />
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="input-container">
          <div className="input-wrapper">
            <textarea
              ref={inputRef}
              className="chat-input"
              placeholder="Describe your dream India trip... (e.g. Plan a 7-day Manali adventure for ₹25,000)"
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
              title="Send Message"
            >
              {isLoading
                ? <span className="send-spinner">⟳</span>
                : <span>↑</span>
              }
            </button>
          </div>
          <div className="input-hint">
            Press Enter to send &middot; Shift+Enter for new line &middot; Stored in Docker Database
          </div>
        </div>
      </main>
    </div>
  );
}

/* ── MessageBubble ───────────────────────────────────────── */
interface MessageBubbleProps {
  message: ChatMessage;
  onBookPackage: (pkg: TripPackage) => void;
}

function MessageBubble({ message, onBookPackage }: MessageBubbleProps) {
  const isUser = message.role === 'user';

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
            {message.packages.map((pkg, idx) => (
              <PackageCard
                key={pkg.package_id}
                pkg={pkg}
                index={idx}
                onSelect={() => {}}
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
          {new Date(message.timestamp).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
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
