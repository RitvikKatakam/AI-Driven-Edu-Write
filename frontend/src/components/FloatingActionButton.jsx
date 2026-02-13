import React from 'react';
import './FloatingActionButton.css';

const FloatingActionButton = ({ onClick }) => {
    return (
        <button
            className="floating-action-button"
            onClick={onClick}
            title="Create New Document"
            aria-label="Create New Document"
        >
            New Doc
        </button>
    );
};

export default FloatingActionButton;
