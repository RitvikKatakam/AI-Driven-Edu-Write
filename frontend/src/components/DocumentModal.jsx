import React, { useState } from 'react';
import './DocumentModal.css';

const DocumentModal = ({ isOpen, onClose, onSave }) => {
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [isSaving, setIsSaving] = useState(false);

    if (!isOpen) return null;

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!title.trim() || !content.trim() || isSaving) return;

        setIsSaving(true);
        try {
            await onSave({ title, content });
            setTitle('');
            setContent('');
            onClose();
        } catch (error) {
            console.error('Failed to save document:', error);
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>Create New Document</h2>
                    <button className="close-btn" onClick={onClose}>✕</button>
                </div>
                <form onSubmit={handleSubmit} className="modal-form">
                    <div className="input-group">
                        <label>Document Title</label>
                        <input
                            type="text"
                            placeholder="Enter title..."
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            required
                        />
                    </div>
                    <div className="input-group">
                        <label>Content</label>
                        <textarea
                            placeholder="Start writing..."
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                            required
                        ></textarea>
                    </div>
                    <div className="modal-actions">
                        <button type="button" className="cancel-btn" onClick={onClose}>Cancel</button>
                        <button type="submit" className="save-btn" disabled={isSaving}>
                            {isSaving ? 'Saving...' : 'Save Document'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default DocumentModal;
