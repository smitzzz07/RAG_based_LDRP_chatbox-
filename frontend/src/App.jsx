import { useEffect, useState } from "react";
import "./App.css";

import Login from "./pages/Login";
import Signup from "./pages/Signup";

const API_BASE = "http://127.0.0.1:8000/api";
const CHAT_API = `${API_BASE}/chat`;
const AUTH_API = `${API_BASE}/auth`;

const WELCOME_MESSAGE = {
  role: "assistant",
  content:
    "Hello! 👋 I’m the LDRP-ITR AI Assistant. Ask me anything about LDRP, MCA syllabus, courses, and academic information.",
};

const suggestedQuestions = [
  "What is the credit of Software Testing?",
  "What subjects are in MCA Semester 3?",
  "What is the MCA-37 subject?",
  "What is the total credit of Semester 3?",
];

function getSavedUser() {
  try {
    const value = localStorage.getItem("user");
    return value ? JSON.parse(value) : null;
  } catch {
    return null;
  }
}

function clearAuth() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("user");
}

function ChatApp({ user, onLogout }) {
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [question, setQuestion] = useState("");
  const [started, setStarted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [expandedSources, setExpandedSources] = useState({});
  const [conversationId, setConversationId] = useState(null);

  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyOpen, setHistoryOpen] = useState(true);
  const [deletingId, setDeletingId] = useState(null);

  const authHeaders = () => {
    const token = localStorage.getItem("access_token");

    return token
      ? { Authorization: `Bearer ${token}` }
      : {};
  };

  const loadHistory = async () => {
    setHistoryLoading(true);

    try {
      const response = await fetch(`${CHAT_API}/history`, {
        headers: {
          ...authHeaders(),
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          onLogout();
        }
        return;
      }

      const data = await response.json();
      setHistory(Array.isArray(data) ? data : []);
    } catch {
      setHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  const loadConversation = async (id) => {
    if (loading || id === conversationId) return;

    try {
      const response = await fetch(`${CHAT_API}/${id}`, {
        headers: {
          ...authHeaders(),
        },
      });

      if (!response.ok) {
        if (response.status === 401) onLogout();
        return;
      }

      const data = await response.json();

      const loadedMessages =
        data.messages && data.messages.length > 0
          ? data.messages.map((message) => ({
              role: message.role,
              content: message.content,
              sources: message.sources || [],
            }))
          : [WELCOME_MESSAGE];

      setConversationId(data.id);
      setMessages(loadedMessages);
      setStarted(loadedMessages.length > 1);
      setExpandedSources({});
      setQuestion("");
    } catch {
      // Keep the current chat if loading a previous conversation fails.
    }
  };

  const sendMessage = async (text = question) => {
    const userQuestion = text.trim();

    if (!userQuestion || loading) return;

    setStarted(true);

    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: userQuestion,
      },
    ]);

    setQuestion("");
    setLoading(true);

    try {
      const token = localStorage.getItem("access_token");

      const body = {
        question: userQuestion,
      };

      if (conversationId !== null) {
        body.conversation_id = conversationId;
      }

      const response = await fetch(CHAT_API, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      });

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          onLogout();
          return;
        }

        throw new Error(
          data.detail || "Unable to generate an answer."
        );
      }

      if (data.conversation_id) {
        setConversationId(data.conversation_id);
      }

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
          sources: data.sources || [],
          needsWebSearch: data.needs_web_search,
        },
      ]);

      await loadHistory();
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            error.message ||
            "I couldn't connect to the LDRP AI server.",
          error: true,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const newChat = () => {
    setConversationId(null);
    setMessages([WELCOME_MESSAGE]);
    setQuestion("");
    setStarted(false);
    setExpandedSources({});
  };

  const deleteConversation = async (event, id) => {
    event.stopPropagation();

    setDeletingId(id);

    try {
      const response = await fetch(`${CHAT_API}/${id}`, {
        method: "DELETE",
        headers: {
          ...authHeaders(),
        },
      });

      if (!response.ok) {
        if (response.status === 401) onLogout();
        return;
      }

      setHistory((prev) => prev.filter((item) => item.id !== id));

      if (conversationId === id) {
        newChat();
      }
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="app">
      <div className="background">
        <div className="orb orb-one"></div>
        <div className="orb orb-two"></div>
        <div className="orb orb-three"></div>
        <div className="grid"></div>
        <div className="floating-ring ring-one"></div>
        <div className="floating-ring ring-two"></div>
      </div>

      <header className="header glass">
        <div className="header-left">
          <button
            type="button"
            className="header-menu"
            onClick={() => setHistoryOpen((value) => !value)}
            title={historyOpen ? "Hide chat history" : "Show chat history"}
            aria-label="Toggle chat history"
          >
            ☰
          </button>

          <div className="brand">
          <div className="logo-3d">
            <span>L</span>
          </div>

          <div className="brand-text">
            <h1>LDRP-ITR</h1>
            <p>AI Academic Assistant</p>
          </div>
        </div>

        </div>

        <div className="header-right">
          <div className="status">
            <span className="status-dot"></span>
            AI Online
          </div>

          <button className="new-chat" onClick={newChat}>
            + New Chat
          </button>

          <div className="user-menu">
            <div className="user-avatar-small">
              {(user?.name || "U").charAt(0).toUpperCase()}
            </div>

            <div className="user-info">
              <strong>{user?.name || "User"}</strong>
              <span>{user?.email || ""}</span>
            </div>

            <button
              className="logout-button"
              onClick={onLogout}
              title="Logout"
              aria-label="Logout"
            >
              ↪
            </button>
          </div>
        </div>
      </header>

      <div className="workspace">
        <aside className={`history-sidebar ${historyOpen ? "open" : "closed"}`}>
          <div className="history-top">
            <div className="history-heading">
              <div className="history-title">
                <span className="history-title-icon">◫</span>
                <span>Chat History</span>
              </div>
              <span className="history-count">
                {history.length}
              </span>
            </div>

            <button
              className="history-new"
              onClick={newChat}
              title="New chat"
            >
              <span>＋</span>
              <span>New chat</span>
            </button>
          </div>

          <div className="history-list">
            {historyLoading ? (
              <div className="history-empty">
                <div className="history-loader"></div>
                <span>Loading chats...</span>
              </div>
            ) : history.length === 0 ? (
              <div className="history-empty">
                <div className="history-empty-icon">✦</div>
                <strong>No conversations yet</strong>
                <span>Your saved chats will appear here.</span>
              </div>
            ) : (
              history.map((item) => (
                <button
                  className={`history-item ${
                    conversationId === item.id ? "active" : ""
                  }`}
                  key={item.id}
                  onClick={() => loadConversation(item.id)}
                >
                  <span className="history-item-icon">◇</span>

                  <span className="history-item-body">
                    <strong>{item.title}</strong>
                    <small>
                      {new Date(item.updated_at).toLocaleDateString(
                        undefined,
                        {
                          day: "2-digit",
                          month: "short",
                        }
                      )}
                    </small>
                  </span>

                  <span
                    className="history-delete"
                    onClick={(event) =>
                      deleteConversation(event, item.id)
                    }
                    title="Delete conversation"
                  >
                    {deletingId === item.id ? "…" : "×"}
                  </span>
                </button>
              ))
            )}
          </div>

          <div className="history-bottom">
            <div className="history-account">
              <div className="history-account-avatar">
                {(user?.name || "U").charAt(0).toUpperCase()}
              </div>
              <div>
                <strong>{user?.name || "User"}</strong>
                <span>Personal workspace</span>
              </div>
            </div>
          </div>
        </aside>

        <button
          className="history-toggle"
          onClick={() => setHistoryOpen((value) => !value)}
          title={historyOpen ? "Hide history" : "Show history"}
          aria-label="Toggle chat history"
        >
          {historyOpen ? "‹" : "›"}
        </button>

        <main
          className={`chat-container ${
            started ? "chat-started" : ""
          }`}
        >
          <section className={`hero ${started ? "hero-started" : ""}`}>
            <div className="ai-orb">
              <div className="orb-core">🎓</div>
              <div className="orb-ring ring-a"></div>
              <div className="orb-ring ring-b"></div>
            </div>

            <div className="hero-badge">✦ LDRP INTELLIGENCE</div>

            <h2>
              Ask anything.
              <br />
              <span>Get intelligent answers.</span>
            </h2>

            <p>
              Your AI-powered academic assistant for LDRP-ITR
              information and MCA resources.
            </p>

            <div className="compact-chat-title">
              <span className="compact-dot"></span>
              LDRP AI
            </div>
          </section>

          <section
            className={`suggestions ${
              started ? "suggestions-hidden" : ""
            }`}
          >
            {suggestedQuestions.map((item, index) => (
              <button
                className="suggestion glass"
                key={item}
                onClick={() => sendMessage(item)}
                style={{
                  animationDelay: `${index * 0.08}s`,
                }}
              >
                <span className="suggestion-icon">
                  {["📚", "🎓", "🔎", "📊"][index]}
                </span>
                <span>{item}</span>
                <span className="suggestion-arrow">→</span>
              </button>
            ))}
          </section>

          <section
            className={`messages ${
              started ? "messages-visible" : ""
            }`}
          >
            {messages.map((message, index) => (
              <div
                className={`message-row ${message.role}`}
                key={`${conversationId || "new"}-${index}`}
              >
                {message.role === "assistant" ? (
                  <div className="assistant-avatar">L</div>
                ) : (
                  <div className="user-avatar">You</div>
                )}

                <div className="message-content">
                  <div
                    className={`message-bubble ${
                      message.error ? "error" : ""
                    }`}
                  >
                    {message.role === "assistant" && (
                      <div className="assistant-label">
                        LDRP AI
                      </div>
                    )}

                    <div className="answer-text">
                      {message.content}
                    </div>
                  </div>

                  {message.sources &&
                    message.sources.length > 0 &&
                    (() => {
                      const isExpanded =
                        !!expandedSources[index];

                      const visibleSources = isExpanded
                        ? message.sources
                        : message.sources.slice(0, 1);

                      const hiddenCount = Math.max(
                        message.sources.length - 1,
                        0
                      );

                      return (
                        <div className="sources">
                          <div className="sources-title">
                            <span>◈</span>
                            Sources
                          </div>

                          {visibleSources.map(
                            (source, sourceIndex) => (
                              <div
                                className="source-card glass"
                                key={`${index}-${sourceIndex}`}
                              >
                                <div className="source-icon">
                                  {source.source_type ===
                                  "pdf"
                                    ? "📄"
                                    : "🌐"}
                                </div>

                                <div className="source-info">
                                  <strong>
                                    {source.title ||
                                      source.source ||
                                      "LDRP Source"}
                                  </strong>

                                  <span>
                                    {source.source_type ===
                                    "pdf"
                                      ? `PDF • Page ${
                                          source.page ?? "N/A"
                                        }`
                                      : "Official LDRP Website"}
                                  </span>
                                </div>

                                {source.url && (
                                  <a
                                    href={source.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="source-open"
                                  >
                                    Open ↗
                                  </a>
                                )}
                              </div>
                            )
                          )}

                          {message.sources.length > 1 && (
                            <button
                              type="button"
                              className="sources-toggle"
                              onClick={() =>
                                setExpandedSources(
                                  (prev) => ({
                                    ...prev,
                                    [index]: !isExpanded,
                                  })
                                )
                              }
                            >
                              {isExpanded
                                ? "− Show less"
                                : `+ View ${hiddenCount} more`}
                            </button>
                          )}
                        </div>
                      );
                    })()}
                </div>
              </div>
            ))}

            {loading && (
              <div className="message-row assistant">
                <div className="assistant-avatar">L</div>

                <div className="message-content">
                  <div className="message-bubble loading-bubble">
                    <div className="assistant-label">
                      LDRP AI
                    </div>

                    <div className="thinking">
                      <span></span>
                      <span></span>
                      <span></span>
                      <small>Searching knowledge base...</small>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </section>
        </main>
      </div>

      <footer
        className={`input-area ${
          started ? "input-started" : ""
        }`}
      >
        <div className="input-glow"></div>

        <div className="input-wrapper glass">
          <div className="input-icon">✦</div>

          <textarea
            value={question}
            onChange={(event) =>
              setQuestion(event.target.value)
            }
            onKeyDown={handleKeyDown}
            placeholder="Ask LDRP AI anything..."
            rows="1"
            disabled={loading}
          />

          <button
            className="send-button"
            onClick={() => sendMessage()}
            disabled={!question.trim() || loading}
          >
            <span>↑</span>
          </button>
        </div>

        <p>
          LDRP-ITR AI • Powered by RAG & Gemini • Enter to send
        </p>
      </footer>
    </div>
  );
}

function App() {
  const [screen, setScreen] = useState("checking");
  const [user, setUser] = useState(null);

  useEffect(() => {
    const checkAuthentication = async () => {
      const token = localStorage.getItem("access_token");

      if (!token) {
        setScreen("login");
        return;
      }

      try {
        const response = await fetch(`${AUTH_API}/me`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          clearAuth();
          setScreen("login");
          return;
        }

        const data = await response.json();

        const currentUser = {
          id: data.id,
          name: data.name,
          email: data.email,
        };

        localStorage.setItem(
          "user",
          JSON.stringify(currentUser)
        );

        setUser(currentUser);
        setScreen("chat");
      } catch {
        clearAuth();
        setScreen("login");
      }
    };

    checkAuthentication();
  }, []);

  const handleLogin = (loginData) => {
    setUser(loginData);
    setScreen("chat");
  };

  const handleSignup = (signupData) => {
    setUser(signupData);
    setScreen("chat");
  };

  const handleLogout = () => {
    clearAuth();
    setUser(null);
    setScreen("login");
  };

  if (screen === "checking") {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <div className="auth-logo">
            <div className="auth-logo-orb">◈</div>
            <div>
              <h1>LDRP AI</h1>
              <span>Academic Assistant</span>
            </div>
          </div>

          <div className="auth-heading">
            <h2>Checking session...</h2>
            <p>
              Please wait while we verify your account.
            </p>
          </div>

          <div
            className="auth-submit"
            style={{ cursor: "default" }}
          >
            <span className="auth-spinner"></span>
            Loading...
          </div>
        </div>
      </div>
    );
  }

  if (screen === "login") {
    return (
      <Login
        onLogin={handleLogin}
        onShowSignup={() => setScreen("signup")}
      />
    );
  }

  if (screen === "signup") {
    return (
      <Signup
        onSignup={handleSignup}
        onShowLogin={() => setScreen("login")}
      />
    );
  }

  return (
    <ChatApp
      user={user || getSavedUser()}
      onLogout={handleLogout}
    />
  );
}

export default App;
