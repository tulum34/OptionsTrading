/**
 * Real-time Trading Dashboard - Frontend JavaScript
 * Handles WebSocket connection and updates dashboard data
 */

// Initialize Socket.IO connection
const socket = io();

// Connection status
let isConnected = false;

// Status thresholds for Greeks
const DELTA_THRESHOLDS = {
    green: { min: -0.10, max: 0.10 },
    yellow: { min: -0.15, max: 0.15 }
};

// Socket.IO event handlers
socket.on('connect', function() {
    console.log('Connected to server');
    isConnected = true;
    updateConnectionStatus(true);
});

socket.on('disconnect', function() {
    console.log('Disconnected from server');
    isConnected = false;
    updateConnectionStatus(false);
});

socket.on('update', function(data) {
    console.log('Received update:', data);
    updateDashboard(data);
});

// Update connection status indicator
function updateConnectionStatus(connected) {
    const statusDot = document.querySelector('.status-dot');
    const statusText = document.getElementById('connection-status');
    
    if (connected) {
        statusDot.classList.add('connected');
        statusText.textContent = 'Connected';
        statusText.style.color = '#00ff88';
    } else {
        statusDot.classList.remove('connected');
        statusText.textContent = 'Disconnected';
        statusText.style.color = '#ff4444';
    }
}

// Main function to update all dashboard elements
function updateDashboard(data) {
    // Update Greeks
    updateGreeks('btc', data.btc);
    updateGreeks('eth', data.eth);
    
    // Update Risk Metrics
    updateRiskMetrics(data.risk_metrics);
    
    // Update Positions
    updatePositions('binance', data.positions.binance);
    updatePositions('bybit', data.positions.bybit);
    
    // Update Recent Activity
    updateActivity(data.recent_activity);
    
    // Update last update time
    document.getElementById('last-update').textContent = 
        `Last Update: ${data.last_update}`;
}

// Update Greeks cards
function updateGreeks(asset, greekData) {
    const greeks = ['delta', 'gamma', 'theta', 'vega'];
    
    greeks.forEach(greek => {
        const valueElement = document.getElementById(`${asset}-${greek}-value`);
        const statusElement = document.getElementById(`${asset}-${greek}-status`);
        
        if (valueElement && statusElement) {
            let value = greekData[greek];
            
            // Format value based on Greek type
            if (greek === 'theta') {
                value = value.toFixed(2);
            } else if (greek === 'delta' || greek === 'gamma') {
                value = value.toFixed(2);
            } else {
                value = value.toFixed(2);
            }
            
            valueElement.textContent = value;
            
            // Add color class for delta and theta (can be negative)
            if (greek === 'delta' || greek === 'theta') {
                valueElement.classList.remove('positive', 'negative');
                if (parseFloat(value) > 0) {
                    valueElement.classList.add('positive');
                } else if (parseFloat(value) < 0) {
                    valueElement.classList.add('negative');
                }
            }
            
            // Update status indicator based on delta thresholds
            if (greek === 'delta') {
                const deltaValue = parseFloat(value);
                if (deltaValue >= DELTA_THRESHOLDS.green.min && deltaValue <= DELTA_THRESHOLDS.green.max) {
                    statusElement.textContent = '🟢';
                } else if (deltaValue >= DELTA_THRESHOLDS.yellow.min && deltaValue <= DELTA_THRESHOLDS.yellow.max) {
                    statusElement.textContent = '🟡';
                } else {
                    statusElement.textContent = '🔴';
                }
            } else {
                // For other Greeks, default to yellow
                statusElement.textContent = '🟡';
            }
        }
    });
}

