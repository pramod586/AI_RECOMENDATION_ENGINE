import { useCallback, useEffect, useRef, useState } from "react";
import "./App.css";
import Auth from "./auth";

const API_BASE =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

const getErrorMessage = (error) =>
  error instanceof Error ? error.message : "Something went wrong.";


function App() {
  // ============================================================
  // AUTHENTICATION STATE
  // ============================================================

  const [token, setToken] = useState(
    () => sessionStorage.getItem("access_token") || ""
  );

  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const savedUser = sessionStorage.getItem("current_user");
      return savedUser ? JSON.parse(savedUser) : null;
    } catch {
      return null;
    }
  });

  const [authChecking, setAuthChecking] = useState(true);
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");
  const [authNotice, setAuthNotice] = useState("");


  // ============================================================
  // CHATBOT STATE
  // ============================================================

  const [serverStatus, setServerStatus] = useState("checking");

  const [conversations, setConversations] = useState([]);

  const [activeConversation, setActiveConversation] =
    useState(null);

  const [messages, setMessages] = useState([]);

  const [input, setInput] = useState("");

  const [loading, setLoading] = useState(false);

  const [uploading, setUploading] = useState(false);

  const [error, setError] = useState("");

  const [sidebarOpen, setSidebarOpen] = useState(false);

  const [uploadedDocuments, setUploadedDocuments] = useState([]);


  // ============================================================
  // REFS
  // ============================================================

  const messagesEndRef = useRef(null);

  const fileInputRef = useRef(null);


  // ============================================================
  // AUTHENTICATION HEADERS
  // ============================================================

  const getAuthHeaders = (additionalHeaders = {}) => ({
    ...additionalHeaders,
    ...(token
      ? {
          Authorization: `Bearer ${token}`,
        }
      : {}),
  });


  // ============================================================
  // CLEAR SESSION
  // ============================================================

  const clearSession = () => {
    sessionStorage.removeItem("access_token");
    sessionStorage.removeItem("current_user");

    setToken("");
    setCurrentUser(null);

    setMessages([]);
    setConversations([]);
    setActiveConversation(null);
    setUploadedDocuments([]);
    setInput("");
    setError("");

    setAuthError("");
  };


  // ============================================================
  // VERIFY SAVED SESSION
  // ============================================================

  useEffect(() => {
    let cancelled = false;

    const verifySession = async () => {
      const savedToken =
        sessionStorage.getItem("access_token");

      if (!savedToken) {
        if (!cancelled) {
          setToken("");
          setCurrentUser(null);
          setAuthChecking(false);
        }

        return;
      }

      try {
        const response = await fetch(
          `${API_BASE}/auth/me`,
          {
            method: "GET",
            headers: {
              Authorization: `Bearer ${savedToken}`,
            },
          }
        );

        if (!response.ok) {
          throw new Error("Session expired");
        }

        const user = await response.json();

        if (!cancelled) {
          setToken(savedToken);

          setCurrentUser(user);

          sessionStorage.setItem(
            "current_user",
            JSON.stringify(user)
          );
        }
      } catch {
        sessionStorage.removeItem(
          "access_token"
        );

        sessionStorage.removeItem(
          "current_user"
        );

        if (!cancelled) {
          setToken("");
          setCurrentUser(null);
        }
      } finally {
        if (!cancelled) {
          setAuthChecking(false);
        }
      }
    };

    verifySession();

    return () => {
      cancelled = true;
    };
  }, []);


  // ============================================================
  // LOGIN
  // ============================================================

  const handleLogin = async (credentials) => {
    setAuthLoading(true);
    setAuthError("");
    setAuthNotice("");

    try {
      const response = await fetch(
        `${API_BASE}/auth/login`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify(credentials),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Login failed"
        );
      }

      sessionStorage.setItem(
        "access_token",
        data.access_token
      );

      sessionStorage.setItem(
        "current_user",
        JSON.stringify(data.user)
      );

      setToken(data.access_token);

      setCurrentUser(data.user);

      setAuthError("");
      setAuthNotice("");
    } catch (err) {
      setAuthError(getErrorMessage(err));
    } finally {
      setAuthLoading(false);
    }
  };


  // ============================================================
  // REGISTER
  // ============================================================

  const handleRegister = async (userData) => {
    setAuthLoading(true);
    setAuthError("");
    setAuthNotice("");

    try {
      const response = await fetch(
        `${API_BASE}/auth/register`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify(userData),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Registration failed"
        );
      }

      // Clear existing login session
      sessionStorage.removeItem(
        "access_token"
      );

      sessionStorage.removeItem(
        "current_user"
      );

      setToken("");
      setCurrentUser(null);

      // Clear chatbot data
      setMessages([]);
      setConversations([]);
      setActiveConversation(null);
      setUploadedDocuments([]);
      setInput("");

      setAuthNotice(
        "Your account has been created successfully! Please log in with your email and password."
      );

      setAuthError("");
    } catch (err) {
      setAuthError(getErrorMessage(err));
    } finally {
      setAuthLoading(false);
    }
  };


  // ============================================================
  // LOGOUT
  // ============================================================

  const handleLogout = () => {
    clearSession();
  };


  // ============================================================
  // SCROLL TO LATEST MESSAGE
  // ============================================================

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  };


  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);


  // ============================================================
  // CHECK BACKEND CONNECTION
  // ============================================================

  const checkBackend = useCallback(async () => {
    try {
      const response = await fetch(
        `${API_BASE}/health`
      );

      if (!response.ok) {
        throw new Error(
          "Backend unavailable"
        );
      }

      setServerStatus("connected");
    } catch {
      setServerStatus("disconnected");
    }
  }, []);


  // ============================================================
  // LOAD CONVERSATIONS
  // ============================================================

  const loadConversations = useCallback(async () => {
    if (!token) return;

    try {
      const response = await fetch(
        `${API_BASE}/api/conversations/`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.status === 401) {
        clearSession();
        return;
      }

      if (!response.ok) {
        throw new Error(
          "Could not load conversations"
        );
      }

      const data = await response.json();

      setConversations(
        Array.isArray(data)
          ? data
          : data.conversations || []
      );
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }, [token]);


  // ============================================================
  // INITIAL BACKEND CHECK
  // ============================================================

  useEffect(() => {
    checkBackend();
  }, [checkBackend]);


  // ============================================================
  // LOAD CONVERSATIONS AFTER LOGIN
  // ============================================================

  useEffect(() => {
    if (token && currentUser) {
      loadConversations();
    }
  }, [
    token,
    currentUser,
    loadConversations,
  ]);


  // ============================================================
  // LOAD MESSAGES
  // ============================================================

  const loadMessages = async (
    conversationId
  ) => {
    try {
      const response = await fetch(
        `${API_BASE}/api/conversations/${conversationId}/messages`,
        {
          headers: getAuthHeaders(),
        }
      );

      if (response.status === 401) {
        clearSession();
        return;
      }

      if (!response.ok) {
        throw new Error(
          "Could not load messages"
        );
      }

      const data = await response.json();

      setMessages(
        Array.isArray(data)
          ? data
          : data.messages || []
      );
    } catch (err) {
      setError(getErrorMessage(err));
      setMessages([]);
    }
  };


  // ============================================================
  // CREATE NEW CHAT
  // ============================================================

  const createNewChat = () => {
    setActiveConversation(null);

    setMessages([]);

    setInput("");

    setError("");

    setSidebarOpen(false);
  };


  // ============================================================
  // SELECT CONVERSATION
  // ============================================================

  const selectConversation = async (
    conversation
  ) => {
    setActiveConversation(conversation);

    setError("");

    await loadMessages(conversation.id);

    setSidebarOpen(false);
  };


  // ============================================================
  // RENAME CONVERSATION
  // ============================================================

  const renameConversation = async (
    conversation
  ) => {
    const currentTitle =
      conversation.title ||
      "New conversation";

    const newTitle = window.prompt(
      "Enter a new conversation name:",
      currentTitle
    );

    if (newTitle === null) {
      return;
    }

    const title = newTitle.trim();

    if (!title) {
      setError(
        "Conversation title cannot be empty."
      );

      return;
    }

    try {
      const response = await fetch(
        `${API_BASE}/api/conversations/${conversation.id}`,
        {
          method: "PATCH",

          headers: getAuthHeaders({
            "Content-Type":
              "application/json",
          }),

          body: JSON.stringify({
            title,
          }),
        }
      );

      if (response.status === 401) {
        clearSession();
        return;
      }

      if (!response.ok) {
        const details =
          await response
            .json()
            .catch(() => ({}));

        throw new Error(
          details.detail ||
            "Unable to rename conversation."
        );
      }

      const updatedConversation =
        await response.json();

      setConversations((previous) =>
        previous.map((item) =>
          item.id ===
          updatedConversation.id
            ? updatedConversation
            : item
        )
      );

      setActiveConversation((previous) =>
        previous?.id ===
        updatedConversation.id
          ? updatedConversation
          : previous
      );

      setError("");
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };


  // ============================================================
  // DELETE CONVERSATION
  // ============================================================

  const deleteConversation = async (
    conversation
  ) => {
    const confirmed = window.confirm(
      `Delete "${
        conversation.title ||
        "New conversation"
      }"?`
    );

    if (!confirmed) {
      return;
    }

    try {
      const response = await fetch(
        `${API_BASE}/api/conversations/${conversation.id}`,
        {
          method: "DELETE",

          headers: getAuthHeaders(),
        }
      );

      if (response.status === 401) {
        clearSession();
        return;
      }

      if (!response.ok) {
        const details =
          await response
            .json()
            .catch(() => ({}));

        throw new Error(
          details.detail ||
            "Unable to delete conversation."
        );
      }

      setConversations((previous) =>
        previous.filter(
          (item) =>
            item.id !== conversation.id
        )
      );

      if (
        activeConversation?.id ===
        conversation.id
      ) {
        setActiveConversation(null);

        setMessages([]);

        setInput("");
      }

      setError("");
    } catch (err) {
      setError(getErrorMessage(err));
    }
  };


  // ============================================================
  // SEND MESSAGE
  // ============================================================

  const sendMessage = async (event) => {
    event?.preventDefault();

    const question = input.trim();

    if (
      !question ||
      loading ||
      !token
    ) {
      return;
    }

    setError("");

    setInput("");

    const temporaryMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: question,
    };

    setMessages((previous) => [
      ...previous,
      temporaryMessage,
    ]);

    setLoading(true);

    try {
      let conversationId =
        activeConversation?.id;


      // --------------------------------------------------------
      // CREATE CONVERSATION IF NEEDED
      // --------------------------------------------------------

      if (!conversationId) {
        const createResponse =
          await fetch(
            `${API_BASE}/api/conversations/`,
            {
              method: "POST",

              headers: getAuthHeaders({
                "Content-Type":
                  "application/json",
              }),

              body: JSON.stringify({
                title:
                  question.slice(0, 60),
              }),
            }
          );

        if (
          createResponse.status === 401
        ) {
          clearSession();

          throw new Error(
            "Your session has expired. Please log in again."
          );
        }

        if (!createResponse.ok) {
          const details =
            await createResponse
              .json()
              .catch(() => ({}));

          throw new Error(
            details.detail ||
              "Unable to create a conversation"
          );
        }

        const newConversation =
          await createResponse.json();

        conversationId =
          newConversation.id;

        setActiveConversation(
          newConversation
        );

        setConversations(
          (previous) => [
            newConversation,
            ...previous,
          ]
        );
      }


      // --------------------------------------------------------
      // SEND QUESTION TO RAG API
      // --------------------------------------------------------

      const response = await fetch(
        `${API_BASE}/api/chat/`,
        {
          method: "POST",

          headers: getAuthHeaders({
            "Content-Type":
              "application/json",
          }),

          body: JSON.stringify({
            conversation_id:
              conversationId,

            message: question,
          }),
        }
      );

      if (response.status === 401) {
        clearSession();

        throw new Error(
          "Your session has expired. Please log in again."
        );
      }

      if (!response.ok) {
        const details =
          await response
            .json()
            .catch(() => ({}));

        throw new Error(
          details.detail ||
            "The AI could not process your question"
        );
      }

      const data =
        await response.json();


      // --------------------------------------------------------
      // ASSISTANT RESPONSE
      // --------------------------------------------------------

      const assistantMessage = {
        id: `assistant-${Date.now()}`,

        role: "assistant",

        content: data.answer,

        sources: data.sources || [],
      };

      setMessages((previous) => [
        ...previous.filter(
          (message) =>
            message.id !==
            temporaryMessage.id
        ),

        temporaryMessage,

        assistantMessage,
      ]);


      // Refresh conversation list
      await loadConversations();
    } catch (err) {
      setMessages((previous) =>
        previous.filter(
          (message) =>
            message.id !==
            temporaryMessage.id
        )
      );

      setInput(question);

      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };


  // ============================================================
  // UPLOAD DOCUMENT
  // ============================================================

  const uploadDocument = async (
    event
  ) => {
    const file =
      event.target.files?.[0];

    if (!file) {
      return;
    }

    setError("");

    setUploading(true);

    try {
      const formData =
        new FormData();

      formData.append(
        "file",
        file
      );

      const response = await fetch(
        `${API_BASE}/api/documents/upload`,
        {
          method: "POST",

          headers: getAuthHeaders(),

          body: formData,
        }
      );

      if (response.status === 401) {
        clearSession();

        throw new Error(
          "Your session has expired. Please log in again."
        );
      }

      if (!response.ok) {
        const details =
          await response
            .json()
            .catch(() => ({}));

        throw new Error(
          details.detail ||
            "Document upload failed"
        );
      }

      const data =
        await response.json();

      setUploadedDocuments(
        (previous) => [
          {
            id:
              data.id ||
              Date.now(),

            name:
              data.filename ||
              data.file_name ||
              file.name,
          },

          ...previous,
        ]
      );
    } catch (err) {
      setError(
        getErrorMessage(err)
      );
    } finally {
      setUploading(false);

      event.target.value = "";
    }
  };


  // ============================================================
  // AUTH LOADING SCREEN
  // ============================================================

  if (authChecking) {
    return (
      <div className="auth-loading-screen">
        <div className="auth-spinner"></div>

        <p>
          Checking your login session...
        </p>
      </div>
    );
  }


  // ============================================================
  // LOGIN SCREEN
  // ============================================================

  if (!token || !currentUser) {
    return (
      <Auth
        onLogin={handleLogin}
        onRegister={handleRegister}
        loading={authLoading}
        error={authError}
        notice={authNotice}
      />
    );
  }


  // ============================================================
  // MAIN CHATBOT INTERFACE
  // ============================================================

  return (
    <div className="app-shell">

      {/* ======================================================
          MOBILE SIDEBAR OVERLAY
          ====================================================== */}

      {sidebarOpen && (
        <button
          className="mobile-overlay"
          aria-label="Close sidebar"
          onClick={() =>
            setSidebarOpen(false)
          }
        />
      )}


      {/* ======================================================
          SIDEBAR
          ====================================================== */}

      <aside
        className={`sidebar ${
          sidebarOpen
            ? "sidebar-open"
            : ""
        }`}
      >

        {/* ----------------------------------------------------
            SIDEBAR BRAND
            ---------------------------------------------------- */}

        <div className="sidebar-brand">

          <div className="brand-icon">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M12 2.8 14.5 9.5 21.2 12 14.5 14.5 12 21.2 9.5 14.5 2.8 12 9.5 9.5 12 2.8Z"
                stroke="currentColor"
                strokeWidth="1.7"
                strokeLinejoin="round"
              />

              <path
                d="m19 2 .8 2.2L22 5l-2.2.8L19 8l-.8-2.2L16 5l2.2-.8L19 2Z"
                fill="currentColor"
              />
            </svg>
          </div>

          <div>
            <h1>
              Knowledge AI
            </h1>

            <span>
              Intelligent workspace
            </span>
          </div>

          <button
            className="mobile-close"
            onClick={() =>
              setSidebarOpen(false)
            }
            aria-label="Close menu"
          >
            ×
          </button>
        </div>


        {/* ----------------------------------------------------
            NEW CONVERSATION
            ---------------------------------------------------- */}

        <button
          className="new-chat-button"
          onClick={createNewChat}
        >
          <span className="plus-icon">
            +
          </span>

          <span>
            New conversation
          </span>

          <span className="shortcut">
            ⌘ K
          </span>
        </button>


        {/* ----------------------------------------------------
            WORKSPACE
            ---------------------------------------------------- */}

        <div className="sidebar-section">

          <div className="section-heading">
            <span>
              WORKSPACE
            </span>
          </div>


          <button
            className="nav-item active"
          >
            <span className="nav-icon">
              ✦
            </span>

            <span>
              AI Assistant
            </span>
          </button>


          <button
            className="nav-item"
            onClick={() =>
              fileInputRef.current?.click()
            }
          >
            <span className="nav-icon">
              ▤
            </span>

            <span>
              Knowledge documents
            </span>

            {uploadedDocuments.length >
              0 && (
              <span className="nav-count">
                {
                  uploadedDocuments.length
                }
              </span>
            )}
          </button>

        </div>


        {/* ----------------------------------------------------
            RECENT CONVERSATIONS
            ---------------------------------------------------- */}

        <div className="sidebar-section history-section">

          <div className="section-heading">
            <span>
              RECENT CONVERSATIONS
            </span>
          </div>


          <div className="conversation-list">

            {conversations.length ===
            0 ? (
              <p className="empty-history">
                Your conversations will
                appear here.
              </p>
            ) : (
              conversations.map(
                (conversation) => (
                  <div
                    key={
                      conversation.id
                    }
                    className={`conversation-item ${
                      activeConversation?.id ===
                      conversation.id
                        ? "selected"
                        : ""
                    }`}
                    style={{
                      display: "flex",
                      alignItems:
                        "center",
                      width: "100%",
                    }}
                  >

                    {/* Conversation selector */}

                    <button
                      type="button"
                      className="conversation-select"
                      onClick={() =>
                        selectConversation(
                          conversation
                        )
                      }
                      style={{
                        flex: 1,
                        minWidth: 0,
                        display:
                          "flex",
                        alignItems:
                          "center",
                        gap: "8px",
                        border: "none",
                        background:
                          "transparent",
                        color:
                          "inherit",
                        cursor:
                          "pointer",
                        textAlign:
                          "left",
                      }}
                    >

                      <span className="conversation-symbol">
                        ◷
                      </span>

                      <span className="conversation-title">
                        {
                          conversation.title ||
                          "New conversation"
                        }
                      </span>

                    </button>


                    {/* Conversation actions */}

                    <div
                      className="conversation-actions"
                      style={{
                        display:
                          "flex",
                        alignItems:
                          "center",
                        gap: "2px",
                        flexShrink: 0,
                      }}
                    >

                      {/* Rename */}

                      <button
                        type="button"
                        title="Rename conversation"
                        aria-label="Rename conversation"
                        onClick={(
                          event
                        ) => {
                          event.stopPropagation();

                          renameConversation(
                            conversation
                          );
                        }}
                        style={{
                          border:
                            "none",
                          background:
                            "transparent",
                          color:
                            "inherit",
                          cursor:
                            "pointer",
                          padding:
                            "5px",
                          borderRadius:
                            "5px",
                        }}
                      >
                        ✎
                      </button>


                      {/* Delete */}

                      <button
                        type="button"
                        title="Delete conversation"
                        aria-label="Delete conversation"
                        onClick={(
                          event
                        ) => {
                          event.stopPropagation();

                          deleteConversation(
                            conversation
                          );
                        }}
                        style={{
                          border:
                            "none",
                          background:
                            "transparent",
                          color:
                            "inherit",
                          cursor:
                            "pointer",
                          padding:
                            "5px",
                          borderRadius:
                            "5px",
                        }}
                      >
                        ×
                      </button>

                    </div>

                  </div>
                )
              )
            )}

          </div>

        </div>


        {/* ----------------------------------------------------
            SIDEBAR BOTTOM
            ---------------------------------------------------- */}

        <div className="sidebar-bottom">

          {/* Backend status */}

          <div className="server-card">

            <span
              className={`status-dot ${
                serverStatus ===
                "connected"
                  ? "online"
                  : ""
              }`}
            />

            <div>

              <strong>
                {serverStatus ===
                "connected"
                  ? "System operational"
                  : serverStatus ===
                    "checking"
                  ? "Connecting..."
                  : "Backend disconnected"}
              </strong>

              <span>
                API connection status
              </span>

            </div>

          </div>


          {/* User profile */}

          <div className="profile-row">

            <div className="avatar">
              {currentUser.full_name
                ?.charAt(0)
                .toUpperCase() ||
                "U"}
            </div>


            <div className="profile-info">

              <strong>
                {
                  currentUser.full_name ||
                  "User"
                }
              </strong>

              <span>
                {currentUser.email}
              </span>

            </div>


            {/* Logout */}

            <button
              type="button"
              className="profile-menu"
              title="Logout"
              onClick={
                handleLogout
              }
              aria-label="Logout"
            >
              ↪
            </button>

          </div>

        </div>

      </aside>


      {/* ======================================================
          MAIN PANEL
          ====================================================== */}

      <main className="main-panel">

        {/* ----------------------------------------------------
            TOP BAR
            ---------------------------------------------------- */}

        <header className="topbar">

          <div className="topbar-left">

            <button
              className="menu-button"
              onClick={() =>
                setSidebarOpen(true)
              }
              aria-label="Open menu"
            >
              ☰
            </button>


            <div className="breadcrumb">

              <span>
                Workspace
              </span>

              <span className="breadcrumb-divider">
                /
              </span>

              <strong>
                AI Assistant
              </strong>

            </div>

          </div>


          <div className="topbar-right">

            <span className="model-badge">

              <span className="model-dot" />

              Gemini powered

            </span>


            <button
              className="icon-button"
              title="Check backend connection"
              onClick={
                checkBackend
              }
            >
              ↻
            </button>

          </div>

        </header>


        {/* ====================================================
            CHAT AREA
            ==================================================== */}

        <section className="chat-area">

          {messages.length === 0 ? (

            /* ------------------------------------------------
               WELCOME SCREEN
               ------------------------------------------------ */

            <div className="welcome-screen">

              <div className="welcome-icon">

                <svg
                  viewBox="0 0 48 48"
                  fill="none"
                  aria-hidden="true"
                >
                  <path
                    d="M24 4 29.5 18.5 44 24 29.5 29.5 24 44 18.5 29.5 4 24 18.5 18.5 24 4Z"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinejoin="round"
                  />

                  <path
                    d="m37 5 2 5 5 2-5 2-2 5-2-5-5-2 5-2 2-5Z"
                    fill="currentColor"
                  />
                </svg>

              </div>


              <span className="eyebrow">
                YOUR PERSONAL AI
                WORKSPACE
              </span>


              <h2>
                Knowledge at your
                fingertips.
              </h2>


              <p className="welcome-description">
                Upload your documents,
                ask questions, and get
                clear answers grounded
                in your own knowledge.
              </p>


              {/* Suggestions */}

              <div className="suggestion-grid">

                <button
                  className="suggestion-card"
                  onClick={() =>
                    setInput(
                      "Summarize the key information in my documents."
                    )
                  }
                >

                  <span className="suggestion-icon purple">
                    ▤
                  </span>

                  <strong>
                    Summarize documents
                  </strong>

                  <span>
                    Get the key points
                    from your files
                  </span>

                  <span className="suggestion-arrow">
                    ↗
                  </span>

                </button>


                <button
                  className="suggestion-card"
                  onClick={() =>
                    setInput(
                      "What are the most important concepts?"
                    )
                  }
                >

                  <span className="suggestion-icon blue">
                    ✧
                  </span>

                  <strong>
                    Explore key concepts
                  </strong>

                  <span>
                    Understand complex
                    topics simply
                  </span>

                  <span className="suggestion-arrow">
                    ↗
                  </span>

                </button>


                <button
                  className="suggestion-card"
                  onClick={() =>
                    setInput(
                      "Compare the important information across my files."
                    )
                  }
                >

                  <span className="suggestion-icon orange">
                    ⇄
                  </span>

                  <strong>
                    Compare information
                  </strong>

                  <span>
                    Find connections
                    across documents
                  </span>

                  <span className="suggestion-arrow">
                    ↗
                  </span>

                </button>


                <button
                  className="suggestion-card"
                  onClick={() =>
                    setInput(
                      "Create a list of important questions from my files."
                    )
                  }
                >

                  <span className="suggestion-icon green">
                    ✓
                  </span>

                  <strong>
                    Generate questions
                  </strong>

                  <span>
                    Turn your knowledge
                    into practice
                  </span>

                  <span className="suggestion-arrow">
                    ↗
                  </span>

                </button>

              </div>


              {/* Upload prompt */}

              <button
                className="upload-prompt"
                onClick={() =>
                  fileInputRef.current?.click()
                }
                disabled={uploading}
              >

                <span className="upload-prompt-icon">
                  ↑
                </span>

                <span>

                  <strong>
                    {uploading
                      ? "Uploading document..."
                      : "Start by uploading a document"}
                  </strong>

                  <small>
                    PDF, DOCX, or TXT
                    files
                  </small>

                </span>

                <span className="upload-prompt-arrow">
                  →
                </span>

              </button>

            </div>

          ) : (

            /* ------------------------------------------------
               MESSAGE LIST
               ------------------------------------------------ */

            <div className="message-list">

              {messages.map(
                (message) => {

                  const isUser =
                    message.role ===
                      "user" ||
                    message.role ===
                      "human";


                  return (
                    <article
                      key={
                        message.id
                      }
                      className={`message-row ${
                        isUser
                          ? "user-row"
                          : "assistant-row"
                      }`}
                    >

                      <div
                        className={`message-avatar ${
                          isUser
                            ? "user-avatar"
                            : ""
                        }`}
                      >

                        {isUser
                          ? currentUser.full_name
                              ?.charAt(
                                0
                              )
                              .toUpperCase() ||
                            "U"
                          : "✦"}

                      </div>


                      <div className="message-content">

                        <div className="message-author">

                          {isUser
                            ? "You"
                            : "Knowledge AI"}

                        </div>


                        <div className="message-text">

                          {
                            message.content ||
                            message.message ||
                            ""
                          }

                        </div>


                        {/* Sources */}

                        {!isUser &&
                          Array.isArray(
                            message.sources
                          ) &&
                          message.sources
                            .length >
                            0 && (

                            <div className="sources-box">

                              <strong>
                                Sources used
                              </strong>


                              {message.sources.map(
                                (
                                  source,
                                  index
                                ) => (

                                  <div
                                    className="source-item"
                                    key={
                                      source.chunk_id ||
                                      source.document_id ||
                                      index
                                    }
                                  >

                                    <span className="source-number">
                                      {index +
                                        1}
                                    </span>

                                    <span>

                                      {
                                        source.filename ||
                                        source.document_name ||
                                        source.name ||
                                        `Document ${
                                          source.document_id ||
                                          index +
                                            1
                                        }`
                                      }

                                    </span>

                                  </div>

                                )
                              )}

                            </div>

                          )}

                      </div>

                    </article>
                  );
                }
              )}


              {/* AI loading */}

              {loading && (

                <div className="message-row assistant-row">

                  <div className="message-avatar">
                    ✦
                  </div>


                  <div className="message-content">

                    <div className="message-author">
                      Knowledge AI
                    </div>


                    <div className="typing-indicator">

                      <span />
                      <span />
                      <span />

                      <small>
                        Thinking...
                      </small>

                    </div>

                  </div>

                </div>

              )}


              <div
                ref={messagesEndRef}
              />

            </div>

          )}

        </section>


        {/* ====================================================
            COMPOSER
            ==================================================== */}

        <div className="composer-area">

          {/* Error */}

          {error && (

            <div className="error-banner">

              <span>
                ⚠
              </span>

              {error}

              <button
                onClick={() =>
                  setError("")
                }
                aria-label="Dismiss error"
              >
                ×
              </button>

            </div>

          )}


          {/* Uploaded files */}

          {uploadedDocuments.length >
            0 && (

            <div className="uploaded-files">

              {uploadedDocuments
                .slice(0, 3)
                .map(
                  (document) => (

                    <span
                      className="file-chip"
                      key={
                        document.id
                      }
                    >
                      ▤{" "}
                      {
                        document.name
                      }
                    </span>

                  )
                )}

            </div>

          )}


          {/* Chat composer */}

          <form
            className="composer"
            onSubmit={sendMessage}
          >

            {/* Hidden file input */}

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt"
              hidden
              onChange={
                uploadDocument
              }
            />


            {/* Upload button */}

            <button
              type="button"
              className="attach-button"
              title="Upload document"
              onClick={() =>
                fileInputRef.current?.click()
              }
              disabled={uploading}
            >
              {uploading
                ? "…"
                : "+"}
            </button>


            {/* Message input */}

            <textarea
              value={input}
              onChange={(event) =>
                setInput(
                  event.target.value
                )
              }
              placeholder="Ask anything about your documents..."
              rows={1}
              onKeyDown={(event) => {

                if (
                  event.key ===
                    "Enter" &&
                  !event.shiftKey
                ) {
                  event.preventDefault();

                  sendMessage();
                }

              }}
            />


            {/* Send */}

            <button
              type="submit"
              className="send-button"
              disabled={
                !input.trim() ||
                loading
              }
              aria-label="Send message"
            >
              ↑
            </button>

          </form>


          {/* Footer */}

          <div className="composer-footer">

            <span>
              AI can make mistakes.
              Verify important
              information.
            </span>

            <span>
              Powered by RAG
              technology
            </span>

          </div>

        </div>

      </main>

    </div>
  );
}


export default App;