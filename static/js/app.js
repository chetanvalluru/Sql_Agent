// Chat with DB - Frontend JavaScript
class ChatWithDB {
    constructor() {
        this.queryForm = document.getElementById('query-form');
        this.queryInput = document.getElementById('query-input');
        this.sendButton = document.getElementById('send-button');
        this.chatMessages = document.getElementById('chat-messages');
        this.resultsContainer = document.getElementById('results-container');
        this.sqlDisplay = document.getElementById('sql-display');
        this.resultsTable = document.getElementById('results-table');
        this.resultCount = document.getElementById('result-count');
        this.copySqlButton = document.getElementById('copy-sql');
        
        // Database explorer elements
        this.refreshDbButton = document.getElementById('refresh-db');
        this.schemaDisplay = document.getElementById('schema-display');
        this.sampleDataDisplay = document.getElementById('sample-data-display');
        this.tabButtons = document.querySelectorAll('.tab-button');
        this.tabContents = document.querySelectorAll('.tab-content');
        
        // Navigation elements
        this.navItems = document.querySelectorAll('.nav-item');
        this.views = document.querySelectorAll('.view');
        this.currentView = 'chat';
        
        this.initializeEventListeners();
        this.loadDatabaseInfo();
    }
    
    initializeEventListeners() {
        // Form submission
        this.queryForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleQuery();
        });
        
        // Enter key in input
        this.queryInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleQuery();
            }
        });
        
        // Copy SQL button
        this.copySqlButton.addEventListener('click', () => {
            this.copyToClipboard(this.sqlDisplay.textContent);
        });
        
        // Database explorer events
        this.refreshDbButton.addEventListener('click', () => {
            this.loadDatabaseInfo();
        });
        
        // Tab switching
        this.tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                this.switchTab(e.target.dataset.tab);
            });
        });
        
        // Navigation switching
        this.navItems.forEach(navItem => {
            navItem.addEventListener('click', (e) => {
                const viewName = e.currentTarget.dataset.view;
                this.switchView(viewName);
            });
        });
    }
    
    async handleQuery() {
        const query = this.queryInput.value.trim();
        if (!query) return;
        
        // Add user message to chat
        this.addMessage(query, 'user');
        
        // Clear input and disable button
        this.queryInput.value = '';
        this.setLoadingState(true);
        
        try {
            // Send query to backend
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query })
            });
            
            const data = await response.json();
            
            if (data.error) {
                this.addMessage(`❌ Error: ${data.error}`, 'system');
            } else {
                // Add results directly to chat
                this.addResultsMessage(data.sql, data.results);
            }
            
        } catch (error) {
            console.error('Error:', error);
            this.addMessage('❌ Network error. Please try again.', 'system');
        } finally {
            this.setLoadingState(false);
        }
    }
    
    addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (type === 'user') {
            messageContent.textContent = content;
        } else {
            messageContent.innerHTML = content;
        }
        
        messageDiv.appendChild(messageContent);
        this.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom with smooth animation
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 50);
    }
    
    addResultsMessage(sql, results) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message system results-message';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Create results content
        let content = '<div class="results-content">';
        
        // Add success indicator and row count
        const rowCount = results ? results.length : 0;
        content += `<div class="results-header">`;
        content += `<span class="success-indicator">Query executed successfully</span>`;
        content += `<span class="row-count">${rowCount} row(s) returned</span>`;
        content += `</div>`;
        
        // Add collapsible SQL section
        content += `<div class="sql-section">`;
        content += `<button class="sql-toggle" onclick="this.parentElement.classList.toggle('expanded')">`;
        content += `<span class="toggle-text">Show SQL</span> <span class="toggle-icon">▶</span>`;
        content += `</button>`;
        content += `<pre class="sql-code">${sql}</pre>`;
        content += `<button class="copy-sql-btn" data-sql="${sql.replace(/"/g, '&quot;').replace(/'/g, '&#39;')}">Copy</button>`;
        content += `</div>`;
        
        // Add results table
        if (results && results.length > 0) {
            content += '<div class="results-table-container">';
            content += this.formatResultsTable(results);
            content += '</div>';
        } else {
            content += '<div class="no-results">No results returned</div>';
        }
        
        content += '</div>';
        
        messageContent.innerHTML = content;
        messageDiv.appendChild(messageContent);
        this.chatMessages.appendChild(messageDiv);
        
        // Add event listener for copy SQL button in this message
        const copySqlBtn = messageDiv.querySelector('.copy-sql-btn');
        if (copySqlBtn) {
            copySqlBtn.addEventListener('click', () => {
                const sqlText = copySqlBtn.getAttribute('data-sql');
                this.copyToClipboard(sqlText, copySqlBtn);
            });
        }
        
        // Scroll to bottom with smooth animation
        setTimeout(() => {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }, 50);
    }
    
    formatResultsTable(results) {
        if (!results || results.length === 0) return '';
        
        let html = '<table class="chat-results-table">';
        
        // Create header
        const columns = Object.keys(results[0]);
        html += '<thead><tr>';
        columns.forEach(column => {
            html += `<th>${column}</th>`;
        });
        html += '</tr></thead>';
        
        // Create body - limit to first 10 rows for chat display
        html += '<tbody>';
        const displayRows = results.slice(0, 10);
        displayRows.forEach(row => {
            html += '<tr>';
            columns.forEach(column => {
                const value = row[column] !== null ? row[column] : 'NULL';
                html += `<td>${value}</td>`;
            });
            html += '</tr>';
        });
        html += '</tbody></table>';
        
        // Add "show more" indicator if there are more than 10 rows
        if (results.length > 10) {
            html += `<div class="show-more-indicator">... and ${results.length - 10} more rows</div>`;
        }
        
        return html;
    }
    
    displayResults(sql, results) {
        // Show results container
        this.resultsContainer.style.display = 'block';
        
        // Display SQL
        this.sqlDisplay.textContent = sql;
        
        // Display results table
        if (results && results.length > 0) {
            this.createResultsTable(results);
            this.resultCount.textContent = `${results.length} row(s) returned`;
        } else {
            this.resultsTable.innerHTML = '<p>No results returned</p>';
            this.resultCount.textContent = '0 rows returned';
        }
        
        // Scroll to results smoothly
        setTimeout(() => {
            this.resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    }
    
    createResultsTable(results) {
        if (!results || results.length === 0) return;
        
        const table = document.createElement('table');
        
        // Create header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        
        const columns = Object.keys(results[0]);
        columns.forEach(column => {
            const th = document.createElement('th');
            th.textContent = column;
            headerRow.appendChild(th);
        });
        
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Create body
        const tbody = document.createElement('tbody');
        results.forEach(row => {
            const tr = document.createElement('tr');
            columns.forEach(column => {
                const td = document.createElement('td');
                td.textContent = row[column] !== null ? row[column] : 'NULL';
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
        
        table.appendChild(tbody);
        
        // Clear and add table
        this.resultsTable.innerHTML = '';
        this.resultsTable.appendChild(table);
    }
    
    setLoadingState(loading) {
        const sendIcon = this.sendButton.querySelector('.send-icon');
        const spinner = this.sendButton.querySelector('.loading-spinner');
        
        if (loading) {
            sendIcon.style.display = 'none';
            spinner.style.display = 'flex';
            this.sendButton.disabled = true;
            this.queryInput.disabled = true;
        } else {
            sendIcon.style.display = 'flex';
            spinner.style.display = 'none';
            this.sendButton.disabled = false;
            this.queryInput.disabled = false;
        }
    }
    
    async copyToClipboard(text, button = null) {
        try {
            await navigator.clipboard.writeText(text);
            
            // Show feedback on the specific button if provided, otherwise use the main copy button
            const targetButton = button || this.copySqlButton;
            if (targetButton) {
                const originalText = targetButton.textContent;
                targetButton.textContent = 'Copied!';
                targetButton.style.background = '#28a745';
                
                setTimeout(() => {
                    targetButton.textContent = originalText;
                    targetButton.style.background = '#28a745';
                }, 2000);
            }
            
        } catch (err) {
            console.error('Failed to copy: ', err);
            
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            
            // Show feedback on the specific button if provided, otherwise use the main copy button
            const targetButton = button || this.copySqlButton;
            if (targetButton) {
                const originalText = targetButton.textContent;
                targetButton.textContent = 'Copied!';
                setTimeout(() => {
                    targetButton.textContent = originalText;
                }, 2000);
            }
        }
    }
    
    async loadDatabaseInfo() {
        try {
            // Load schema
            const schemaResponse = await fetch('/api/schema');
            const schemaData = await schemaResponse.json();
            this.displaySchema(schemaData.schema);
            
            // Load sample data
            const sampleResponse = await fetch('/api/sample-data');
            const sampleData = await sampleResponse.json();
            this.displaySampleData(sampleData.sample_data);
            
        } catch (error) {
            console.error('Error loading database info:', error);
            this.schemaDisplay.innerHTML = '<div class="error">Failed to load schema</div>';
            this.sampleDataDisplay.innerHTML = '<div class="error">Failed to load sample data</div>';
        }
    }
    
    displaySchema(schema) {
        if (!schema || Object.keys(schema).length === 0) {
            this.schemaDisplay.innerHTML = '<div class="error">No schema information available</div>';
            return;
        }
        
        let html = '';
        for (const [tableName, columns] of Object.entries(schema)) {
            html += `<div class="schema-table">`;
            html += `<h5>Table: ${tableName}</h5>`;
            html += `<table>`;
            html += `<thead><tr><th>Column</th><th>Type</th><th>Nullable</th><th>Key</th></tr></thead>`;
            html += `<tbody>`;
            
            columns.forEach(col => {
                html += `<tr>`;
                html += `<td>${col.column}</td>`;
                html += `<td>${col.type}</td>`;
                html += `<td>${col.nullable}</td>`;
                html += `<td>${col.key || '-'}</td>`;
                html += `</tr>`;
            });
            
            html += `</tbody></table></div>`;
        }
        
        this.schemaDisplay.innerHTML = html;
    }
    
    displaySampleData(sampleData) {
        if (!sampleData || Object.keys(sampleData).length === 0) {
            this.sampleDataDisplay.innerHTML = '<div class="error">No sample data available</div>';
            return;
        }
        
        let html = '';
        for (const [tableName, rows] of Object.entries(sampleData)) {
            if (rows.length === 0) continue;
            
            html += `<div class="sample-data-table">`;
            html += `<h5>Table: ${tableName} (${rows.length} rows)</h5>`;
            html += `<table>`;
            
            // Create header
            const columns = Object.keys(rows[0]);
            html += `<thead><tr>`;
            columns.forEach(col => {
                html += `<th>${col}</th>`;
            });
            html += `</tr></thead>`;
            
            // Create body
            html += `<tbody>`;
            rows.forEach(row => {
                html += `<tr>`;
                columns.forEach(col => {
                    html += `<td>${row[col] !== null ? row[col] : 'NULL'}</td>`;
                });
                html += `</tr>`;
            });
            html += `</tbody></table></div>`;
        }
        
        this.sampleDataDisplay.innerHTML = html;
    }
    
    switchTab(tabName) {
        // Update tab buttons
        this.tabButtons.forEach(button => {
            button.classList.toggle('active', button.dataset.tab === tabName);
        });
        
        // Update tab content
        this.tabContents.forEach(content => {
            content.classList.toggle('active', content.id === `${tabName}-tab`);
        });
    }
    
    switchView(viewName) {
        // Update navigation items
        this.navItems.forEach(navItem => {
            navItem.classList.toggle('active', navItem.dataset.view === viewName);
        });
        
        // Update views
        this.views.forEach(view => {
            view.classList.toggle('active', view.id === `${viewName}-view`);
        });
        
        // Update current view
        this.currentView = viewName;
        
        // If switching to explorer view and data hasn't been loaded yet, load it
        if (viewName === 'explorer') {
            this.loadDatabaseInfo();
        }
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new ChatWithDB();
});