// Update Risk Metrics
function updateRiskMetrics(metrics) {
    // Delta Exposure
    const deltaExpElement = document.getElementById('delta-exposure');
    const deltaExpStatus = document.getElementById('delta-exposure-status');
    if (deltaExpElement) {
        const value = metrics.delta_exposure.toFixed(2);
        deltaExpElement.textContent = value;
        deltaExpElement.classList.remove('positive', 'negative');
        if (parseFloat(value) > 0) {
            deltaExpElement.classList.add('positive');
        } else if (parseFloat(value) < 0) {
            deltaExpElement.classList.add('negative');
        }
        
        // Status for delta exposure
        const deltaValue = parseFloat(value);
        if (deltaValue >= DELTA_THRESHOLDS.green.min && deltaValue <= DELTA_THRESHOLDS.green.max) {
            deltaExpStatus.textContent = '🟢';
        } else if (deltaValue >= DELTA_THRESHOLDS.yellow.min && deltaValue <= DELTA_THRESHOLDS.yellow.max) {
            deltaExpStatus.textContent = '🟡';
        } else {
            deltaExpStatus.textContent = '🔴';
        }
    }
    
    // Hedge Position
    document.getElementById('hedge-btc').textContent = metrics.hedge_position.btc.toFixed(2);
    document.getElementById('hedge-eth').textContent = metrics.hedge_position.eth.toFixed(2);
    
    // Net Risk
    document.getElementById('net-risk').textContent = formatCurrency(metrics.net_risk);
    document.getElementById('margin-used').textContent = `${metrics.margin_used}%`;
    
    // Daily P&L
    const dailyPnlElement = document.getElementById('daily-pnl');
    const dailyPnlPctElement = document.getElementById('daily-pnl-pct');
    if (dailyPnlElement) {
        dailyPnlElement.textContent = formatCurrency(metrics.daily_pnl);
        dailyPnlElement.classList.remove('positive', 'negative');
        if (metrics.daily_pnl >= 0) {
            dailyPnlElement.classList.add('positive');
        } else {
            dailyPnlElement.classList.add('negative');
        }
    }
    if (dailyPnlPctElement) {
        const pct = metrics.daily_pnl_pct.toFixed(2);
        dailyPnlPctElement.textContent = `${pct >= 0 ? '+' : ''}${pct}%`;
        dailyPnlPctElement.classList.remove('positive', 'negative');
        if (metrics.daily_pnl_pct >= 0) {
            dailyPnlPctElement.classList.add('positive');
        } else {
            dailyPnlPctElement.classList.add('negative');
        }
    }
    
    // Portfolio Value
    document.getElementById('portfolio-value').textContent = formatCurrency(metrics.portfolio_value);
    
    // Hedge Ratio
    const hedgeRatioElement = document.getElementById('hedge-ratio');
    const hedgeRatioProgress = document.getElementById('hedge-ratio-progress');
    if (hedgeRatioElement) {
        hedgeRatioElement.textContent = `${metrics.hedge_ratio}%`;
    }
    if (hedgeRatioProgress) {
        hedgeRatioProgress.style.width = `${metrics.hedge_ratio}%`;
    }
}

// Update Positions Table
function updatePositions(exchange, positions) {
    const tbody = document.getElementById(`${exchange}-positions`);
    
    if (!tbody) return;
    
    // Clear existing rows
    tbody.innerHTML = '';
    
    if (positions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">No positions</td></tr>';
        return;
    }
    
    // Create rows for each position
    positions.forEach(position => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${position.symbol}</td>
            <td>${position.type}</td>
            <td>${position.qty}</td>
            <td>${position.delta.toFixed(2)}</td>
            <td>${position.gamma.toFixed(2)}</td>
            <td class="${position.pnl >= 0 ? 'pnl-positive' : 'pnl-negative'}">${formatCurrency(position.pnl)}</td>
        `;
        
        tbody.appendChild(row);
    });
}

// Update Recent Activity Log
function updateActivity(activities) {
    const activityLog = document.getElementById('activity-log');
    
    if (!activityLog) return;
    
    // Clear existing activities
    activityLog.innerHTML = '';
    
    // Show last 5 activities
    const recentActivities = activities.slice(-5).reverse();
    
    if (recentActivities.length === 0) {
        activityLog.innerHTML = '<div class="activity-item"><span class="activity-time">--:--:--</span><span class="activity-desc">No recent activity</span><span class="activity-status">ℹ️</span></div>';
        return;
    }
    
    recentActivities.forEach(activity => {
        const item = document.createElement('div');
        item.className = 'activity-item';
        
        const statusIcon = getActivityIcon(activity.status);
        
        item.innerHTML = `
            <span class="activity-time">${activity.time}</span>
            <span class="activity-desc">${activity.description}</span>
            <span class="activity-status">${statusIcon}</span>
        `;
        
        activityLog.appendChild(item);
    });
}

// Get activity icon based on status
function getActivityIcon(status) {
    switch(status) {
        case 'filled':
            return '✓';
        case 'alert':
            return '⚠️';
        case 'info':
            return 'ℹ️';
        default:
            return 'ℹ️';
    }
}

// Format currency
function formatCurrency(value) {
    const sign = value >= 0 ? '$' : '-$';
    const absValue = Math.abs(value);
    return `${sign}${absValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// Button event handlers
document.addEventListener('DOMContentLoaded', function() {
    // Hedge Now button
    const hedgeBtn = document.getElementById('hedge-btn');
    if (hedgeBtn) {
        hedgeBtn.addEventListener('click', function() {
            alert('Hedge functionality will be implemented later');
            // TODO: Implement hedge logic
        });
    }
    
    // Refresh All button
    const refreshBtn = document.getElementById('refresh-btn');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            if (isConnected) {
                socket.emit('request_update');
                // Force reconnection to get fresh data
                socket.connect();
            } else {
                alert('Not connected to server. Please wait for connection.');
            }
        });
    }
});

