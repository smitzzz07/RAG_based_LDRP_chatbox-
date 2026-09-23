import { useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000/api/chat";

const suggestedQuestions = [
  "What is the credit of Software Testing?",
  "What subjects are in MCA Semester 3?",
  "What is the MCA-37 subject?",
  "What is the total credit of Semester 3?",
];

function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! 👋 I’m the LDRP-ITR AI Assistant. Ask me anything about LDRP, MCA syllabus, courses, and academic information.",
    },
  ]);

  const [question, setQuestion] = useState("");
  const [started, setStarted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [expandedSources, setExpandedSources] = useState({});

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
      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: userQuestion,
        }),
      });

      if (!response.ok) {
        throw new Error("API request failed");
      }

      const data = await response.json();

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.answer,
          sources: data.sources || [],
          needsWebSearch: data.needs_web_search,
        },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "I couldn't connect to the LDRP AI server. Please make sure the FastAPI backend is running.",
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

  const clearChat = () => {
    setExpandedSources({});
    setStarted(false);
    setMessages([
      {
        role: "assistant",
        content:
          "Hello! 👋 I’m the LDRP-ITR AI Assistant. Ask me anything about LDRP, MCA syllabus, courses, and academic information.",
      },
    ]);
  };

  return (
    <div className="app">

      {/* Background 3D decoration */}
      <div className="background">
        <div className="orb orb-one"></div>
        <div className="orb orb-two"></div>
        <div className="orb orb-three"></div>

        <div className="grid"></div>

        <div className="floating-ring ring-one"></div>
        <div className="floating-ring ring-two"></div>
      </div>

      {/* Header */}
      <header className="header glass">

        <div className="brand">

          <div className="logo-3d">
            <span>L</span>
          </div>

          <div className="brand-text">
            <h1>LDRP-ITR</h1>
            <p>AI Academic Assistant</p>
          </div>

        </div>

        <div className="header-right">

          <div className="status">
            <span className="status-dot"></span>
            AI Online
          </div>

          <button
            className="new-chat"
            onClick={clearChat}
          >
            + New Chat
          </button>

        </div>

      </header>

      {/* Main */}
      <main className={`chat-container ${started ? "chat-started" : ""}`}>

        {/* Hero */}
        <section className={`hero ${started ? "hero-started" : ""}`}>

          <div className="ai-orb">

            <div className="orb-core">
              🎓
            </div>

            <div className="orb-ring ring-a"></div>
            <div className="orb-ring ring-b"></div>

          </div>

          <div className="hero-badge">
            ✦ LDRP INTELLIGENCE
          </div>

          <h2>
            Ask anything.
            <br />
            <span>Get intelligent answers.</span>
          </h2>

          <p>
            Your AI-powered academic assistant for
            LDRP-ITR information and MCA resources.
          </p>

          <div className="compact-chat-title">
            <span className="compact-dot"></span>
            LDRP AI
          </div>

        </section>

        {/* Suggestions */}
        <section className={`suggestions ${started ? "suggestions-hidden" : ""}`}>

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

              <span className="suggestion-arrow">
                →
              </span>

            </button>

          ))}

        </section>

        {/* Messages */}
        <section className={`messages ${started ? "messages-visible" : ""}`}>

          {messages.map((message, index) => (

            <div
              className={`message-row ${message.role}`}
              key={index}
            >

              {message.role === "assistant" ? (

                <div className="assistant-avatar">
                  L
                </div>

              ) : (

                <div className="user-avatar">
                  You
                </div>

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

                {/* Sources */}
                {message.sources && message.sources.length > 0 && (() => {
                  const isExpanded = !!expandedSources[index];
                  const visibleSources = isExpanded
                    ? message.sources
                    : message.sources.slice(0, 1);
                  const hiddenCount = Math.max(message.sources.length - 1, 0);

                  return (
                    <div className="sources">
                      <div className="sources-title">
                        <span>◈</span>
                        Sources
                      </div>

                      {visibleSources.map((source, sourceIndex) => (
                        <div
                          className="source-card glass"
                          key={`${index}-${sourceIndex}`}
                        >
                          <div className="source-icon">
                            {source.source_type === "pdf" ? "📄" : "🌐"}
                          </div>

                         <div className="source-info">
  <strong>
    {source.title ||
      source.source ||
      "LDRP Source"}
  </strong>

  <span>
    {source.source_type === "web"
      ? `Web Search${
          source.url
            ? ` • ${new URL(source.url).hostname.replace("www.", "")}`
            : ""
        }`
      : `PDF • Page ${source.page ?? "N/A"}`}
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
                      ))}

                      {message.sources.length > 1 && (
                        <button
                          type="button"
                          className="sources-toggle"
                          onClick={() =>
                            setExpandedSources((prev) => ({
                              ...prev,
                              [index]: !isExpanded,
                            }))
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

          {/* Loading */}
          {loading && (

            <div className="message-row assistant">

              <div className="assistant-avatar">
                L
              </div>

              <div className="message-content">

                <div className="message-bubble loading-bubble">

                  <div className="assistant-label">
                    LDRP AI
                  </div>

                  <div className="thinking">

                    <span></span>
                    <span></span>
                    <span></span>

                    <small>
                      Searching knowledge base...
                    </small>

                  </div>

                </div>

              </div>

            </div>

          )}

        </section>

      </main>

      {/* Input */}
      <footer className={`input-area ${started ? "input-started" : ""}`}>

        <div className="input-glow"></div>

        <div className="input-wrapper glass">

          <div className="input-icon">
            ✦
          </div>

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

export default App; 