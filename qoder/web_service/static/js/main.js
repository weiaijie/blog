document.addEventListener('DOMContentLoaded', function() {
    // DOM元素
    const tabs = document.querySelectorAll('.sidebar nav li');
    const tabContents = document.querySelectorAll('.tab-content');
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    const statsDiv = document.getElementById('stats');
    const messageInput = document.getElementById('message-input');
    const sendMessageBtn = document.getElementById('send-message');
    const clearMessageBtn = document.getElementById('clear-message');
    const togglePanelBtn = document.getElementById('toggle-panel');
    const messagePanel = document.querySelector('.message-panel');
    const closeViewerBtn = document.getElementById('close-viewer');
    const contentView = document.getElementById('content-viewer');

    // 当前激活的标签页
    let activeTab = 'chat-sessions';

    // 初始化
    initTabs();
    loadStats();
    setupEventListeners();

    function initTabs() {
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const tabId = this.getAttribute('data-tab');
                activateTab(tabId);
            });
        });
        
        // 默认激活第一个标签页
        activateTab(activeTab);
    }

    function activateTab(tabId) {
        // 更新标签页
        tabs.forEach(tab => {
            tab.classList.toggle('active', tab.getAttribute('data-tab') === tabId);
        });
        
        // 显示对应的标签页内容
        tabContents.forEach(content => {
            content.classList.toggle('active', content.id === `${tabId}-tab`);
        });
        
        activeTab = tabId;
        
        // 加载对应标签页的数据
        loadTabData(tabId);
    }

    function setupEventListeners() {
        // 搜索事件
        searchBtn.addEventListener('click', performSearch);
        searchInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                performSearch();
            }
        });

        // 消息发送事件
        sendMessageBtn.addEventListener('click', sendMessage);
        clearMessageBtn.addEventListener('click', () => {
            messageInput.value = '';
        });

        // 面板切换
        togglePanelBtn.addEventListener('click', toggleMessagePanel);

        // 关闭内容查看器
        closeViewerBtn.addEventListener('click', () => {
            contentView.style.display = 'none';
        });
    }

    function loadStats() {
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                statsDiv.innerHTML = `
                    <div class="stat-item">
                        <span class="stat-label">聊天会话</span>
                        <span class="stat-value">${data.chat_sessions_count}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">编辑会话</span>
                        <span class="stat-value">${data.editing_sessions_count}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">历史文件</span>
                        <span class="stat-value">${data.history_files_count}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">总大小</span>
                        <span class="stat-value">${formatFileSize(data.total_size)}</span>
                    </div>
                `;
            })
            .catch(error => {
                console.error('加载统计信息失败:', error);
            });
    }

    function loadTabData(tabId) {
        switch(tabId) {
            case 'chat-sessions':
                loadChatSessions();
                break;
            case 'editing-sessions':
                loadEditingSessions();
                break;
            case 'history-files':
                loadHistoryFiles();
                break;
            case 'search-results':
                // 搜索结果在搜索时加载
                break;
        }
    }

    function loadChatSessions() {
        const list = document.getElementById('chat-sessions-list');
        list.innerHTML = '<div class="loading">加载中...</div>';

        fetch('/api/chat-sessions')
            .then(response => response.json())
            .then(data => {
                document.getElementById('chat-sessions-count').textContent = data.count;
                
                if (data.sessions.length === 0) {
                    list.innerHTML = '<div class="no-results">暂无聊天会话</div>';
                    return;
                }

                list.innerHTML = '';
                data.sessions.forEach(session => {
                    const card = createItemCard({
                        title: `会话 ${session.file.split('\\').pop()}`,
                        content: JSON.stringify(session.data).substring(0, 100) + '...',
                        timestamp: formatDate(session.timestamp),
                        onClick: () => showSessionDetail(session)
                    });
                    list.appendChild(card);
                });
            })
            .catch(error => {
                console.error('加载聊天会话失败:', error);
                list.innerHTML = '<div class="no-results">加载失败</div>';
            });
    }

    function loadEditingSessions() {
        const list = document.getElementById('editing-sessions-list');
        list.innerHTML = '<div class="loading">加载中...</div>';

        fetch('/api/chat-editing-sessions')
            .then(response => response.json())
            .then(data => {
                document.getElementById('editing-sessions-count').textContent = data.count;
                
                if (data.sessions.length === 0) {
                    list.innerHTML = '<div class="no-results">暂无编辑会话</div>';
                    return;
                }

                list.innerHTML = '';
                data.sessions.forEach(session => {
                    const card = createItemCard({
                        title: `编辑会话 ${session.session_id}`,
                        content: JSON.stringify(session.data).substring(0, 100) + '...',
                        timestamp: formatDate(session.timestamp),
                        onClick: () => showSessionDetail(session)
                    });
                    list.appendChild(card);
                });
            })
            .catch(error => {
                console.error('加载编辑会话失败:', error);
                list.innerHTML = '<div class="no-results">加载失败</div>';
            });
    }

    function loadHistoryFiles(searchTerm = '') {
        const list = document.getElementById('history-files-list');
        list.innerHTML = '<div class="loading">加载中...</div>';

        const url = searchTerm ? `/api/history-files?search=${encodeURIComponent(searchTerm)}` : '/api/history-files';
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                document.getElementById('history-files-count').textContent = data.count;
                
                if (data.files.length === 0) {
                    list.innerHTML = '<div class="no-results">暂无历史文件</div>';
                    return;
                }

                list.innerHTML = '';
                data.files.forEach(file => {
                    const card = createItemCard({
                        title: file.name,
                        content: `路径: ${file.relative_path}<br>大小: ${formatFileSize(file.size)}`,
                        timestamp: formatDate(file.modified),
                        onClick: () => showFileContent(file.path)
                    });
                    list.appendChild(card);
                });
            })
            .catch(error => {
                console.error('加载历史文件失败:', error);
                list.innerHTML = '<div class="no-results">加载失败</div>';
            });
    }

    function performSearch() {
        const searchTerm = searchInput.value.trim();
        if (!searchTerm) {
            alert('请输入搜索词');
            return;
        }

        const list = document.getElementById('search-results-list');
        list.innerHTML = '<div class="loading">搜索中...</div>';

        fetch(`/api/search?q=${encodeURIComponent(searchTerm)}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('search-results-count').textContent = data.count;
                
                if (data.results.length === 0) {
                    list.innerHTML = '<div class="no-results">未找到匹配结果</div>';
                    return;
                }

                list.innerHTML = '';
                data.results.forEach(result => {
                    const card = createItemCard({
                        title: `搜索结果: ${result.file}`,
                        content: `匹配项: ${result.total_matches} 个<br>路径: ${result.path}`,
                        timestamp: '',
                        onClick: () => showFileContent(result.path)
                    });
                    list.appendChild(card);
                });
            })
            .catch(error => {
                console.error('搜索失败:', error);
                list.innerHTML = '<div class="no-results">搜索失败</div>';
            });

        // 切换到搜索结果标签页
        activateTab('search-results');
    }

    function createItemCard({title, content, timestamp, onClick}) {
        const card = document.createElement('div');
        card.className = 'item-card';
        
        card.innerHTML = `
            <h4>${title}</h4>
            <p>${content}</p>
            ${timestamp ? `<div class="item-meta"><span>${timestamp}</span></div>` : ''}
        `;
        
        card.addEventListener('click', onClick);
        return card;
    }

    function showSessionDetail(session) {
        // 显示会话详情，这里可以创建一个模态框或详情视图
        alert(`会话详情:\n${JSON.stringify(session, null, 2)}`);
    }

    function showFileContent(filePath) {
        fetch(`/api/file-content?path=${encodeURIComponent(filePath)}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('加载文件失败: ' + data.error);
                    return;
                }

                document.getElementById('viewer-title').textContent = data.file;
                document.getElementById('viewer-content').textContent = data.content;
                contentView.style.display = 'flex';
            })
            .catch(error => {
                console.error('加载文件内容失败:', error);
                alert('加载文件失败');
            });
    }

    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) {
            alert('请输入消息内容');
            return;
        }

        fetch('/api/send-message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert('发送失败: ' + data.error);
                return;
            }
            
            alert('消息已发送!');
            messageInput.value = '';
        })
        .catch(error => {
            console.error('发送消息失败:', error);
            alert('发送失败: ' + error.message);
        });
    }

    function toggleMessagePanel() {
        const isHidden = messagePanel.style.display === 'none';
        if (isHidden) {
            messagePanel.style.display = 'block';
            togglePanelBtn.classList.remove('rotated');
        } else {
            messagePanel.style.display = 'none';
            togglePanelBtn.classList.add('rotated');
        }
    }

    function formatDate(timestamp) {
        const date = new Date(timestamp * 1000);
        return date.toLocaleString('zh-CN');
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // 暴露一些函数到全局作用域，便于调试
    window.app = {
        loadStats,
        loadChatSessions,
        loadEditingSessions,
        loadHistoryFiles,
        performSearch
    };
});