// Request initial data on page load
socket.on('connect', function() {
    socket.emit('request_update');
});

// Order Form Handling
document.addEventListener('DOMContentLoaded', function() {
    const orderForm = document.getElementById('order-form');
    const orderTypeSelect = document.getElementById('order-type');
    const priceGroup = document.getElementById('price-group');
    const orderPriceInput = document.getElementById('order-price');
    const resetBtn = document.getElementById('reset-order-form');
    const orderResult = document.getElementById('order-result');
    
    // Show/hide price field based on order type
    if (orderTypeSelect) {
        orderTypeSelect.addEventListener('change', function() {
            if (this.value === 'limit') {
                priceGroup.style.display = 'block';
                orderPriceInput.setAttribute('required', 'required');
            } else {
                priceGroup.style.display = 'none';
                orderPriceInput.removeAttribute('required');
                orderPriceInput.value = '';
            }
        });
    }
    
    // Handle form submission
    if (orderForm) {
        orderForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Disable submit button
            const submitBtn = orderForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.textContent = 'Placing Order...';
            
            // Clear previous results
            orderResult.className = 'order-result';
            orderResult.style.display = 'none';
            orderResult.textContent = '';
            
            // Get form data
            const formData = {
                exchange: document.getElementById('order-exchange').value,
                symbol: document.getElementById('order-symbol').value,
                side: document.getElementById('order-side').value,
                type: document.getElementById('order-type').value,
                amount: parseFloat(document.getElementById('order-amount').value),
                price: document.getElementById('order-price').value ? parseFloat(document.getElementById('order-price').value) : null
            };
            
            try {
                const response = await fetch('/api/place_order', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(formData)
                });
                
                const result = await response.json();
                
                // Show result
                orderResult.style.display = 'block';
                
                if (result.success) {
                    orderResult.className = 'order-result success';
                    orderResult.innerHTML = `
                        <strong>✅ Order Placed Successfully!</strong><br>
                        Order ID: ${result.order_id || 'N/A'}<br>
                        Symbol: ${result.symbol}<br>
                        Side: ${result.side.toUpperCase()}<br>
                        Type: ${result.type.toUpperCase()}<br>
                        Amount: ${result.amount}<br>
                        ${result.price ? `Price: ${result.price}<br>` : ''}
                        Status: ${result.status || 'Pending'}<br>
                        Time: ${result.timestamp}
                    `;
                    
                    // Reset form after successful order
                    setTimeout(() => {
                        orderForm.reset();
                        priceGroup.style.display = 'none';
                        orderResult.style.display = 'none';
                    }, 5000);
                    
                    // Request dashboard update
                    socket.emit('request_update');
                } else {
                    orderResult.className = 'order-result error';
                    orderResult.innerHTML = `
                        <strong>❌ Order Failed</strong><br>
                        Error: ${result.error || 'Unknown error'}
                    `;
                }
            } catch (error) {
                orderResult.className = 'order-result error';
                orderResult.style.display = 'block';
                orderResult.innerHTML = `
                    <strong>❌ Error</strong><br>
                    ${error.message}
                `;
            } finally {
                // Re-enable submit button
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }
        });
    }
    
    // Handle reset button
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            orderForm.reset();
            priceGroup.style.display = 'none';
            orderPriceInput.removeAttribute('required');
            orderResult.className = 'order-result';
            orderResult.style.display = 'none';
            orderResult.textContent = '';
        });
    }
    
    // Listen for order placed events
    socket.on('order_placed', function(data) {
        console.log('Order placed:', data);
        // Dashboard will be updated automatically via request_update
    });
});

