import React, { useState, useEffect, useRef } from 'react';
import api from '../api/axiosConfig';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Background3D from './Background3D';
import LoadingIndicator from './LoadingIndicator';
import FloatingActionButton from './FloatingActionButton';
import DocumentModal from './DocumentModal';
import { LogOut } from 'lucide-react';

const Dashboard = ({ user, onLogout }) => {
    const [inputText, setInputText] = useState('');
    const [aiMode, setAiMode] = useState('standard');
    const [contentType, setContentType] = useState('Explanation');
    const [isGenerating, setIsGenerating] = useState(false);
    const [isDocModalOpen, setIsDocModalOpen] = useState(false);
    const [documents, setDocuments] = useState([]);
    const [activeTab, setActiveTab] = useState('generator');
    const [chatMessages, setChatMessages] = useState(() => {
        const saved = localStorage.getItem('chatMessages');
        return saved ? JSON.parse(saved) : [];
    });
    const [typingId, setTypingId] = useState(null);
    const [displayContent, setDisplayContent] = useState({});

    useEffect(() => {
        localStorage.setItem('chatMessages', JSON.stringify(chatMessages));
    }, [chatMessages]);
    const [historyItems, setHistoryItems] = useState([]);
    const [adminStats, setAdminStats] = useState(null);

    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isRightBarOpen, setIsRightBarOpen] = useState(false);
    const [isActionMenuOpen, setIsActionMenuOpen] = useState(false);
    const [openCategories, setOpenCategories] = useState({
        educational: true,
        technical: false
    });

    const actionMenuItems = [
        { label: 'Telescope', icon: '🔭', mode: 'telescope' },
        { label: 'Deep Research', icon: '🔬', mode: 'deep' },
        { label: 'Thinking Mode', icon: '💡', mode: 'thinking' },
        { label: 'More', icon: '⋯', mode: 'more' }
    ];

    const toggleCategory = (cat) => {
        setOpenCategories(prev => ({
            ...prev,
            [cat]: !prev[cat]
        }));
    };

    const fetchHistory = async () => {
        try {
            const response = await api.get(`/api/history?user_id=${user.id || user.email}`);
            if (response.data.status === 'success') {
                setHistoryItems(response.data.history);
            }
        } catch (error) { console.error('Error fetching history:', error); }
    };

    const fetchDocuments = async () => {
        try {
            const response = await api.get(`/api/documents?user_id=${user.id || user.email}`);
            if (response.data.status === 'success') setDocuments(response.data.documents);
        } catch (error) { console.error('Error fetching documents:', error); }
    };

    useEffect(() => {
        if (user) {
            fetchHistory();
            fetchDocuments();
        }
    }, [user]);

    const fetchAdminStats = async () => {
        if (!user || user.email.toLowerCase() !== 'admin@gmail.com') {
            console.log("Access denied: Not admin email", user?.email);
            return;
        }
        try {
            console.log("Fetching admin stats for:", user.email);
            const response = await api.get(`/api/admin/stats?admin_email=${user.email}`);
            console.log("Admin stats response:", response.data);
            setAdminStats(response.data.daily_logins || []);
        } catch (error) {
            console.error('Error fetching admin stats:', error);
            setAdminStats([]); // Fallback to empty array to show at least the container/error state
        }
    };

    useEffect(() => {
        if (user && user.email.toLowerCase() === 'admin@gmail.com') {
            fetchAdminStats();
        }
    }, [user]);

    // Auto-scroll to bottom of response
    useEffect(() => {
        if (chatMessages.length > 0 || isGenerating) {
            const scrollArea = document.querySelector('.response-scroll-area');
            if (scrollArea) {
                // Use a small delay to ensure the DOM has updated and images/content are rendered
                const timeoutId = setTimeout(() => {
                    scrollArea.scrollTo({ top: scrollArea.scrollHeight, behavior: 'smooth' });
                }, 100);
                return () => clearTimeout(timeoutId);
            }
        }
    }, [chatMessages, isGenerating]);



    const handleGenerate = async (e) => {
        e.preventDefault();
        if (!inputText.trim() || isGenerating) return;

        const currentInput = inputText;
        const currentType = contentType;

        // Add user message to chat
        const userMsg = { id: Date.now(), type: 'user', content: currentInput };
        setChatMessages(prev => [...prev, userMsg]);
        setInputText(''); // Clear input immediately for better UX
        setIsGenerating(true);

        try {
            setIsGenerating(true);
            const response = await api.post('/api/generate', {
                topic: currentInput,
                content_type: currentType,
                user_id: user.id || user.email,
                mode: aiMode
            });

            if (response.data.content) {
                const aiMsgId = Date.now() + 1;
                const aiMsg = {
                    id: aiMsgId,
                    type: 'ai',
                    content: response.data.content,
                    contentType: currentType,
                    topic: currentInput
                };
                setChatMessages(prev => [...prev, aiMsg]);

                // Start Typing Effect
                setTypingId(aiMsgId);
                let fullText = response.data.content;
                let currentText = "";
                let index = 0;

                const typeInterval = setInterval(() => {
                    if (index < fullText.length) {
                        currentText += fullText[index];
                        setDisplayContent(prev => ({ ...prev, [aiMsgId]: currentText }));
                        index++;
                    } else {
                        clearInterval(typeInterval);
                        setTypingId(null);
                    }
                }, 5); // Fast typing speed

                fetchHistory(); // Refresh history
            }

        } catch (error) {
            console.error('Generation error:', error);
            const errorData = error.response?.data;
            let errorMsg = errorData?.error || error.message || "Failed to generate content";

            // Special handling for history full error
            if (errorData?.history_full) {
                errorMsg = "⚠️ Your history is full! Please go to the History tab and click 'Clear All' to continue generating.";
            }

            const errAiMsg = { id: Date.now() + 1, type: 'error', content: `❌ ${errorMsg}` };
            setChatMessages(prev => [...prev, errAiMsg]);
        } finally {
            setIsGenerating(false);
        }
    };


    const aboutFeatures = [
        { title: "AI-Powered", description: "Harness cutting-edge artificial intelligence to generate high-quality content in seconds", icon: "🤖" },
        { title: "Lightning Fast", description: "Get instant results without waiting. Our optimized algorithms deliver speed you can count on", icon: "⚡" },
        { title: "Analytics", description: "Track your usage, monitor trends, and optimize your content generation strategy", icon: "📊" },
        { title: "Secure", description: "Your data is encrypted and protected with enterprise-grade security measures", icon: "🔒" },
        { title: "Premium Quality", description: "Every piece of content is crafted with attention to detail and quality standards", icon: "💎" },
        { title: "Always Evolving", description: "We continuously improve our AI models to deliver better results every day", icon: "🚀" }
    ];

    const handleSaveDocument = async (docData) => {
        try {
            const response = await api.post('/api/documents', {
                ...docData,
                user_id: user.id || user.email
            });
            if (response.data.status === 'success') {
                fetchDocuments(); // Refresh the documents list
                setIsDocModalOpen(false);
            }
        } catch (error) {
            console.error('Error saving document:', error);
            alert('Failed to save document. Please try again.');
        }
    };

    return (
        <div className="dashboard-container">
            <Background3D />

            {/* Mobile Navbar */}
            <div className="mobile-navbar">
                <button className="mobile-menu-btn" onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
                    ☰
                </button>
                <div className="brand mobile-brand">
                    <img src="/bg.png" alt="EduWrite" className="mobile-logo" />
                    <span className="brand-text">EduWrite AI</span>
                </div>
                <div className="mobile-nav-right">
                    <button className="mobile-menu-btn logout-mobile-btn" onClick={onLogout} title="Logout">
                        <LogOut size={20} />
                    </button>
                    <button className="mobile-menu-btn" onClick={() => setIsRightBarOpen(!isRightBarOpen)}>
                        ⚙️
                    </button>
                </div>
            </div>

            {/* Mobile Navigation Tabs */}
            <div className="mobile-nav-tabs">
                <button
                    className={`mobile-tab ${activeTab === 'generator' ? 'active' : ''}`}
                    onClick={() => setActiveTab('generator')}
                >
                    Generator
                </button>
                <button
                    className={`mobile-tab ${activeTab === 'history' ? 'active' : ''}`}
                    onClick={() => setActiveTab('history')}
                >
                    History
                </button>
                <button
                    className={`mobile-tab ${activeTab === 'activity' ? 'active' : ''}`}
                    onClick={() => setActiveTab('activity')}
                >
                    Activity
                </button>
                <button
                    className={`mobile-tab ${activeTab === 'about' ? 'active' : ''}`}
                    onClick={() => setActiveTab('about')}
                >
                    About
                </button>
            </div>

            {/* Desktop Navbar */}
            <nav className="navbar desktop-only">
                <div className="nav-left">
                    <div className="brand">
                        <img src="/bg.png" alt="EduWrite" className="nav-logo" />
                        <h1 className="brand-name">EduWrite AI <span className="pro-badge">PRO</span></h1>
                    </div>
                </div>

                <div className="nav-center">
                    <div className="nav-links">
                        <button className={`nav-item ${activeTab === 'generator' ? 'active' : ''}`} onClick={() => setActiveTab('generator')}>Generator</button>
                        <button className={`nav-item ${activeTab === 'history' ? 'active' : ''}`} onClick={() => setActiveTab('history')}>History</button>
                        <button className={`nav-item ${activeTab === 'activity' ? 'active' : ''}`} onClick={() => setActiveTab('activity')}>Activity</button>
                        <button className={`nav-item ${activeTab === 'about' ? 'active' : ''}`} onClick={() => setActiveTab('about')}>About</button>
                    </div>
                </div>

                <div className="nav-right">
                    <button className="logout-button" onClick={onLogout}>
                        <span className="logout-icon">🚪</span>
                        Logout
                    </button>
                </div>
            </nav>

            {/* Left Sidebar */}
            <aside className={`sidebar left-sidebar ${isSidebarOpen ? 'mobile-open' : ''}`}>
                <button className="new-chat-btn" onClick={() => { setActiveTab('generator'); setIsSidebarOpen(false); setChatMessages([]); localStorage.removeItem('chatMessages'); setInputText(''); }}>
                    New Chat
                </button>

                <div className="chat-history-container">
                    <h3 className="sidebar-label">Chat History</h3>
                    <div className="chat-history">
                        {historyItems.length > 0 ? historyItems.map((item) => (
                            <div key={item.id} className={`history-item ${chatMessages[0]?.id === `user-${item.id}` ? 'active' : ''}`} onClick={() => {
                                setChatMessages([
                                    { id: `user-${item.id}`, type: 'user', content: item.topic },
                                    { id: `ai-${item.id}`, type: 'ai', content: item.response, topic: item.topic, contentType: item.content_type }
                                ]);
                                setIsSidebarOpen(false);
                                setActiveTab('generator');
                            }}>
                                <span className="icon">📜</span>
                                <span className="history-text">{item.topic || item.title}</span>
                            </div>
                        )) : (
                            <div className="history-item empty">No history yet</div>
                        )}
                    </div>
                </div>

            </aside>

            {/* Main Content */}
            < main className="main-content" onClick={() => { setIsSidebarOpen(false); setIsRightBarOpen(false); }}>
                <div className="tab-content-wrapper">
                    {activeTab === 'generator' ? (
                        <div className="generator-container">
                            <div className="response-scroll-area">
                                {chatMessages.length === 0 ? (
                                    <div className="welcome-center">
                                        <h2>Welcome, <span>{user.name || user.email.split('@')[0]}</span></h2>
                                        <p>Ask anything to generate <span className="cyan-text">{contentType}</span> with AI</p>
                                        <div className="suggestion-chips">
                                            {['Write a short story', 'Solve a math problem', 'Explain Quantum Physics', 'Create a study plan'].map(suggestion => (
                                                <button key={suggestion} className="suggestion-chip" onClick={() => { setInputText(suggestion); }}>
                                                    {suggestion}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                ) : (
                                    <div className="chat-sequence">
                                        {chatMessages.map((msg) => (
                                            <div key={msg.id} className={`message-item ${msg.type}`}>
                                                {msg.type === 'user' ? (
                                                    <div className="user-query-bubble">
                                                        <span className="user-icon">👤</span>
                                                        <p>{msg.content}</p>
                                                    </div>
                                                ) : msg.type === 'error' ? (
                                                    <div className="error-display">{msg.content}</div>
                                                ) : (
                                                    <div className="ai-message-wrapper">
                                                        <div className="ai-avatar-circle">🤖</div>
                                                        <div className="response-display chat-ai-response">
                                                            <div className="response-header">
                                                                <span className="type-badge">{msg.contentType}</span>
                                                                <h3 className="topic-title">{msg.topic}</h3>
                                                            </div>
                                                            <div className="response-body markdown-content">
                                                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                                    {displayContent[msg.id] || msg.content}
                                                                </ReactMarkdown>
                                                                {typingId === msg.id && <span className="typing-cursor">|</span>}
                                                            </div>
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                        {isGenerating && (
                                            <div className="ai-loading-indicator">
                                                <LoadingIndicator size={120} />
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : activeTab === 'history' ? (
                        <div className="response-scroll-area">
                            <div className="section-header-flex">
                                <h2 className="section-title">Generation History</h2>
                                {historyItems.length > 0 && (
                                    <button className="clear-btn" onClick={async () => {
                                        try {
                                            await api.post('/api/history/clear', { user_id: user.id || user.email });
                                        } catch (e) { console.error('Error clearing history:', e); }
                                        setChatMessages([]);
                                        setHistoryItems([]);
                                        localStorage.removeItem('chatMessages');
                                    }}>Clear All</button>
                                )}
                            </div>
                            {historyItems.length > 0 ? (
                                <div className="history-grid">
                                    {historyItems.map((item) => (
                                        <div key={item.id} className="history-card" onClick={() => {
                                            setChatMessages([
                                                { id: `user-${item.id}`, type: 'user', content: item.topic },
                                                { id: `ai-${item.id}`, type: 'ai', content: item.response, topic: item.topic, contentType: item.content_type }
                                            ]);
                                            setActiveTab('generator');
                                        }}>
                                            <div className="history-card-header">
                                                <span className="type-badge">{item.content_type}</span>
                                                <span className="history-card-date">{new Date(item.created_at).toLocaleDateString()}</span>
                                            </div>
                                            <div className="history-card-topic">{item.topic}</div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="empty-state">
                                    <span>📊</span>
                                    <p>Your history is empty. Start generating!</p>
                                </div>
                            )}
                        </div>
                    ) : activeTab === 'activity' ? (
                        <div className="response-scroll-area">
                            <h2 className="section-title">Your Activity</h2>
                            <div className="activity-stats">
                                <div className="stat-card">
                                    <div className="stat-value">{historyItems.length}</div>
                                    <div className="stat-label">Total Generations</div>
                                </div>
                                {user.email.toLowerCase() === 'admin@gmail.com' && (
                                    <div className="admin-stats-container">
                                        <div className="admin-header">
                                            <h3 className="admin-stats-title">Daily User Logins</h3>
                                            <button onClick={fetchAdminStats} className="refresh-btn">🔄 Refresh</button>
                                        </div>
                                        {adminStats && adminStats.length > 0 ? (
                                            <div className="admin-stats-list">
                                                {adminStats.map((stat, idx) => (
                                                    <div key={idx} className="admin-stat-row">
                                                        <span className="stat-day">{new Date(stat.day).toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}</span>
                                                        <span className="stat-count">{stat.count} accounts</span>
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <p className="loading-text">{adminStats ? "No records found." : "Loading admin statistics..."}</p>
                                        )}
                                    </div>
                                )}
                                <div className="stat-card">
                                    <div className="stat-value">Active</div>
                                    <div className="stat-label">Account Status</div>
                                </div>
                            </div>
                        </div>
                    ) : activeTab === 'about' ? (
                        <div className="about-container">
                            <div className="about-header">
                                <h2 className="greeting-text">Hello, <span className="cyan-text">{user.name || user.email.split('@')[0]}!</span></h2>
                                <h1>About <span className="cyan-text">Edu Write</span></h1>
                                <p className="tagline">Transforming Education with <span className="purple-text">Intelligent Content Generation</span></p>
                            </div>
                            <div className="about-content">
                                <h2 className="section-title">Why Choose Edu Write?</h2>
                                <div className="features-grid">
                                    {aboutFeatures.map((feature, index) => (
                                        <div key={index} className="feature-card">
                                            <div className="feature-icon">{feature.icon}</div>
                                            <div className="feature-info"><h3>{feature.title}</h3><p>{feature.description}</p></div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    ) : null}
                </div>

                {
                    activeTab !== 'about' && (
                        <div className="input-section-bottom">
                            <div className="input-container">
                                <form onSubmit={handleGenerate} className="chat-input-wrapper" style={{ position: 'relative' }}>
                                    <div className="input-action-container">
                                        <button
                                            type="button"
                                            className={`input-action-btn ${isActionMenuOpen ? 'active' : ''}`}
                                            onClick={() => setIsActionMenuOpen(!isActionMenuOpen)}
                                        >
                                            <span className="plus-icon">+</span>
                                        </button>

                                        {isActionMenuOpen && (
                                            <div className="input-action-menu">
                                                {actionMenuItems.map((item, idx) => (
                                                    <div
                                                        key={idx}
                                                        className={`action-menu-item ${aiMode === item.mode ? 'active' : ''}`}
                                                        onClick={() => {
                                                            if (item.mode !== 'more') {
                                                                setAiMode(item.mode);
                                                            }
                                                            setIsActionMenuOpen(false);
                                                        }}
                                                    >
                                                        <span className="action-icon">{item.icon}</span>
                                                        <span className="action-label">{item.label}</span>
                                                        {aiMode === item.mode && item.mode !== 'upload' && <span className="active-dot"></span>}
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                    <input
                                        type="text"
                                        className="chat-input"
                                        placeholder={`Ask about something for ${contentType}...`}
                                        value={inputText}
                                        onChange={(e) => setInputText(e.target.value)}
                                        disabled={isGenerating}
                                    />
                                    <button type="submit" className="send-btn" disabled={isGenerating || !inputText.trim()}>
                                        {isGenerating ? <div className="loader-small"></div> : <span className="send-icon">→</span>}
                                    </button>
                                </form>
                            </div>
                        </div>
                    )
                }
            </main >

            {/* Right Sidebar */}
            < aside className={`right-bar ${isRightBarOpen ? 'open' : ''}`}>
                <div className="sidebar-section">
                    <h3 className="sidebar-label">CONTENT TYPES</h3>
                    <div className="category-wrapper">
                        <div className="category-header smaller" onClick={() => toggleCategory('educational')}>
                            <span>Educational</span><span className={`chevron ${openCategories.educational ? 'open' : ''}`}>▼</span>
                        </div>
                        <div className="category-content" style={{ maxHeight: openCategories.educational ? '500px' : '0' }}>
                            {['Explanation', 'Summary', 'Quiz', 'Interactive Lesson', 'Mind Map'].map(type => (
                                <div key={type} className={`content-type-item ${contentType === type ? 'active' : ''}`} onClick={() => { setContentType(type); setActiveTab('generator'); setIsRightBarOpen(false); }}>
                                    <span className="dot"></span>
                                    {type}
                                </div>
                            ))}
                        </div>
                    </div>
                    <div className="category-wrapper">
                        <div className="category-header smaller" onClick={() => toggleCategory('technical')}>
                            <span>Technical</span><span className={`chevron ${openCategories.technical ? 'open' : ''}`}>▼</span>
                        </div>
                        <div className="category-content" style={{ maxHeight: openCategories.technical ? '500px' : '0' }}>
                            {['Coding', 'Research Paper'].map(type => (
                                <div key={type} className={`content-type-item ${contentType === type ? 'active' : ''}`} onClick={() => { setContentType(type); setActiveTab('generator'); setIsRightBarOpen(false); }}>
                                    <span className="dot"></span>
                                    {type}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </aside >

            {(isSidebarOpen || isRightBarOpen) && <div className="mobile-overlay" onClick={() => { setIsSidebarOpen(false); setIsRightBarOpen(false); }}></div>}

            <DocumentModal
                isOpen={isDocModalOpen}
                onClose={() => setIsDocModalOpen(false)}
                onSave={handleSaveDocument}
            />
        </div >
    );
};

export default Dashboard;
