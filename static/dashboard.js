/**
 * Dashboard JavaScript functionality for Call Center System
 * Handles real-time updates, charts, and interactive features
 */

class CallCenterDashboard {
    constructor() {
        this.refreshInterval = 30000; // 30 seconds
        this.refreshTimers = new Map();
        this.charts = new Map();
        this.lastUpdate = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
        this.startAutoRefresh();
        this.initializeCharts();
    }

    setupEventListeners() {
        // Refresh buttons
        document.getElementById('refreshCallsBtn')?.addEventListener('click', () => {
            this.loadActiveCalls();
        });

        // Period selectors
        document.getElementById('chartPeriod')?.addEventListener('change', (e) => {
            this.updateCallVolumeChart(e.target.value);
        });

        document.getElementById('performancePeriod')?.addEventListener('change', (e) => {
            this.loadPerformanceMetrics(e.target.value);
        });

        // Table row click handlers for call details
        document.addEventListener('click', (e) => {
            if (e.target.closest('.call-row')) {
                const callId = e.target.closest('.call-row').dataset.callId;
                if (callId) {
                    this.showCallDetails(callId);
                }
            }
        });
    }

    async loadInitialData() {
        try {
            await Promise.all([
                this.loadDashboardSummary(),
                this.loadActiveCalls(),
                this.loadAgentStatus(),
                this.loadDepartmentQueues(),
                this.loadPerformanceMetrics('today')
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    async loadDashboardSummary() {
        try {
            const response = await fetch('/api/dashboard/summary', {
                credentials: 'include'
            });
            const data = await response.json();

            if (data.success) {
                // Update summary cards
                this.updateSummaryCard('totalActiveCalls', data.active_calls?.total_active_calls || 0);
                this.updateSummaryCard('availableAgents', this.getAvailableAgentsCount(data.agent_status));
                this.updateSummaryCard('escalatedCalls', data.active_calls?.escalated_calls || 0);
                
                // Calculate average wait time from queue status
                const avgWaitTime = this.calculateAverageWaitTime(data.queue_status);
                this.updateSummaryCard('avgWaitTime', avgWaitTime);
            }
        } catch (error) {
            console.error('Error loading dashboard summary:', error);
        }
    }

    async loadActiveCalls() {
        try {
            const response = await fetch('/api/dashboard/calls/active', {
                credentials: 'include'
            });
            const data = await response.json();

            if (data.success) {
                this.renderActiveCallsTable(data.active_calls || []);
                
                // Update summary metrics
                const summary = data.summary || {};
                this.updateSummaryCard('totalActiveCalls', summary.total_active_calls || 0);
                this.updateSummaryCard('escalatedCalls', summary.escalated_calls || 0);
            } else {
                this.renderActiveCallsTable([]);
            }
        } catch (error) {
            console.error('Error loading active calls:', error);
            this.renderActiveCallsTable([]);
        }
    }

    async loadAgentStatus() {
        try {
            const response = await fetch('/api/dashboard/agents', {
                credentials: 'include'
            });
            const data = await response.json();

            if (data.success) {
                this.renderAgentStatus(data.agents || []);
                this.updateSummaryCard('availableAgents', data.available_agents || 0);
            } else {
                this.renderAgentStatus([]);
            }
        } catch (error) {
            console.error('Error loading agent status:', error);
            this.renderAgentStatus([]);
        }
    }

    async loadDepartmentQueues() {
        try {
            const response = await fetch('/api/routing/queue-status', {
                credentials: 'include'
            });
            const data = await response.json();

            if (data.success && data.queue_status) {
                this.renderDepartmentQueues(data.queue_status);
            } else {
                this.renderDepartmentQueues({});
            }
        } catch (error) {
            console.error('Error loading department queues:', error);
            this.renderDepartmentQueues({});
        }
    }

    async loadPerformanceMetrics(period = 'today') {
        try {
            const response = await fetch(`/api/dashboard/performance?time_period=${period}`, {
                credentials: 'include'
            });
            const data = await response.json();

            if (data.success) {
                this.renderPerformanceMetrics(data);
            } else {
                this.renderPerformanceMetrics({ performance_data: {}, summary: {} });
            }
        } catch (error) {
            console.error('Error loading performance metrics:', error);
            this.renderPerformanceMetrics({ performance_data: {}, summary: {} });
        }
    }

    renderActiveCallsTable(calls) {
        const tbody = document.getElementById('activeCallsBody');
        if (!tbody) return;

        if (calls.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted">No active calls</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = calls.map(call => {
            const duration = this.formatDuration(call.duration_seconds || 0);
            const priorityClass = this.getPriorityClass(call.priority);
            const statusBadge = call.escalated ? 
                '<span class="badge bg-warning">Escalated</span>' : 
                '<span class="badge bg-success">Active</span>';

            return `
                <tr class="call-row" data-call-id="${call.call_id}" style="cursor: pointer;">
                    <td><code>${call.call_id}</code></td>
                    <td>
                        <div>${call.customer_name || 'Unknown'}</div>
                        <small class="text-muted">${call.customer_phone || ''}</small>
                    </td>
                    <td><span class="badge bg-info">${call.department || 'General'}</span></td>
                    <td><span class="badge bg-secondary">${call.current_agent || 'Unassigned'}</span></td>
                    <td>${duration}</td>
                    <td><span class="priority-${priorityClass}">${this.getPriorityText(call.priority)}</span></td>
                    <td>${statusBadge}</td>
                </tr>
            `;
        }).join('');
    }

    renderAgentStatus(agents) {
        const container = document.getElementById('agentStatusList');
        if (!container) return;

        if (agents.length === 0) {
            container.innerHTML = '<div class="text-center text-muted">No agents available</div>';
            return;
        }

        container.innerHTML = agents.map(agent => {
            const statusClass = this.getAgentStatusClass(agent.status);
            const statusBadge = `<span class="badge ${statusClass}">${agent.status}</span>`;
            
            return `
                <div class="agent-status-item p-3 mb-2 border rounded">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6 class="mb-1">${agent.name}</h6>
                            <small class="text-muted">${agent.role}</small>
                        </div>
                        <div class="text-end">
                            ${statusBadge}
                            <small class="d-block text-muted mt-1">
                                ${agent.current_calls} active / ${agent.total_calls} total
                            </small>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    renderDepartmentQueues(queueStatus) {
        const container = document.getElementById('departmentQueues');
        if (!container) return;

        if (Object.keys(queueStatus).length === 0) {
            container.innerHTML = '<div class="text-center text-muted">No queue data available</div>';
            return;
        }

        container.innerHTML = Object.entries(queueStatus).map(([deptCode, deptData]) => {
            const waitTimeClass = this.getWaitTimeClass(deptData.estimated_wait_time);
            
            return `
                <div class="queue-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6 class="mb-0">${deptData.name}</h6>
                        <span class="badge ${waitTimeClass}">${deptData.estimated_wait_time}</span>
                    </div>
                    <div class="queue-stats mt-2">
                        <div class="queue-stat">
                            <div class="queue-stat-value">${deptData.active_calls}</div>
                            <div class="queue-stat-label">Active</div>
                        </div>
                        <div class="queue-stat">
                            <div class="queue-stat-value">${deptData.available_agents}</div>
                            <div class="queue-stat-label">Agents</div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    renderPerformanceMetrics(data) {
        const container = document.getElementById('performanceMetrics');
        if (!container) return;

        const performanceData = data.performance_data || {};
        const summary = data.summary || {};

        if (Object.keys(performanceData).length === 0) {
            container.innerHTML = '<div class="text-center text-muted">No performance data available</div>';
            return;
        }

        // Render summary first
        let html = '';
        if (summary.total_agents) {
            html += `
                <div class="row mb-4">
                    <div class="col-md-3">
                        <div class="text-center">
                            <h4>${summary.total_agents}</h4>
                            <small class="text-muted">Total Agents</small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="text-center">
                            <h4>${summary.total_calls_handled}</h4>
                            <small class="text-muted">Total Calls</small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="text-center">
                            <h4>${summary.average_quality_score}</h4>
                            <small class="text-muted">Avg Quality</small>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="text-center">
                            <h4>${summary.average_satisfaction}</h4>
                            <small class="text-muted">Avg Satisfaction</small>
                        </div>
                    </div>
                </div>
            `;
        }

        // Render individual agent performance
        html += '<div class="row">';
        Object.entries(performanceData).forEach(([agentId, metrics]) => {
            const qualityClass = metrics.average_quality_score >= 4 ? 'success' : 
                               metrics.average_quality_score >= 3 ? 'warning' : 'danger';
            
            html += `
                <div class="col-md-6 mb-3">
                    <div class="card">
                        <div class="card-body">
                            <h6>${metrics.name}</h6>
                            <small class="text-muted">${metrics.role}</small>
                            <div class="mt-2">
                                <div class="d-flex justify-content-between">
                                    <span>Calls Handled:</span>
                                    <strong>${metrics.total_calls}</strong>
                                </div>
                                <div class="d-flex justify-content-between">
                                    <span>Quality Score:</span>
                                    <span class="badge bg-${qualityClass}">${metrics.average_quality_score.toFixed(1)}</span>
                                </div>
                                <div class="d-flex justify-content-between">
                                    <span>Escalation Rate:</span>
                                    <strong>${metrics.escalation_rate.toFixed(1)}%</strong>
                                </div>
                                <div class="d-flex justify-content-between">
                                    <span>Satisfaction:</span>
                                    <strong>${metrics.customer_satisfaction.toFixed(1)}/5</strong>
                                </div>
                            </div>
                            ${metrics.recommendations.length > 0 ? `
                                <div class="mt-2">
                                    <small class="text-muted">Recommendations:</small>
                                    <ul class="small mt-1">
                                        ${metrics.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                                    </ul>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
        });
        html += '</div>';

        container.innerHTML = html;
    }

    async showCallDetails(callId) {
        try {
            const [statusResponse, historyResponse] = await Promise.all([
                fetch(`/api/calls/${callId}/status`, {
                    credentials: 'include'
                }),
                fetch(`/api/calls/${callId}/history`, {
                    credentials: 'include'
                })
            ]);

            const statusData = await statusResponse.json();
            const historyData = await historyResponse.json();

            if (statusData.success && historyData.success) {
                this.renderCallDetailsModal(callId, statusData, historyData);
            } else {
                this.showError('Failed to load call details');
            }
        } catch (error) {
            console.error('Error loading call details:', error);
            this.showError('Error loading call details');
        }
    }

    renderCallDetailsModal(callId, statusData, historyData) {
        const modalBody = document.getElementById('callDetailsBody');
        if (!modalBody) return;

        const call = statusData;
        const history = historyData.history || [];

        modalBody.innerHTML = `
            <div class="row mb-3">
                <div class="col-md-6">
                    <strong>Call ID:</strong> <code>${callId}</code><br>
                    <strong>Status:</strong> <span class="badge bg-info">${call.status}</span><br>
                    <strong>Department:</strong> ${call.department || 'N/A'}<br>
                    <strong>Priority:</strong> <span class="priority-${this.getPriorityClass(call.priority)}">${this.getPriorityText(call.priority)}</span>
                </div>
                <div class="col-md-6">
                    <strong>Current Agent:</strong> ${call.current_agent || 'Unassigned'}<br>
                    <strong>Escalated:</strong> ${call.escalated ? 'Yes' : 'No'}<br>
                    <strong>Duration:</strong> ${this.formatDuration(call.duration_seconds || 0)}<br>
                    <strong>Messages:</strong> ${call.message_count || history.length}
                </div>
            </div>
            
            <h6>Conversation History</h6>
            <div class="conversation-history" style="max-height: 300px; overflow-y: auto; border: 1px solid #dee2e6; border-radius: 0.375rem; padding: 15px;">
                ${history.length > 0 ? history.map(log => `
                    <div class="message ${log.message_type}-message mb-2">
                        <div class="message-header">
                            <strong>${this.formatMessageType(log.message_type, log.agent_id)}</strong>
                            <small class="text-muted">${this.formatTimestamp(log.timestamp)}</small>
                        </div>
                        <div class="message-content">${log.content}</div>
                    </div>
                `).join('') : '<div class="text-center text-muted">No conversation history available</div>'}
            </div>
        `;

        // Show the modal
        const modal = new bootstrap.Modal(document.getElementById('callDetailsModal'));
        modal.show();
    }

    initializeCharts() {
        this.initCallVolumeChart();
    }

    initCallVolumeChart() {
        const ctx = document.getElementById('callVolumeChart');
        if (!ctx) return;

        // Initialize with empty data
        this.charts.set('callVolume', new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Call Volume',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        }));

        // Load initial chart data
        this.updateCallVolumeChart('today');
    }

    async updateCallVolumeChart(period) {
        const chart = this.charts.get('callVolume');
        if (!chart) return;

        try {
            // For demo purposes, generate sample data based on period
            // In a real implementation, this would fetch actual data from the API
            const { labels, data } = this.generateChartData(period);
            
            chart.data.labels = labels;
            chart.data.datasets[0].data = data;
            chart.update();
        } catch (error) {
            console.error('Error updating call volume chart:', error);
        }
    }

    generateChartData(period) {
        // Generate sample data for demonstration
        // In a real implementation, this would be fetched from the API
        const now = new Date();
        let labels = [];
        let data = [];

        if (period === 'today') {
            // Hourly data for today
            for (let i = 0; i < 24; i++) {
                const hour = i.toString().padStart(2, '0') + ':00';
                labels.push(hour);
                data.push(Math.floor(Math.random() * 10)); // Random data for demo
            }
        } else if (period === 'week') {
            // Daily data for the week
            for (let i = 6; i >= 0; i--) {
                const date = new Date(now);
                date.setDate(date.getDate() - i);
                labels.push(date.toLocaleDateString('en-US', { weekday: 'short' }));
                data.push(Math.floor(Math.random() * 50));
            }
        } else if (period === 'month') {
            // Weekly data for the month
            for (let i = 3; i >= 0; i--) {
                const date = new Date(now);
                date.setDate(date.getDate() - (i * 7));
                labels.push(`Week ${4-i}`);
                data.push(Math.floor(Math.random() * 200));
            }
        }

        return { labels, data };
    }

    startAutoRefresh() {
        // Set up auto-refresh timers
        this.refreshTimers.set('summary', setInterval(() => {
            this.loadDashboardSummary();
        }, this.refreshInterval));

        this.refreshTimers.set('calls', setInterval(() => {
            this.loadActiveCalls();
        }, this.refreshInterval));

        this.refreshTimers.set('agents', setInterval(() => {
            this.loadAgentStatus();
        }, this.refreshInterval));

        this.refreshTimers.set('queues', setInterval(() => {
            this.loadDepartmentQueues();
        }, this.refreshInterval * 2)); // Refresh queues less frequently
    }

    stopAutoRefresh() {
        this.refreshTimers.forEach((timer) => {
            clearInterval(timer);
        });
        this.refreshTimers.clear();
    }

    // Utility methods
    updateSummaryCard(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    getAvailableAgentsCount(agentStatus) {
        if (!agentStatus || typeof agentStatus !== 'object') return 0;
        return Object.values(agentStatus).filter(agent => agent.status === 'available').length;
    }

    calculateAverageWaitTime(queueStatus) {
        if (!queueStatus || typeof queueStatus !== 'object') return '--';
        
        const waitTimes = Object.values(queueStatus)
            .map(dept => dept.estimated_wait_time)
            .filter(time => time && time !== 'Unknown')
            .map(time => parseInt(time.replace(/\D/g, '')) || 0);
        
        if (waitTimes.length === 0) return '--';
        
        const avg = waitTimes.reduce((sum, time) => sum + time, 0) / waitTimes.length;
        return `${Math.round(avg)} min`;
    }

    formatDuration(seconds) {
        if (!seconds) return '00:00';
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    getPriorityClass(priority) {
        switch (priority) {
            case 1: return 'low';
            case 2: return 'normal';
            case 3: return 'high';
            case 4: return 'urgent';
            default: return 'normal';
        }
    }

    getPriorityText(priority) {
        switch (priority) {
            case 1: return 'Low';
            case 2: return 'Normal';
            case 3: return 'High';
            case 4: return 'Urgent';
            default: return 'Normal';
        }
    }

    getAgentStatusClass(status) {
        switch (status) {
            case 'available': return 'bg-success';
            case 'busy': return 'bg-warning';
            case 'offline': return 'bg-secondary';
            default: return 'bg-secondary';
        }
    }

    getWaitTimeClass(waitTime) {
        if (!waitTime || waitTime === 'Unknown') return 'bg-secondary';
        
        const minutes = parseInt(waitTime.replace(/\D/g, '')) || 0;
        if (minutes <= 2) return 'bg-success';
        if (minutes <= 5) return 'bg-warning';
        return 'bg-danger';
    }

    formatMessageType(messageType, agentId) {
        switch (messageType) {
            case 'customer': return 'Customer';
            case 'agent': return agentId ? agentId.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Agent';
            case 'supervisor': return 'Supervisor';
            case 'system': return 'System';
            default: return messageType;
        }
    }

    formatTimestamp(timestamp) {
        if (!timestamp) return '';
        try {
            return new Date(timestamp).toLocaleString();
        } catch (error) {
            return timestamp;
        }
    }

    showError(message) {
        // Create and show error alert
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed';
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.callCenterDashboard = new CallCenterDashboard();
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (window.callCenterDashboard) {
        window.callCenterDashboard.stopAutoRefresh();
    }
});
