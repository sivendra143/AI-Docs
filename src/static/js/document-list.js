// document-list.js: Fetch and show uploaded document names as a system message on chat load

document.addEventListener('DOMContentLoaded', async function() {
    // Only run on chat page
    if (!document.getElementById('chat-messages')) return;

    // Helper to update selected documents globally
    window.selectedDocuments = [];

    // Create the card UI
    function createDocumentSelectCard(documents) {
        const card = document.createElement('div');
        card.className = 'system-doc-select-card';
        card.innerHTML = `
            <div class="doc-select-header"><b>📄 Select documents to chat about:</b></div>
            <div class="doc-select-list"></div>
            <div class="doc-select-footer">
                <label><input type="checkbox" id="select-all-docs"> <span style="font-weight:500">Select All</span></label>
                <span class="doc-select-count">Selected: 0</span>
            </div>
        `;
        return card;
    }

    function updateSelectedCount(card, count) {
        card.querySelector('.doc-select-count').textContent = `Selected: ${count}`;
    }

    try {
        const resp = await fetch('/api/refresh', { method: 'GET' });
        const data = await resp.json();
        if (data && data.documents && data.documents.length > 0) {
            const chatMessages = document.getElementById('chat-messages');
            const card = createDocumentSelectCard(data.documents);
            const listDiv = card.querySelector('.doc-select-list');
            data.documents.forEach((doc, idx) => {
                const id = `doc-cb-${idx}`;
                const label = document.createElement('label');
                label.className = 'doc-cb-label';
                label.innerHTML = `<input type="checkbox" class="doc-cb" value="${doc}" id="${id}"> <span>${doc}</span>`;
                listDiv.appendChild(label);
            });
            chatMessages.insertBefore(card, chatMessages.firstChild);

            // Create preview element
            const previewTooltip = document.createElement('div');
            previewTooltip.className = 'doc-preview';
            previewTooltip.innerHTML = '<div class="preview-content"></div>';
            document.body.appendChild(previewTooltip);

            // Add hover events to document labels
            document.querySelectorAll('.doc-cb-label').forEach(label => {
              label.addEventListener('mouseenter', function(e) {
                const docName = this.querySelector('.doc-cb').value;
                fetch(`/api/document/preview/${encodeURIComponent(docName)}`)
                  .then(res => res.json())
                  .then(data => {
                    if (data.preview) {
                      previewTooltip.querySelector('.preview-content').textContent = data.preview;
                      positionPreview(e.clientX, e.clientY);
                      previewTooltip.style.opacity = '1';
                    }
                  });
              });

              label.addEventListener('mouseleave', () => {
                previewTooltip.style.opacity = '0';
              });

              label.addEventListener('mousemove', (e) => {
                positionPreview(e.clientX, e.clientY);
              });
            });

            function positionPreview(x, y) {
              previewTooltip.style.left = (x + 15) + 'px';
              previewTooltip.style.top = (y - 15) + 'px';
            }

            // Checkbox logic
            const checkboxes = card.querySelectorAll('.doc-cb');
            const selectAll = card.querySelector('#select-all-docs');
            function syncSelected() {
                window.selectedDocuments = Array.from(checkboxes).filter(cb => cb.checked).map(cb => cb.value);
                updateSelectedCount(card, window.selectedDocuments.length);
                selectAll.checked = window.selectedDocuments.length === checkboxes.length;
            }
            checkboxes.forEach(cb => {
                cb.addEventListener('change', syncSelected);
            });
            selectAll.addEventListener('change', function() {
                checkboxes.forEach(cb => { cb.checked = selectAll.checked; });
                syncSelected();
            });
        } else {
            if (window.addSystemMessage) {
                window.addSystemMessage('No documents uploaded yet.');
            }
        }
    } catch (err) {
        if (window.addSystemMessage) {
            window.addSystemMessage('Could not load document list.');
        }
    }
});

// Modern styles for doc selection card
const style = document.createElement('style');
style.innerHTML = `
.system-doc-select-card {
    background: linear-gradient(90deg, #f7fafc 60%, #e3f2fd 100%);
    border-radius: 1rem;
    box-shadow: 0 2px 8px #1976d222;
    padding: 1.2rem 1.5rem 1rem 1.5rem;
    margin-bottom: 1.2rem;
    border-left: 5px solid #1976d2;
    color: #222;
    font-size: 1.08em;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
}
[data-theme="dark"] .system-doc-select-card {
    background: linear-gradient(90deg, #23272e 60%, #283593 100%);
    color: #f3f6fa;
    border-left: 5px solid #90caf9;
}
.doc-select-header {
    font-size: 1.1em;
    margin-bottom: 0.7em;
}
.doc-select-list {
    display: flex;
    flex-wrap: wrap;
    gap: 0.7em 1.2em;
    margin-bottom: 0.7em;
}
.doc-cb-label {
    display: flex;
    align-items: center;
    gap: 0.3em;
    font-size: 1em;
    background: rgba(25, 118, 210, 0.06);
    border-radius: 0.4em;
    padding: 0.25em 0.7em;
    cursor: pointer;
    user-select: none;
    transition: background 0.2s;
}
[data-theme="dark"] .doc-cb-label {
    background: rgba(144, 202, 249, 0.13);
}
.doc-cb-label input[type="checkbox"] {
    accent-color: #1976d2;
    width: 1.05em;
    height: 1.05em;
    margin-right: 0.3em;
}
.doc-select-footer {
    display: flex;
    align-items: center;
    gap: 1.5em;
    margin-top: 0.4em;
    font-size: 0.98em;
}
.doc-select-count {
    color: #1976d2;
    font-weight: 500;
}
[data-theme="dark"] .doc-select-count {
    color: #90caf9;
}
.doc-preview {
  position: absolute;
  background-color: #fff;
  border: 1px solid #ddd;
  padding: 10px;
  border-radius: 5px;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
  opacity: 0;
  transition: opacity 0.2s;
}
[data-theme="dark"] .doc-preview {
  background-color: #333;
  border: 1px solid #555;
  color: #fff;
}
`;
document.head.appendChild(style);
